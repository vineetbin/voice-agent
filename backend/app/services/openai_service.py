"""
OpenAI service for structured transcript extraction.

This service handles GPT-4 integration for extracting structured data
from call transcripts using JSON schema validation.
"""

import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors."""
    pass


class OpenAIService:
    """
    Service class for OpenAI operations.
    
    Handles structured extraction from transcripts using GPT-4
    with JSON schema validation.
    """
    
    def __init__(self):
        """Initialize OpenAI client with API key."""
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"  # Using gpt-4o-mini for cost efficiency
    
    def extract_structured_data(
        self,
        transcript: str,
        schema: BaseModel,
        scenario_type: str,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured data from transcript using GPT-4.
        
        Args:
            transcript: Full call transcript text
            schema: Pydantic model defining the expected structure
            scenario_type: 'dispatch_checkin' or 'emergency'
            system_prompt: Optional custom prompt override
            
        Returns:
            Dictionary with extracted data matching the schema
            
        Raises:
            OpenAIServiceError: If extraction fails
        """
        try:
            # Get JSON schema from Pydantic model
            json_schema = schema.model_json_schema()
            
            # Generate system prompt with explicit field name instructions
            if not system_prompt:
                system_prompt = self._get_default_system_prompt(scenario_type, json_schema)
            
            # Extract field names and their allowed values from schema for clearer instructions
            properties = json_schema.get("properties", {})
            required_fields = json_schema.get("required", [])
            
            # Build explicit field list with allowed values
            field_instructions = []
            for field_name, field_spec in properties.items():
                field_desc = f'"{field_name}"'
                if "enum" in field_spec:
                    enum_values = ', '.join([f'"{v}"' for v in field_spec['enum']])
                    field_desc += f" (must be exactly one of: {enum_values})"
                elif field_spec.get("type") == "boolean":
                    field_desc += " (boolean: true, false, or null)"
                elif "anyOf" in field_spec:
                    # Handle Literal types from Pydantic
                    for option in field_spec["anyOf"]:
                        if "const" in option:
                            const_value = option["const"]
                            field_desc += f' (must be exactly "{const_value}")'
                            break
                field_instructions.append(field_desc)
            
            # Build the extraction prompt with explicit instructions
            user_prompt = f"""Extract structured information from the following call transcript.

CRITICAL FIELD NAME REQUIREMENTS:
- Use EXACT field names (case-sensitive, singular forms)
- Do NOT use plural forms (e.g., use "delay_reason" NOT "delay_reasons")
- Do NOT add fields that are not listed below

Required fields: {', '.join([f'"{f}"' for f in required_fields])}

All fields and their allowed values:
{chr(10).join(f'- {field}' for field in field_instructions)}

Schema structure:
{json.dumps(json_schema, indent=2)}

Transcript:
{transcript}

Instructions:
1. Use ONLY the exact field names listed above (singular forms, case-sensitive)
2. For fields with specific allowed values, use ONLY those exact values (no variations)
3. Extract only information explicitly stated in the transcript
4. Use null for fields where no information is available
5. Do not add any fields not in the list above

Return a JSON object using the EXACT field names and values specified above."""
            
            # Call OpenAI with structured output
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent extraction
            )
            
            # Parse response
            content = response.choices[0].message.content
            if not content:
                raise OpenAIServiceError("Empty response from OpenAI")
            
            extracted_data = json.loads(content)
            
            # Validate against schema
            try:
                validated = schema.model_validate(extracted_data)
                return validated.model_dump(exclude_none=True)
            except ValidationError as e:
                # Log the validation errors for debugging
                error_details = []
                for error in e.errors():
                    field = error.get("loc", ("unknown",))[0] if error.get("loc") else "unknown"
                    error_type = error.get("type", "unknown")
                    error_msg = error.get("msg", "unknown")
                    error_details.append(f"{field}: {error_type} - {error_msg}")
                
                logger.warning(
                    f"Schema validation failed for OpenAI response. Errors: {', '.join(error_details)}. "
                    f"Returning raw data (will be handled by fallback extraction)."
                )
                # Return raw data - post-processing will handle missing/invalid fields with fallback
                return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            raise OpenAIServiceError(f"Invalid JSON response from OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            raise OpenAIServiceError(f"Failed to extract structured data: {str(e)}")
    
    def _get_default_system_prompt(self, scenario_type: str, json_schema: Dict[str, Any]) -> str:
        """
        Get default system prompt for extraction based on scenario type.
        
        Args:
            scenario_type: 'dispatch_checkin' or 'emergency'
            json_schema: JSON schema from Pydantic model
        """
        base_prompt = """You are an expert at extracting structured information from logistics call transcripts.

CRITICAL REQUIREMENTS:
1. Use EXACT field names from the provided schema (case-sensitive, singular forms)
2. For enum/literal fields, use ONLY the exact values specified - do not create variations
3. Extract only information explicitly stated in the transcript
4. Use null for missing information
5. Do not add fields not in the schema

The schema defines the exact structure you must follow."""
        
        if scenario_type == "emergency":
            return base_prompt + """

For emergency scenarios, focus on:
- emergency_type: Must be exactly one of: "Accident", "Breakdown", "Medical", "Other"
- call_outcome: Must be exactly "Emergency Escalation"
- escalation_status: Must be exactly "Connected to Human Dispatcher"
- load_secure: Boolean (true/false/null)
- safety_status, injury_status, emergency_location: Free-form text or null"""
        else:  # dispatch_checkin
            return base_prompt + """

For dispatch check-in scenarios, focus on:
- call_outcome: Must be exactly one of: "In-Transit Update" or "Arrival Confirmation"
- driver_status: Must be exactly one of: "Driving", "Delayed", "Arrived", "Unloading"
- delay_reason: Must be exactly one of: "Heavy Traffic", "Weather", "None", or null
- unloading_status: Must be exactly one of: "In Door 42", "Waiting for Lumper", "Detention", "N/A", or null
- pod_reminder_acknowledged: Boolean (true/false/null)
- current_location, eta: Free-form text or null

IMPORTANT: Use singular field names (e.g., "delay_reason" not "delay_reasons")."""


# Singleton instance for dependency injection
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """
    Get or create OpenAI service instance.
    
    Used as FastAPI dependency.
    """
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service

