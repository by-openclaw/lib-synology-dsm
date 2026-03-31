"""Live NAS integration tests — NFSManager."""

from __future__ import annotations

import os
import uuid

import pytest

# ── Config ────────────────────────────────────────────────────────────────────
NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = int(os.environ.get("NAS_PORT") or "5001")
ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")
NFS_CLIENT = os.environ.get("NFS_CLIENT", "10.6.224.0/20")

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
class TestNFSManager:
    """Full ensure() lifecycle for NFS rules (requires a share as prerequisite)."""

    @pytest.fixture(autouse=True)
    def setup(self, client, run_id) -> None:  # noqa: ANN001
        from synology_dsm import NFSManager, ShareManager

        self.shares = ShareManager(client)
        self.nfs = NFSManager(client)
        self.sharename = f"rune-s-{run_id}"
        yield
        try:
            self.shares.ensure(self.sharename, state="absent")
        except Exception:
            pass

    def test_nfs_ensure_present_creates(self) -> None:
        self.shares.ensure(self.sharename, state="present", volume_path="/volume1")
        r = self.nfs.ensure(self.sharename, NFS_CLIENT, state="present", rw=True)
        assert r["changed"] is True
        assert r["action"] == "created"

    def test_nfs_ensure_present_noop(self) -> None:
        self.shares.ensure(self.sharename, state="present", volume_path="/volume1")
        self.nfs.ensure(self.sharename, NFS_CLIENT, state="present", rw=True)
        r = self.nfs.ensure(self.sharename, NFS_CLIENT, state="present", rw=True)
        assert r["changed"] is False
        assert r["action"] == "noop"

    def test_nfs_ensure_updates_privilege(self) -> None:
        self.shares.ensure(self.sharename, state="present", volume_path="/volume1")
        self.nfs.ensure(self.sharename, NFS_CLIENT, state="present", rw=True)
        r = self.nfs.ensure(self.sharename, NFS_CLIENT, state="present", rw=False)
        assert r["changed"] is True
        assert r["action"] == "updated"
        assert r["after"]["privilege"] == "ro"

    def test_nfs_ensure_absent_deletes(self) -> None:
        self.shares.ensure(self.sharename, state="present", volume_path="/volume1")
        self.nfs.ensure(self.sharename, NFS_CLIENT, state="present", rw=True)
        r = self.nfs.ensure(self.sharename, NFS_CLIENT, state="absent")
        assert r["changed"] is True
        assert r["action"] == "deleted"

    def test_nfs_ensure_absent_noop(self) -> None:
        self.shares.ensure(self.sharename, state="present", volume_path="/volume1")
        self.nfs.ensure(self.sharename, NFS_CLIENT, state="absent")
        r = self.nfs.ensure(self.sharename, NFS_CLIENT, state="absent")
        assert r["changed"] is False
        assert r["action"] == "noop"
