"""Integration test configuration — requires live NAS (set NAS_HOST env var).

Credentials are loaded from .devcontainer/.env.local (gitignored) if present,
so the container always starts even without env vars pre-set.
"""

import os
from pathlib import Path

import pytest

# Load .devcontainer/.env.local if it exists — allows running inside the dev container
# without needing --env-file or Windows environment variables.
# python-dotenv is a dev dependency; fail gracefully if somehow not installed.
try:
    from dotenv import load_dotenv

    _env_file = Path(__file__).parents[2] / ".devcontainer" / ".env.local"
    if _env_file.exists():
        load_dotenv(_env_file, override=False)  # override=False: real env vars win
except ImportError:
    pass

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
