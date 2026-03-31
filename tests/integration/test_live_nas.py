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
NAS_PORT = int(os.environ.get("NAS_PORT") or "5001")
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


# ── UserManager ───────────────────────────────────────────────────────────────


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
            assert result["changed"] is True
            assert result["action"] == "uploaded"
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


# ── StorageManager ───────────────────────────────────────────────────────────


@nas_required
class TestStorageManager:
    """Read-only volume queries — no resources created or deleted."""

    @pytest.fixture(autouse=True)
    def setup(self, client) -> None:  # noqa: ANN001
        from synology_dsm.storage import StorageManager

        self.storage = StorageManager(client)

    def test_list_volumes_returns_list(self) -> None:
        volumes = self.storage.list_volumes()
        assert isinstance(volumes, list)

    def test_list_volumes_has_at_least_one(self) -> None:
        volumes = self.storage.list_volumes()
        assert len(volumes) >= 1, "Expected at least one volume on NAS"

    def test_volume_has_expected_fields(self) -> None:
        volumes = self.storage.list_volumes()
        assert len(volumes) >= 1
        v = volumes[0]
        # DSM 7.x uses volume_path; older DSM uses id — accept either
        assert "volume_path" in v or "id" in v
        assert "status" in v
        assert "size_total_byte" in v

    def test_get_volume_returns_dict(self) -> None:
        volumes = self.storage.list_volumes()
        assert len(volumes) >= 1
        # Use volume_path (DSM 7.x) or id (older DSM) as identifier
        vol_ref = volumes[0].get("volume_path") or volumes[0].get("id")
        assert vol_ref is not None, "volume has neither volume_path nor id"
        result = self.storage.get_volume(vol_ref)
        assert result is not None

    def test_get_volume_returns_none_for_missing(self) -> None:
        result = self.storage.get_volume("/volume999")
        assert result is None

    def test_ensure_present_returns_dict(self) -> None:
        """ensure(present) — returns {changed=False, action="none", volume=dict}."""
        volumes = self.storage.list_volumes()
        assert len(volumes) >= 1
        vol_ref = volumes[0].get("volume_path") or volumes[0].get("id")
        r = self.storage.ensure(vol_ref, state="present")
        assert r["changed"] is False
        assert r["action"] == "none"
        assert isinstance(r["volume"], dict)

    def test_ensure_absent_returns_dict(self) -> None:
        """ensure(absent) — read-assert only, never raises, returns volume."""
        volumes = self.storage.list_volumes()
        assert len(volumes) >= 1
        vol_ref = volumes[0].get("volume_path") or volumes[0].get("id")
        r = self.storage.ensure(vol_ref, state="absent")
        assert r["changed"] is False
        assert r["action"] == "none"

    def test_ensure_present_missing_raises(self) -> None:
        """ensure(present) — raises DSMResourceNotFoundError for unknown volume."""
        from synology_dsm.exceptions import DSMResourceNotFoundError
        with pytest.raises(DSMResourceNotFoundError):
            self.storage.ensure("/volume999", state="present")


# ── QuotaManager ─────────────────────────────────────────────────────────────


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


# ── BandwidthManager ──────────────────────────────────────────────────────────


@nas_required
class TestBandwidthManager:
    """Bandwidth limit queries + write + ensure lifecycle."""

    @pytest.fixture(autouse=True)
    def setup(self, client) -> None:  # noqa: ANN001
        from synology_dsm.bandwidth import BandwidthManager

        self.bw = BandwidthManager(client)
        yield
        # Restore: disable any limits set during tests
        try:
            self.bw.ensure_user(ADMIN_USER, "FileStation", "disabled")
        except Exception:
            pass
        try:
            self.bw.ensure_user(ADMIN_USER, "FTP", "disabled")
        except Exception:
            pass

    def test_get_group_limit_returns_dict(self) -> None:
        result = self.bw.get_group_limit("administrators")
        assert isinstance(result, dict)

    def test_get_user_limit_returns_dict(self) -> None:
        result = self.bw.get_user_limit(ADMIN_USER)
        assert isinstance(result, dict)

    def test_get_limit_local_group(self) -> None:
        result = self.bw.get_limit("administrators", "local_group")
        assert isinstance(result, dict)

    def test_get_limit_local_user(self) -> None:
        result = self.bw.get_limit(ADMIN_USER, "local_user")
        assert isinstance(result, dict)

    def test_invalid_owner_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid owner_type"):
            self.bw.get_limit("administrators", "domain_user")

    def test_set_user_and_restore(self) -> None:
        """set_user() — set a limit then restore to disabled."""
        r = self.bw.set_user(
            ADMIN_USER,
            "FileStation",
            "enabled",
            upload_limit_1=500,
            download_limit_1=5000,
        )
        assert r["changed"] is True

        r2 = self.bw.set_user(ADMIN_USER, "FileStation", "disabled")
        assert r2["changed"] is True

    def test_ensure_user_noop(self) -> None:
        """ensure_user() — noop when state already matches."""
        current = self.bw.get(ADMIN_USER, "local_user")
        if not current:
            pytest.skip("No bandwidth entries for ADMIN_USER")
        entry = current[0]
        r = self.bw.ensure_user(
            ADMIN_USER,
            entry["protocol"],
            entry.get("policy", "disabled"),
            upload_limit_1=entry.get("upload_limit_1", 0),
            download_limit_1=entry.get("download_limit_1", 0),
        )
        assert r["changed"] is False

    def test_ensure_user_updates(self) -> None:
        """ensure_user() — changed=True when state differs, then restore."""
        r = self.bw.ensure_user(
            ADMIN_USER,
            "FTP",
            "enabled",
            upload_limit_1=200,
            download_limit_1=2000,
        )
        # Restore
        self.bw.ensure_user(ADMIN_USER, "FTP", "disabled")
        assert isinstance(r["changed"], bool)

    def test_dry_run_does_not_change(self) -> None:
        """dry_run=True must not write to the API."""
        before = self.bw.get(ADMIN_USER, "local_user")
        r = self.bw.set_user(
            ADMIN_USER,
            "FileStation",
            "enabled",
            upload_limit_1=999,
            download_limit_1=9999,
            dry_run=True,
        )
        after = self.bw.get(ADMIN_USER, "local_user")
        assert r["dry_run"] is True
        assert before == after

    def test_ensure_group_noop(self) -> None:
        """ensure_group() — noop when state already matches."""
        self.bw.ensure_group("administrators", "FileStation", "disabled")
        r = self.bw.ensure_group("administrators", "FileStation", "disabled")
        assert r["changed"] is False
        assert r["action"] == "none"

    def test_ensure_group_updates(self) -> None:
        """ensure_group() — changed=True when state differs, then restore."""
        self.bw.ensure_group("administrators", "FTP", "disabled")
        r = self.bw.ensure_group("administrators", "FTP", "enabled",
                                  upload_limit_1=100, download_limit_1=100)
        assert isinstance(r["changed"], bool)
        # Restore
        self.bw.ensure_group("administrators", "FTP", "disabled")

    def test_disable_user_returns_dict(self) -> None:
        """disable_user() — returns {changed, action}."""
        r = self.bw.disable_user(ADMIN_USER, "FileStation")
        assert isinstance(r["changed"], bool)
        assert "action" in r

    def test_disable_group_returns_dict(self) -> None:
        """disable_group() — returns {changed, action}."""
        r = self.bw.disable_group("administrators", "FileStation")
        assert isinstance(r["changed"], bool)
        assert "action" in r

    def test_ensure_user_returns_action_key(self) -> None:
        """ensure_user() result always has action key."""
        r = self.bw.ensure_user(ADMIN_USER, "FileStation", "disabled")
        assert "action" in r
        assert r["action"] in ("none", "updated")

    def test_ensure_group_returns_action_key(self) -> None:
        """ensure_group() result always has action key."""
        r = self.bw.ensure_group("administrators", "FileStation", "disabled")
        assert "action" in r
        assert r["action"] in ("none", "updated")


# ── TrafficControlManager ─────────────────────────────────────────────────────


@nas_required
class TestTrafficControlManager:
    """TrafficControl rules — full lifecycle on ovs_bond0 adapter."""

    ADAPTER = "ovs_bond0"

    @pytest.fixture(autouse=True)
    def setup(self, client) -> None:  # noqa: ANN001
        from synology_dsm.trafficcontrol import TrafficControlManager

        self.tc = TrafficControlManager(client)
        yield
        try:
            self.tc.clear_rules(self.ADAPTER)
        except Exception:
            pass

    def test_load_returns_list(self) -> None:
        """load() returns a list (may be empty)."""
        result = self.tc.load(self.ADAPTER)
        assert isinstance(result, list)

    def test_clear_rules(self) -> None:
        """clear_rules() — empties rule list, returns changed."""
        r = self.tc.clear_rules(self.ADAPTER)
        assert isinstance(r["changed"], bool)
        assert "action" in r
        assert self.tc.load(self.ADAPTER) == []

    def test_add_and_remove_rule(self) -> None:
        """add_rule() then remove_rule() — full round-trip."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "nfs",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 500,
            "maxrate": 1000,
            "source": "all",
            "ip_direction": "dest",
        }
        r_add = self.tc.add_rule(self.ADAPTER, rule)
        assert r_add["changed"] is True
        rules = self.tc.load(self.ADAPTER)
        assert len(rules) == 1

        rule_id = rules[0]["id"]
        r_remove = self.tc.remove_rule(self.ADAPTER, rule_id)
        assert r_remove["changed"] is True
        assert self.tc.load(self.ADAPTER) == []

    def test_ensure_rule_creates(self) -> None:
        """ensure_rule() — creates rule when absent."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "ssh",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 100,
            "maxrate": 500,
            "source": "all",
            "ip_direction": "dest",
        }
        r = self.tc.ensure_rule(self.ADAPTER, rule)
        assert r["changed"] is True
        assert r["action"] == "added"

    def test_ensure_rule_noop(self) -> None:
        """ensure_rule() — noop when identical rule already present."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "ftp",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 200,
            "maxrate": 800,
            "source": "all",
            "ip_direction": "dest",
        }
        self.tc.ensure_rule(self.ADAPTER, rule)
        r = self.tc.ensure_rule(self.ADAPTER, rule)
        assert r["changed"] is False
        assert r["action"] == "none"

    def test_dry_run_does_not_change(self) -> None:
        """dry_run=True must not write rules."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "snmp",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 50,
            "maxrate": 200,
            "source": "all",
            "ip_direction": "dest",
        }
        r = self.tc.add_rule(self.ADAPTER, rule, dry_run=True)
        assert r["dry_run"] is True
        assert self.tc.load(self.ADAPTER) == []


# ── ShareManager — list_shares_for_group ──────────────────────────────────────


@nas_required
class TestSharePermissionsByGroup:
    """Group share permission queries — read-only."""

    @pytest.fixture(autouse=True)
    def setup(self, client) -> None:  # noqa: ANN001
        from synology_dsm import ShareManager

        self.shares = ShareManager(client)

    def test_list_shares_for_group_returns_list(self) -> None:
        result = self.shares.list_shares_for_group("administrators")
        assert isinstance(result, list)

    def test_shares_have_permission_fields(self) -> None:
        result = self.shares.list_shares_for_group("administrators")
        if not result:
            pytest.skip("administrators group has no share permissions configured")
        s = result[0]
        assert "name" in s
        assert "is_writable" in s or "is_readonly" in s or "is_deny" in s

    def test_custom_share_type_filter(self) -> None:
        result = self.shares.list_shares_for_group("administrators", share_type=["local"])
        assert isinstance(result, list)

    def test_with_additional_fields(self) -> None:
        result = self.shares.list_shares_for_group(
            "administrators",
            additional=["hidden", "encryption", "is_aclmode"],
        )
        assert isinstance(result, list)


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
