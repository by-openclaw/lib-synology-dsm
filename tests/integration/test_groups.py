"""Live NAS integration tests — GroupManager."""

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
class TestGroupManager:
    """Full ensure() lifecycle + member add/remove."""

    @pytest.fixture(autouse=True)
    def setup(self, client, run_id) -> None:  # noqa: ANN001
        from synology_dsm import GroupManager, UserManager

        self.mgr = GroupManager(client)
        self.users = UserManager(client)
        self.groupname = f"rune-g-{run_id}"
        self.username = f"rune-gu-{run_id}"
        yield
        try:
            self.mgr.ensure(self.groupname, state="absent")
            self.users.ensure(self.username, state="absent")
        except Exception:
            pass

    def test_ensure_present_creates(self) -> None:
        r = self.mgr.ensure(self.groupname, state="present", description="pytest integration")
        assert r["changed"] is True
        assert r["action"] == "created"

    def test_ensure_present_noop(self) -> None:
        self.mgr.ensure(self.groupname, state="present", description="pytest integration")
        r = self.mgr.ensure(self.groupname, state="present", description="pytest integration")
        assert r["changed"] is False
        assert r["action"] == "noop"

    def test_add_member(self) -> None:
        self.mgr.ensure(self.groupname, state="present")
        self.users.ensure(self.username, password=TEST_USER_PASS, state="present")
        r = self.mgr.add_member(self.groupname, self.username)
        assert r["changed"] is True
        assert r["action"] in ("added", "noop")  # noop acceptable on DSM 7.1.1 member_list bug

    def test_remove_member(self) -> None:
        self.mgr.ensure(self.groupname, state="present")
        self.users.ensure(self.username, password=TEST_USER_PASS, state="present")
        self.mgr.add_member(self.groupname, self.username)
        r = self.mgr.remove_member(self.groupname, self.username)
        assert r["changed"] is True
        assert r["action"] in ("removed", "noop")  # noop acceptable on DSM 7.1.1 member_list bug

    def test_ensure_absent_deletes(self) -> None:
        self.mgr.ensure(self.groupname, state="present")
        r = self.mgr.ensure(self.groupname, state="absent")
        assert r["changed"] is True
        assert r["action"] == "deleted"

    def test_ensure_absent_noop(self) -> None:
        self.mgr.ensure(self.groupname, state="absent")
        r = self.mgr.ensure(self.groupname, state="absent")
        assert r["changed"] is False
        assert r["action"] == "noop"
