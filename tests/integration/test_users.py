"""Live NAS integration tests — UserManager."""

from __future__ import annotations

import os
import uuid

import pytest

# ── Config ────────────────────────────────────────────────────────────────────
NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = int(os.environ.get("NAS_PORT") or "5001")
ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")
TEST_USER_PASS = os.environ.get("TEST_USER_PASS", "TmpPass123!")

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
class TestUserManager:
    """Full ensure() lifecycle: create → noop → update → delete → noop + list/list_detailed."""

    @pytest.fixture(autouse=True)
    def setup(self, client, run_id) -> None:  # noqa: ANN001
        from synology_dsm import UserManager

        self.mgr = UserManager(client)
        self.username = f"rune-u-{run_id}"
        yield
        # cleanup — best effort
        try:
            self.mgr.ensure(self.username, state="absent")
        except Exception:
            pass

    def test_list_includes_user_after_create(self) -> None:
        self.mgr.ensure(self.username, password=TEST_USER_PASS, state="present")
        users = self.mgr.list()
        names = [u["name"] for u in users]
        assert self.username in names

    def test_list_detailed_returns_extended_fields(self) -> None:
        self.mgr.ensure(
            self.username,
            password=TEST_USER_PASS,
            state="present",
            description="pytest integration",
        )
        detailed = self.mgr.list_detailed()
        match = [u for u in detailed if u["name"] == self.username]
        assert len(match) == 1, f"{self.username} not found in list_detailed"
        u = match[0]
        assert "email" in u
        assert "enabled" in u
        assert "2fa_enabled" in u

    def test_ensure_present_updates_description(self) -> None:
        self.mgr.ensure(
            self.username, password=TEST_USER_PASS, state="present", description="original"
        )
        r = self.mgr.ensure(
            self.username, password=TEST_USER_PASS, state="present", description="updated"
        )
        assert r["changed"] is True
        assert r["action"] == "updated"
        detailed = self.mgr.list_detailed()
        match = [u for u in detailed if u["name"] == self.username]
        assert match[0]["description"] == "updated"

    def test_ensure_present_creates(self) -> None:
        r = self.mgr.ensure(
            self.username,
            password=TEST_USER_PASS,
            state="present",
            description="pytest integration",
        )
        assert r["changed"] is True
        assert r["action"] == "created"

    def test_ensure_present_noop(self) -> None:
        self.mgr.ensure(
            self.username,
            password=TEST_USER_PASS,
            state="present",
            description="pytest integration",
        )
        r = self.mgr.ensure(
            self.username,
            password=TEST_USER_PASS,
            state="present",
            description="pytest integration",
        )
        assert r["changed"] is False
        assert r["action"] == "noop"

    def test_ensure_absent_deletes(self) -> None:
        self.mgr.ensure(self.username, password=TEST_USER_PASS, state="present")
        r = self.mgr.ensure(self.username, state="absent")
        assert r["changed"] is True
        assert r["action"] == "deleted"

    def test_ensure_absent_noop(self) -> None:
        self.mgr.ensure(self.username, state="absent")
        r = self.mgr.ensure(self.username, state="absent")
        assert r["changed"] is False
        assert r["action"] == "noop"
