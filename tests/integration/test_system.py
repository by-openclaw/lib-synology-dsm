"""Live NAS integration tests — SystemManager."""

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


@nas_required
class TestSystemManager:
    """System info queries — read-only."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        from synology_dsm.system import SystemManager

        self.system = SystemManager(client)

    def test_get_info_returns_dict(self):
        result = self.system.get_info()
        assert isinstance(result, dict)

    def test_get_info_has_expected_fields(self):
        result = self.system.get_info()
        assert "model" in result
        assert "serial" in result
        assert "hostname" in result
        assert "dsm_version" in result

    def test_get_info_model_not_none(self):
        result = self.system.get_info()
        assert result["model"] is not None

    def test_ensure_returns_noop(self):
        r = self.system.ensure()
        assert r["changed"] is False
        assert r["action"] == "noop"
        assert "info" in r

    def test_ensure_info_has_fields(self):
        r = self.system.ensure()
        info = r["info"]
        assert "model" in info
        assert "dsm_version" in info
