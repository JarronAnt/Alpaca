# tests/conftest.py
"""Pytest configuration."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    return "Test response"


@pytest.fixture
def mock_tool_result():
    """Mock tool result."""
    return MagicMock(success=True, output="Done", error=None)
