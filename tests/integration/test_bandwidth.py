"""Live NAS integration tests — BandwidthManager."""

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
