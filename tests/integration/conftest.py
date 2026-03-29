"""Integration test configuration — requires live NAS (set NAS_HOST env var)."""

import os

import pytest
from synology_dsm import DSMClient

NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = 5001
ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")


@pytest.fixture(scope="session")
def dsm_client():
    """Session-scoped DSMClient logged in to the live NAS."""
    client = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    client.login(ADMIN_USER, ADMIN_PASS)
    yield client
    client.logout()
