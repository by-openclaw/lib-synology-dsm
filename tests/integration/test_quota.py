"""Live NAS integration tests — QuotaManager."""

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
class TestQuotaManager:
    """Quota queries — read-only, uses admin user and administrators group."""

    @pytest.fixture(autouse=True)
    def setup(self, client) -> None:  # noqa: ANN001
        from synology_dsm.quota import QuotaManager

        self.quota = QuotaManager(client)

    def test_get_group_quota_returns_dict(self) -> None:
        result = self.quota.get_group_quota("administrators")
        assert isinstance(result, dict)

    def test_get_user_quota_returns_dict(self) -> None:
        result = self.quota.get_user_quota(ADMIN_USER)
        assert isinstance(result, dict)

    def test_get_quota_group_subject_type(self) -> None:
        result = self.quota.get_quota("administrators", "group")
        assert isinstance(result, dict)

    def test_get_quota_user_subject_type(self) -> None:
        result = self.quota.get_quota(ADMIN_USER, "user")
        assert isinstance(result, dict)

    def test_invalid_subject_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid subject_type"):
            self.quota.get_quota("administrators", "invalid")

    def test_ensure_present_creates_or_updates(self) -> None:
        """ensure(present) — sets quota, returns {changed, action}."""
        r = self.quota.ensure(ADMIN_USER, "user", "/volume1", quota_mb=10240)
        assert isinstance(r["changed"], bool)
        assert r["action"] in ("created", "updated", "none")

    def test_ensure_present_noop(self) -> None:
        """ensure(present) — noop when quota already matches."""
        self.quota.ensure(ADMIN_USER, "user", "/volume1", quota_mb=10240)
        r = self.quota.ensure(ADMIN_USER, "user", "/volume1", quota_mb=10240)
        assert r["changed"] is False
        assert r["action"] == "none"

    def test_ensure_absent_removes(self) -> None:
        """ensure(absent) — sets quota to 0 (unlimited), returns changed."""
        self.quota.ensure(ADMIN_USER, "user", "/volume1", quota_mb=10240)
        r = self.quota.ensure(ADMIN_USER, "user", "/volume1", state="absent")
        assert isinstance(r["changed"], bool)
        assert r["action"] in ("removed", "none")

    def test_set_user_quota_returns_dict(self) -> None:
        """set_user_quota() — returns {changed=True, action="set"}."""
        r = self.quota.set_user_quota(ADMIN_USER, "/volume1", quota_mb=0)
        assert r["changed"] is True
        assert r["action"] == "set"

    def test_set_group_quota_returns_dict(self) -> None:
        """set_group_quota() — returns {changed=True, action="set"}."""
        r = self.quota.set_group_quota("administrators", "/volume1", quota_mb=0)
        assert r["changed"] is True
        assert r["action"] == "set"

    def test_dry_run_does_not_change(self) -> None:
        """ensure() dry_run=True — returns plan without writing."""
        r = self.quota.ensure(ADMIN_USER, "user", "/volume1", quota_mb=51200, dry_run=True)
        assert r.get("dry_run") is True
        assert isinstance(r["changed"], bool)
