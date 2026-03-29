"""Integration test configuration — requires live NAS at 10.6.224.6."""

import pytest
from synology_dsm import DSMClient

NAS_HOST = "10.6.224.6"
NAS_PORT = 5001
ADMIN_USER = "rune-api"
ADMIN_PASS = "YOUR_PASSWORD"


@pytest.fixture(scope="session")
def dsm_client():
    """Session-scoped DSMClient logged in to the live NAS."""
    client = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    client.login(ADMIN_USER, ADMIN_PASS)
    yield client
    client.logout()
