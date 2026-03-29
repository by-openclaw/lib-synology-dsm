"""
Live NAS integration tests — lib-synology-dsm

Real pytest test suite — runs against a live Synology DSM instance.
Every resource goes through the full ensure() lifecycle:
  ensure(present) → changed=True (created)
  ensure(present) → changed=False (noop — state matches)
  ensure(absent)  → changed=True (deleted)
  ensure(absent)  → changed=False (noop — already gone)

Run:
  # All integration tests (requires NAS env vars):
  pytest tests/integration/ -m integration -v

  # Skip integration tests (unit only):
  pytest tests/unit/

Required env vars:
  NAS_HOST        IP or hostname of DSM (e.g. 10.6.224.6)
  API_USER        Admin account (administrators group)
  API_PASS        Admin password
  TEST_USER_PASS  Password to set on test user (default: TmpPass123!)
  NFS_CLIENT      CIDR for NFS rule (default: 10.6.224.0/20)
  FS_BASE_SHARE   Existing share for FileStation tests (default: by-terraform-state)

Also supports standalone run for human-readable report:
  python tests/integration/test_live_nas.py [--report /path/base]
"""

from __future__ import annotations

import os
import tempfile
import uuid

import pytest

# ── Config ────────────────────────────────────────────────────────────────────
NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = int(os.environ.get("NAS_PORT", "5001"))
ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")
TEST_USER_PASS = os.environ.get("TEST_USER_PASS", "TmpPass123!")
NFS_CLIENT = os.environ.get("NFS_CLIENT", "10.6.224.0/20")
FS_BASE_SHARE = os.environ.get("FS_BASE_SHARE", "by-terraform-state")

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


# ── UserManager ───────────────────────────────────────────────────────────────


@nas_required
class TestUserManager:
    """Full ensure() lifecycle: create → noop → delete → noop."""

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


# ── GroupManager ──────────────────────────────────────────────────────────────


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


# ── ShareManager + NFSManager ─────────────────────────────────────────────────


@nas_required
class TestShareManager:
    """Full ensure() lifecycle for shares + NFS rules."""

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

    def test_share_ensure_present_creates(self) -> None:
        r = self.shares.ensure(
            self.sharename,
            state="present",
            volume_path="/volume1",
            description="pytest integration",
        )
        assert r["changed"] is True
        assert r["action"] == "created"

    def test_share_ensure_present_noop(self) -> None:
        self.shares.ensure(
            self.sharename,
            state="present",
            volume_path="/volume1",
            description="pytest integration",
        )
        r = self.shares.ensure(
            self.sharename,
            state="present",
            volume_path="/volume1",
            description="pytest integration",
        )
        assert r["changed"] is False
        assert r["action"] == "noop"

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

    def test_share_ensure_absent_deletes(self) -> None:
        self.shares.ensure(self.sharename, state="present", volume_path="/volume1")
        r = self.shares.ensure(self.sharename, state="absent")
        assert r["changed"] is True
        assert r["action"] == "deleted"

    def test_share_ensure_absent_noop(self) -> None:
        self.shares.ensure(self.sharename, state="absent")
        r = self.shares.ensure(self.sharename, state="absent")
        assert r["changed"] is False
        assert r["action"] == "noop"


# ── FileStationManager ────────────────────────────────────────────────────────


@nas_required
class TestFileStationManager:
    """Full lifecycle: mkdir / ensure / upload / list / download / delete."""

    @pytest.fixture(autouse=True)
    def setup(self, client, run_id) -> None:  # noqa: ANN001
        from synology_dsm.filestation import FileStationManager

        self.fs = FileStationManager(client)
        self.folder = f"rune-f-{run_id}"
        self.folder_path = f"/{FS_BASE_SHARE}/{self.folder}"
        self.filename = f"rune-upload-{run_id}.txt"
        yield
        try:
            self.fs.ensure(self.folder_path, state="absent")
        except Exception:
            pass

    def test_list_shares(self) -> None:
        shares = self.fs.list_shares()
        assert isinstance(shares, list)
        assert len(shares) > 0

    def test_ensure_folder_present_creates(self) -> None:
        r = self.fs.ensure(self.folder_path, state="present")
        assert r["changed"] is True
        assert r["action"] == "created"

    def test_ensure_folder_present_noop(self) -> None:
        self.fs.ensure(self.folder_path, state="present")
        r = self.fs.ensure(self.folder_path, state="present")
        assert r["changed"] is False
        assert r["action"] == "noop"

    def test_upload_and_list(self) -> None:
        self.fs.ensure(self.folder_path, state="present")
        tmp = os.path.join(tempfile.gettempdir(), self.filename)
        with open(tmp, "w") as f:
            f.write("lib-synology-dsm pytest integration test\n")
        try:
            result = self.fs.upload(tmp, self.folder_path, overwrite=True)
            assert result.get("success") or result.get("skipped") is False
            files = self.fs.list(self.folder_path)
            names = [f["name"] for f in files]
            assert self.filename in names
        finally:
            os.unlink(tmp)

    def test_download_content(self) -> None:
        self.fs.ensure(self.folder_path, state="present")
        content = b"lib-synology-dsm pytest download test\n"
        tmp_up = os.path.join(tempfile.gettempdir(), self.filename)
        with open(tmp_up, "wb") as f:
            f.write(content)
        self.fs.upload(tmp_up, self.folder_path, overwrite=True)
        os.unlink(tmp_up)

        tmp_dl = os.path.join(tempfile.gettempdir(), f"rune-dl-{uuid.uuid4().hex[:8]}.txt")
        try:
            self.fs.download(f"{self.folder_path}/{self.filename}", tmp_dl)
            with open(tmp_dl, "rb") as f:
                downloaded = f.read()
            assert b"lib-synology-dsm" in downloaded
        finally:
            try:
                os.unlink(tmp_dl)
            except FileNotFoundError:
                pass

    def test_ensure_folder_absent_deletes(self) -> None:
        self.fs.ensure(self.folder_path, state="present")
        r = self.fs.ensure(self.folder_path, state="absent")
        assert r["changed"] is True
        assert r["action"] == "deleted"

    def test_ensure_folder_absent_noop(self) -> None:
        self.fs.ensure(self.folder_path, state="absent")
        r = self.fs.ensure(self.folder_path, state="absent")
        assert r["changed"] is False
        assert r["action"] == "noop"


# ── Standalone runner (for human-readable report) ─────────────────────────────

if __name__ == "__main__":
    import subprocess
    import sys

    args = sys.argv[1:]
    report_path = None
    if "--report" in args:
        idx = args.index("--report")
        report_path = args[idx + 1]
        args = args[:idx] + args[idx + 2 :]

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/test_live_nas.py",
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
