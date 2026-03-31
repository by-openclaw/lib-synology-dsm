"""Live NAS integration tests — SharePermissionManager."""

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
class TestSharePermissionManager:
    """Full ACL lifecycle: list, set, set_bulk, ensure present/absent."""

    @pytest.fixture(autouse=True)
    def setup(self, client, run_id):
        from synology_dsm import ShareManager, UserManager
        from synology_dsm.share_permissions import SharePermissionManager

        self.perms = SharePermissionManager(client)
        self.shares = ShareManager(client)
        self.users = UserManager(client)
        self.sharename = f"rune-sp-{run_id}"
        self.username = f"rune-spu-{run_id}"
        # Create test share and user
        self.shares.ensure(self.sharename, state="present", volume_path="/volume1")
        self.users.ensure(self.username, password=TEST_USER_PASS, state="present")
        yield
        try:
            self.shares.ensure(self.sharename, state="absent")
        except Exception:
            pass
        try:
            self.users.ensure(self.username, state="absent")
        except Exception:
            pass

    def test_list_returns_list(self):
        result = self.perms.list(self.sharename)
        assert isinstance(result, list)

    def test_set_user_permission(self):
        result = self.perms.set(self.sharename, self.username, "read_write")
        assert result["changed"] is True
        assert result["action"] == "set"

    def test_set_bulk_permissions(self):
        result = self.perms.set_bulk(self.sharename, [
            {"name": self.username, "is_group": False, "perm": "read_only"},
        ])
        assert result["changed"] is True
        assert result["action"] == "set_bulk"
        assert result["count"] == 1

    def test_ensure_present_sets(self):
        r = self.perms.ensure(self.sharename, self.username, "read_write")
        assert isinstance(r["changed"], bool)
        assert r["action"] in ("set", "noop")

    def test_ensure_present_noop(self):
        self.perms.set(self.sharename, self.username, "read_write")
        r = self.perms.ensure(self.sharename, self.username, "read_write")
        assert r["changed"] is False
        assert r["action"] == "noop"

    def test_ensure_absent_removes(self):
        self.perms.set(self.sharename, self.username, "read_write")
        r = self.perms.ensure(self.sharename, self.username, "read_write", state="absent")
        assert r["changed"] is True
        assert r["action"] == "removed"

    def test_ensure_absent_noop(self):
        self.perms.set(self.sharename, self.username, "no_access")
        r = self.perms.ensure(self.sharename, self.username, "read_write", state="absent")
        assert r["changed"] is False
        assert r["action"] == "noop"

    def test_dry_run_does_not_change(self):
        r = self.perms.set(self.sharename, self.username, "read_write", dry_run=True)
        assert r["dry_run"] is True
