"""
Post-processing service for transcript analysis.

Orchestrates structured data extraction from call transcripts using:
1. OpenAI GPT-4 extraction (primary)
2. Limited regex fallback for missing categorical fields only
3. Marks summaries as partial when incomplete

Flow:
1. Try OpenAI structured extraction
2. Validate required fields
3. If missing → run limited regex fallback (only high-confidence categorical fields)
4. Mark summary as partial if still incomplete
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.services.openai_service import OpenAIService, OpenAIServiceError, get_openai_service
from app.services.extraction_schemas import DispatchCheckInExtraction, EmergencyExtraction
from app.services.fallback_extraction import fill_missing_categorical_fields
from app.models.schemas import ScenarioType

logger = logging.getLogger(__name__)


def _get_required_fields(scenario_type: ScenarioType) -> list[str]:
    """
    Get list of required fields for a scenario type.
    
    Required fields are those that must be present for a complete extraction.
    """
    if scenario_type == ScenarioType.EMERGENCY:
        return ["call_outcome", "emergency_type"]
    else:  # DISPATCH_CHECKIN
        return ["call_outcome", "driver_status"]


def _is_extraction_complete(extracted_data: Dict[str, Any], scenario_type: ScenarioType) -> bool:
    """
    Check if extraction is complete (all required fields present).
    
    Args:
        extracted_data: Extracted data dictionary
        scenario_type: Scenario type
        
    Returns:
        True if all required fields are present, False otherwise
    """
    required_fields = _get_required_fields(scenario_type)
    return all(
        field in extracted_data and extracted_data[field] is not None
        for field in required_fields
    )


class PostProcessingService:
    """
    Service for post-processing call transcripts.
    
    Handles structured extraction and database storage with limited fallback.
    """
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        """
        Initialize post-processing service.
        
        Args:
            openai_service: Optional OpenAI service instance (for dependency injection)
        """
        self.openai_service = openai_service or get_openai_service()
    
    async def process_transcript(
        self,
        call_id: UUID,
        transcript: str,
        scenario_type: ScenarioType,
        db: Client,
    ) -> Dict[str, Any]:
        """
        Process a call transcript and extract structured data.
        
        Process:
        1. Try OpenAI structured extraction
        2. Validate required fields
        3. If missing → run limited regex fallback (only categorical fields)
        4. Mark summary as partial if still incomplete
        
        Args:
            call_id: Internal call ID
            transcript: Full call transcript text
            scenario_type: 'dispatch_checkin' or 'emergency'
            db: Supabase client
            
        Returns:
            Dictionary with extracted structured data
        """
        logger.info(f"Processing transcript for call {call_id} (scenario: {scenario_type.value})")
        
        extracted_data: Dict[str, Any] = {}
        extraction_method = "unknown"
        is_partial = False
        
        # Step 1: Try OpenAI extraction first
        try:
            if scenario_type == ScenarioType.EMERGENCY:
                schema = EmergencyExtraction
                extracted_data = self.openai_service.extract_structured_data(
                    transcript=transcript,
                    schema=schema,
                    scenario_type=scenario_type.value,
                )
            else:  # DISPATCH_CHECKIN
                schema = DispatchCheckInExtraction
                extracted_data = self.openai_service.extract_structured_data(
                    transcript=transcript,
                    schema=schema,
                    scenario_type=scenario_type.value,
                )
            
            extraction_method = "openai"
            logger.info(f"Successfully extracted data using OpenAI for call {call_id}")
            
        except OpenAIServiceError as e:
            logger.warning(f"OpenAI extraction failed for call {call_id}: {e}. Using limited regex fallback.")
            extracted_data = {}
            extraction_method = "failed_openai"
        
        # Step 2: Validate required fields
        is_complete = _is_extraction_complete(extracted_data, scenario_type)
        
        # Step 3: If missing required fields, run limited regex fallback
        if not is_complete:
            logger.info(f"OpenAI extraction incomplete for call {call_id}, applying limited regex fallback for categorical fields")
            extracted_data = fill_missing_categorical_fields(
                extracted_data=extracted_data,
                transcript=transcript,
                scenario_type=scenario_type.value,
            )
            
            if extraction_method == "failed_openai":
                extraction_method = "regex_fallback_only"
            else:
                extraction_method = "openai_with_regex_fallback"
        
        # Step 4: Check if still incomplete (mark as partial)
        is_complete = _is_extraction_complete(extracted_data, scenario_type)
        if not is_complete:
            is_partial = True
            logger.info(f"Extraction still incomplete for call {call_id}, marking as partial")
        
        # Prepare data for database storage
        # Filter to only valid database columns (prevent errors from invalid field names)
        valid_db_fields = {
            "call_outcome", "driver_status", "current_location", "eta", "delay_reason",
            "unloading_status", "pod_reminder_acknowledged", "emergency_type",
            "safety_status", "injury_status", "emergency_location", "load_secure",
            "escalation_status"
        }
        
        # Filter extracted_data to only include valid database fields
        filtered_extracted = {
            k: v for k, v in extracted_data.items()
            if k in valid_db_fields
        }
        
        raw_extraction_with_metadata = {
            **extracted_data,  # Keep full extracted data (including invalid fields) in raw_extraction
            "_extraction_method": extraction_method,
            "_is_partial": is_partial,
        }
        
        summary_data = {
            "call_id": str(call_id),
            "raw_extraction": raw_extraction_with_metadata,
            "partial": is_partial,  # Store partial flag at top level for easy querying
        }
        
        # Add only valid extracted fields to summary_data (these map to database columns)
        summary_data.update(filtered_extracted)
        
        # Store in database
        try:
            # Check if summary already exists (update if exists, insert if not)
            existing = db.table("structured_summaries").select("id").eq("call_id", str(call_id)).execute()
            
            if existing.data:
                # Update existing summary
                response = db.table("structured_summaries").update(summary_data).eq(
                    "call_id", str(call_id)
                ).execute()
                logger.info(f"Updated structured summary for call {call_id} (partial: {is_partial})")
            else:
                # Insert new summary
                response = db.table("structured_summaries").insert(summary_data).execute()
                logger.info(f"Created structured summary for call {call_id} (partial: {is_partial})")
            
            if not response.data:
                logger.error(f"Failed to save structured summary for call {call_id}")
                return extracted_data
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Failed to store structured summary in database for call {call_id}: {e}")
            # Return extracted data even if storage fails
            return extracted_data


# Convenience function for dependency injection
def get_post_processing_service() -> PostProcessingService:
    """
    Get post-processing service instance.
    
    Used as FastAPI dependency.
    """
    return PostProcessingService()

