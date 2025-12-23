"""
Unit tests for extraction schemas.

Tests Pydantic schema validation for structured extraction data.
"""

import pytest
from app.services.extraction_schemas import DispatchCheckInExtraction, EmergencyExtraction
from pydantic import ValidationError


class TestDispatchCheckInExtraction:
    """Tests for dispatch check-in extraction schema."""
    
    def test_valid_in_transit_extraction(self):
        """Test valid in-transit update extraction."""
        data = {
            "call_outcome": "In-Transit Update",
            "driver_status": "Driving",
            "current_location": "I-10 near Indio, CA",
            "eta": "Tomorrow, 8:00 AM",
            "delay_reason": "None",
            "unloading_status": "N/A",
            "pod_reminder_acknowledged": False,
        }
        extraction = DispatchCheckInExtraction(**data)
        assert extraction.call_outcome == "In-Transit Update"
        assert extraction.driver_status == "Driving"
    
    def test_valid_arrival_extraction(self):
        """Test valid arrival confirmation extraction."""
        data = {
            "call_outcome": "Arrival Confirmation",
            "driver_status": "Arrived",
            "unloading_status": "In Door 42",
            "pod_reminder_acknowledged": True,
        }
        extraction = DispatchCheckInExtraction(**data)
        assert extraction.call_outcome == "Arrival Confirmation"
        assert extraction.driver_status == "Arrived"
    
    def test_invalid_call_outcome(self):
        """Test validation fails with invalid call_outcome."""
        data = {
            "call_outcome": "Invalid Outcome",
            "driver_status": "Driving",
        }
        with pytest.raises(ValidationError):
            DispatchCheckInExtraction(**data)
    
    def test_invalid_driver_status(self):
        """Test validation fails with invalid driver_status."""
        data = {
            "call_outcome": "In-Transit Update",
            "driver_status": "Invalid Status",
        }
        with pytest.raises(ValidationError):
            DispatchCheckInExtraction(**data)
    
    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        data = {
            "call_outcome": "In-Transit Update",
            "driver_status": "Driving",
        }
        extraction = DispatchCheckInExtraction(**data)
        assert extraction.current_location is None
        assert extraction.eta is None


class TestEmergencyExtraction:
    """Tests for emergency extraction schema."""
    
    def test_valid_accident_extraction(self):
        """Test valid accident emergency extraction."""
        data = {
            "call_outcome": "Emergency Escalation",
            "emergency_type": "Accident",
            "safety_status": "Driver confirmed everyone is safe",
            "injury_status": "No injuries reported",
            "emergency_location": "I-15 North, Mile Marker 123",
            "load_secure": True,
            "escalation_status": "Connected to Human Dispatcher",
        }
        extraction = EmergencyExtraction(**data)
        assert extraction.call_outcome == "Emergency Escalation"
        assert extraction.emergency_type == "Accident"
        assert extraction.load_secure is True
    
    def test_valid_breakdown_extraction(self):
        """Test valid breakdown emergency extraction."""
        data = {
            "emergency_type": "Breakdown",
            "load_secure": True,
        }
        extraction = EmergencyExtraction(**data)
        assert extraction.emergency_type == "Breakdown"
        assert extraction.call_outcome == "Emergency Escalation"  # Default value
        assert extraction.escalation_status == "Connected to Human Dispatcher"  # Default value
    
    def test_invalid_emergency_type(self):
        """Test validation fails with invalid emergency_type."""
        data = {
            "emergency_type": "Invalid Type",
        }
        with pytest.raises(ValidationError):
            EmergencyExtraction(**data)
    
    def test_optional_fields(self):
        """Test that optional fields can be omitted."""
        data = {
            "emergency_type": "Accident",
        }
        extraction = EmergencyExtraction(**data)
        assert extraction.safety_status is None
        assert extraction.injury_status is None
        assert extraction.emergency_location is None
        assert extraction.load_secure is None

