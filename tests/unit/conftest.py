"""Shared fixtures for unit tests."""

import pytest
from unittest.mock import MagicMock
from synology_dsm.client import DSMClient


@pytest.fixture
def mock_client():
    """Mock DSMClient with a fake session token."""
    client = MagicMock(spec=DSMClient)
    client._synotoken = "fake-token"
    client._sid = "fake-sid"
    return client
