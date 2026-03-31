"""
Live NAS integration tests — lib-synology-dsm

Tests have been split into per-manager files:
  - test_users.py, test_groups.py, test_shares.py, test_nfs.py
  - test_filestation.py, test_storage.py, test_quota.py
  - test_bandwidth.py, test_trafficcontrol.py
  - test_share_permissions.py, test_system.py

Run all:
  pytest tests/integration/ -m integration -v
"""

from __future__ import annotations

import os
import uuid

import pytest

# ── Config ────────────────────────────────────────────────────────────────────
NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = int(os.environ.get("NAS_PORT") or "5001")
ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")

# Skip entire module when NAS not configured
pytestmark = pytest.mark.integration
nas_required = pytest.mark.skipif(
    not NAS_HOST or not ADMIN_USER or not ADMIN_PASS,
    reason="NAS_HOST / API_USER / API_PASS not set — skipping live NAS tests",
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def run_id() -> str:
    """Unique 8-char hex ID for this test run — scopes all test resources."""
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="module")
def client():
    """Authenticated DSMClient for the entire test module."""
    from synology_dsm import DSMClient

    if not NAS_HOST or not ADMIN_USER or not ADMIN_PASS:
        pytest.skip("NAS_HOST / API_USER / API_PASS not set")

    c = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    c.login(ADMIN_USER, ADMIN_PASS)
    yield c
    try:
        c.logout()
    except Exception:
        pass


# ── Auth ──────────────────────────────────────────────────────────────────────


@nas_required
class TestAuth:
    def test_login_produces_sid(self, client) -> None:  # noqa: ANN001
        assert client._sid is not None
        assert len(client._sid) > 10

    def test_login_produces_synotoken(self, client) -> None:  # noqa: ANN001
        assert client._synotoken is not None
        assert len(client._synotoken) > 0

    def test_logout_and_relogin(self) -> None:
        """Logout clears SID; re-login issues a fresh session."""
        from synology_dsm import DSMClient

        cli = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
        cli.login(ADMIN_USER, ADMIN_PASS)
        assert cli._sid is not None
        cli.logout()
        assert cli._sid is None
        cli.login(ADMIN_USER, ADMIN_PASS)
        assert cli._sid is not None
        cli.logout()

    def test_wrong_password_raises_auth_error(self) -> None:
        """Wrong password must raise DSMAuthError (error 400).

        Synology DSM logs the failed attempt in Security → Login activity.
        This confirms the error is surfaced correctly — not swallowed.
        """
        from synology_dsm import DSMClient
        from synology_dsm.exceptions import DSMAuthError

        cli = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
        with pytest.raises(DSMAuthError, match="400|Login failed|Invalid password"):
            cli.login(ADMIN_USER, "definitely-wrong-password-rune-test")

    def test_wrong_user_raises_auth_error(self) -> None:
        """Non-existent user must raise DSMAuthError (error 400).

        Synology DSM logs the failed attempt in Security → Login activity.
        This confirms the error is surfaced correctly — not swallowed.
        """
        from synology_dsm import DSMClient
        from synology_dsm.exceptions import DSMAuthError

        cli = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
        with pytest.raises(DSMAuthError, match="400|Login failed|No such account"):
            cli.login("rune-nonexistent-user-xyzzy", "some-password")


# ── Standalone runner (for human-readable report) ─────────────────────────────

if __name__ == "__main__":
    import subprocess
    import sys

    args = sys.argv[1:]
    report_path = None
    if "--report" in args:
        idx = args.index("--report")
        report_path = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/",
        "-m",
        "integration",
        "-v",
        "--tb=short",
        "--no-header",
    ]
    if report_path:
        cmd += [f"--junitxml={report_path}.xml"]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)
