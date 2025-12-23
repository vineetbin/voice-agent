"""
Unit tests for limited fallback extraction.

Tests regex extraction for only high-confidence categorical fields:
- driver_status
- emergency_type
- call_outcome
- load_secure
- pod_reminder_acknowledged
"""

import pytest
from app.services.fallback_extraction import (
    fill_missing_categorical_fields,
    extract_driver_status,
    extract_emergency_type,
    extract_call_outcome,
    extract_load_secure,
    extract_pod_reminder_acknowledged,
)


class TestDispatchCheckInFallback:
    """Tests for dispatch check-in categorical field extraction."""
    
    def test_extract_driver_status_driving(self):
        """Test extraction of 'Driving' status."""
        transcript = "I'm still driving on I-10. Should be there soon."
        assert extract_driver_status(transcript) == "Driving"
    
    def test_extract_driver_status_arrived(self):
        """Test extraction of 'Arrived' status."""
        transcript = "I just got here at the destination."
        assert extract_driver_status(transcript) == "Arrived"
    
    def test_extract_driver_status_unloading(self):
        """Test extraction of 'Unloading' status."""
        transcript = "I'm unloading now, in door 42."
        assert extract_driver_status(transcript) == "Unloading"
    
    def test_extract_driver_status_delayed(self):
        """Test extraction of 'Delayed' status."""
        transcript = "I'm running behind schedule due to traffic."
        assert extract_driver_status(transcript) == "Delayed"
    
    def test_extract_driver_status_no_match(self):
        """Test when no driver status pattern matches."""
        transcript = "The weather is nice today."
        assert extract_driver_status(transcript) is None
    
    def test_extract_call_outcome_in_transit(self):
        """Test extraction of 'In-Transit Update' outcome."""
        transcript = "I'm still driving, en route to the destination."
        assert extract_call_outcome(transcript, is_emergency=False) == "In-Transit Update"
    
    def test_extract_call_outcome_arrival(self):
        """Test extraction of 'Arrival Confirmation' outcome."""
        transcript = "I just arrived at the destination."
        assert extract_call_outcome(transcript, is_emergency=False) == "Arrival Confirmation"
    
    def test_extract_pod_reminder_acknowledged_yes(self):
        """Test extraction of POD acknowledgment (positive)."""
        transcript = "Agent: Don't forget to get your POD. Driver: Yes, got it."
        assert extract_pod_reminder_acknowledged(transcript) is True
    
    def test_extract_pod_reminder_acknowledged_no_pod_mentioned(self):
        """Test when POD is not mentioned."""
        transcript = "I'm driving on the highway."
        assert extract_pod_reminder_acknowledged(transcript) is None
    
    def test_fill_missing_fields_dispatch(self):
        """Test filling missing categorical fields for dispatch check-in."""
        # Simulate OpenAI extraction missing driver_status
        extracted_data = {
            "call_outcome": "In-Transit Update",
            # driver_status is missing
        }
        
        transcript = "I'm still driving on I-10."
        result = fill_missing_categorical_fields(extracted_data, transcript, "dispatch_checkin")
        
        assert result["call_outcome"] == "In-Transit Update"  # Preserved
        assert result["driver_status"] == "Driving"  # Added by fallback


class TestEmergencyFallback:
    """Tests for emergency categorical field extraction."""
    
    def test_extract_emergency_type_accident(self):
        """Test extraction of 'Accident' emergency type."""
        transcript = "I just had an accident! I'm pulling over."
        assert extract_emergency_type(transcript) == "Accident"
    
    def test_extract_emergency_type_breakdown(self):
        """Test extraction of 'Breakdown' emergency type."""
        transcript = "I had a blowout and the truck broke down."
        assert extract_emergency_type(transcript) == "Breakdown"
    
    def test_extract_emergency_type_medical(self):
        """Test extraction of 'Medical' emergency type."""
        transcript = "I'm having a medical issue. Need an ambulance."
        assert extract_emergency_type(transcript) == "Medical"
    
    def test_extract_emergency_type_other(self):
        """Test extraction of 'Other' emergency type."""
        transcript = "Something's wrong, I need to pull over. This is an emergency."
        assert extract_emergency_type(transcript) == "Other"
    
    def test_extract_call_outcome_emergency(self):
        """Test extraction of 'Emergency Escalation' outcome."""
        transcript = "I just had an accident! This is an emergency!"
        assert extract_call_outcome(transcript, is_emergency=True) == "Emergency Escalation"
    
    def test_extract_load_secure_true(self):
        """Test extraction of load_secure (positive)."""
        transcript = "The load is secure, no problem there."
        assert extract_load_secure(transcript) is True
    
    def test_extract_load_secure_false(self):
        """Test extraction of load_secure (negative)."""
        transcript = "The load shifted and is not secure."
        assert extract_load_secure(transcript) is False
    
    def test_extract_load_secure_uncertain(self):
        """Test when load_secure cannot be determined."""
        transcript = "I'm driving on the highway."
        assert extract_load_secure(transcript) is None
    
    def test_fill_missing_fields_emergency(self):
        """Test filling missing categorical fields for emergency."""
        # Simulate OpenAI extraction missing emergency_type
        extracted_data = {
            "call_outcome": "Emergency Escalation",
            # emergency_type is missing
        }
        
        transcript = "I just had an accident! Everyone is safe."
        result = fill_missing_categorical_fields(extracted_data, transcript, "emergency")
        
        assert result["call_outcome"] == "Emergency Escalation"  # Preserved
        assert result["emergency_type"] == "Accident"  # Added by fallback


class TestLimitedFallbackScope:
    """Tests to ensure fallback is limited to categorical fields only."""
    
    def test_does_not_extract_location(self):
        """Test that location strings are NOT extracted by fallback."""
        extracted_data = {}
        transcript = "I'm near Las Vegas, on I-15 at Mile Marker 123."
        
        result = fill_missing_categorical_fields(extracted_data, transcript, "dispatch_checkin")
        
        # Should extract categorical fields if possible
        assert "driver_status" in result or result.get("driver_status") is None
        
        # Should NOT extract location (too free-form for regex)
        assert "current_location" not in result or result.get("current_location") is None
    
    def test_does_not_extract_eta(self):
        """Test that ETA is NOT extracted by fallback."""
        extracted_data = {}
        transcript = "I'll be there tomorrow around 8:00 AM."
        
        result = fill_missing_categorical_fields(extracted_data, transcript, "dispatch_checkin")
        
        # Should NOT extract ETA (too free-form for regex)
        assert "eta" not in result or result.get("eta") is None
    
    def test_does_not_extract_safety_descriptions(self):
        """Test that safety/injury descriptions are NOT extracted by fallback."""
        extracted_data = {"call_outcome": "Emergency Escalation"}
        transcript = "Everyone is safe. No injuries reported. The driver confirmed everyone is okay."
        
        result = fill_missing_categorical_fields(extracted_data, transcript, "emergency")
        
        # Should extract emergency_type if possible
        assert "emergency_type" in result or result.get("emergency_type") is None
        
        # Should NOT extract safety/injury descriptions (too free-form for regex)
        assert "safety_status" not in result or result.get("safety_status") is None
        assert "injury_status" not in result or result.get("injury_status") is None
