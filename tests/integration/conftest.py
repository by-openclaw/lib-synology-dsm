"""Integration test configuration — requires live NAS.

Credentials are loaded from infra-synology-nas.json (KV fields block).
Path resolved via NAS_CREDS_JSON env var, or falls back to the workspace default.

  NAS_CREDS_JSON=~/.openclaw/workspace/infra/secrets/fabric/infra-synology-nas.json \\
  pytest tests/integration/ -v
"""

import json
import os
from pathlib import Path

import pytest

from synology_dsm import DSMClient

_DEFAULT_CREDS = Path.home() / ".openclaw/workspace/infra/secrets/fabric/infra-synology-nas.json"
_creds_path = Path(os.environ.get("NAS_CREDS_JSON", str(_DEFAULT_CREDS)))

if not _creds_path.exists():
    raise FileNotFoundError(
        f"NAS credentials file not found: {_creds_path}\n"
        "Set NAS_CREDS_JSON env var to the correct path."
    )

_creds = json.loads(_creds_path.read_text())["fields"]

NAS_HOST: str = _creds["host"]
NAS_PORT: int = int(_creds["port"])
ADMIN_USER: str = _creds["svc_rune_username"]  # executor — administrators group
ADMIN_PASS: str = _creds["svc_rune_password"]
AUDIT_USER: str = _creds["svc_opus_username"]  # auditor — users group (read-only)
AUDIT_PASS: str = _creds["svc_opus_password"]


@pytest.fixture(scope="session")
def dsm_client():
    """Session-scoped DSMClient logged in as svc-rune (executor — full CRUD)."""
    client = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    client.login(ADMIN_USER, ADMIN_PASS)
    yield client
    client.logout()


@pytest.fixture(scope="session")
def audit_client():
    """Session-scoped DSMClient logged in as svc-opus (auditor — read-only).

    Use this fixture in tests that verify read-only operations succeed
    and write operations are correctly blocked (expect DSMPermissionError or HTTP 403).
    Skipped automatically if AUDIT_USER / AUDIT_PASS env vars are not set.
    """
    if not AUDIT_USER or not AUDIT_PASS:
        pytest.skip("AUDIT_USER / AUDIT_PASS not set — skipping audit client tests")
    client = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    # Non-admin users on DSM 7.1.x get error 402 with session='DSM'.
    # Empty session string works — DSM treats it as a generic API session.
    client.login(AUDIT_USER, AUDIT_PASS, session="")
    yield client
    client.logout()
