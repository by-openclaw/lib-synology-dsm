"""Integration test configuration — requires live NAS (set NAS_HOST env var).

Credentials are loaded from the root `.env` file (gitignored) if present.
Works for both native Python runs and inside the dev container — same file,
same path, no duplication.

  cp .env.example .env      # fill in API_PASS and TEST_USER_PASS
  pytest tests/integration/ -v
"""

import os
from pathlib import Path

import pytest

# Load root .env if it exists.
# override=False: real env vars (shell exports, CI secrets) always win over the file.
# python-dotenv is in dev/container extras; fail gracefully if somehow absent.
try:
    from dotenv import load_dotenv

    _env_file = Path(__file__).parents[2] / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=False)
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
