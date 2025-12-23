"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
from supabase import Client


@pytest.fixture
def mock_db():
    """Mock Supabase client for testing."""
    db = Mock(spec=Client)
    db.table = Mock(return_value=db)
    db.select = Mock(return_value=db)
    db.insert = Mock(return_value=db)
    db.update = Mock(return_value=db)
    db.eq = Mock(return_value=db)
    db.execute = Mock(return_value=MagicMock(data=[]))
    return db

