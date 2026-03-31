"""Live NAS integration tests — FileStationManager."""

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
FS_BASE_SHARE = os.environ.get("FS_BASE_SHARE", "by-terraform-state")

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
