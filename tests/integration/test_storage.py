"""Live NAS integration tests — StorageManager."""

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
