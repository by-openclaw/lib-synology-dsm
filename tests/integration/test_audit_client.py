"""Live NAS integration tests — audit client (svc-opus, read-only).

DSM 7.1.x permission model:
  - SYNO.Core.* APIs (User, Group, Share) require ``administrators`` group
    → NOT accessible to svc-opus
  - SYNO.FileStation.* APIs accessible to any user with File Station = Allow
  - Non-admin users get error 105 ("session does not have permission") on Core APIs

This test suite verifies:
  1. FileStation read ops succeed (only APIs available to non-admin)
  2. FileStation write ops blocked (no write permission on shares)
  3. Core API calls fail with DSMSessionError(105) — correctly blocked
  4. Audit client session is valid

Uses ``audit_client`` fixture from conftest.py (svc-opus, session="").
"""

from __future__ import annotations

import pytest

from synology_dsm.exceptions import DSMAPIError, DSMError, DSMPermissionError, DSMSessionError
from synology_dsm.filestation import FileStationManager
from synology_dsm.groups import GroupManager
from synology_dsm.shares import ShareManager
from synology_dsm.users import UserManager

pytestmark = pytest.mark.integration


# ── FileStation read ops — should succeed ────────────────────────────────────


class TestAuditFileStationRead:
    """svc-opus (users group) can read FileStation resources."""

    def test_list_shares(self, audit_client) -> None:  # noqa: ANN001
        """Auditor can list FileStation shares."""
        mgr = FileStationManager(audit_client)
        shares = mgr.list_shares()
        assert isinstance(shares, list)
        assert len(shares) > 0

    def test_list_folder(self, audit_client) -> None:  # noqa: ANN001
        """Auditor can list contents of a share."""
        mgr = FileStationManager(audit_client)
        shares = mgr.list_shares()
        if not shares:
            pytest.skip("No shares accessible to svc-opus")
        first_share = shares[0]["path"]
        files = mgr.list(first_share)
        assert isinstance(files, list)


# ── FileStation write ops — should be blocked ────────────────────────────────


class TestAuditFileStationWriteBlocked:
    """svc-opus cannot perform FileStation write operations."""

    def test_cannot_mkdir(self, audit_client) -> None:  # noqa: ANN001
        """Auditor cannot create a folder (error 407 = operation not permitted)."""
        mgr = FileStationManager(audit_client)
        with pytest.raises((DSMPermissionError, DSMAPIError, DSMError, RuntimeError)):
            mgr.mkdir("/by-terraform-state", "audit-block-folder")

    def test_cannot_upload(self, audit_client) -> None:  # noqa: ANN001
        """Auditor cannot upload a file."""
        mgr = FileStationManager(audit_client)
        with pytest.raises((DSMPermissionError, DSMAPIError, DSMError, RuntimeError)):
            mgr.upload(
                local_path="/dev/null",
                dest_folder="/by-terraform-state",
                overwrite=False,
            )


# ── Core APIs — blocked for non-admin (error 105) ───────────────────────────


class TestAuditCoreAPIsBlocked:
    """SYNO.Core.* APIs require administrators group.

    svc-opus (users group) gets error 105 on all Core API calls.
    This is a DSM design constraint, not a lib bug.
    """

    def test_core_user_list_blocked(self, audit_client) -> None:  # noqa: ANN001
        """Core.User.list requires admin — auditor gets error 105."""
        mgr = UserManager(audit_client)
        with pytest.raises(DSMSessionError) as exc_info:
            mgr.list()
        assert exc_info.value.code == 105

    def test_core_group_list_blocked(self, audit_client) -> None:  # noqa: ANN001
        """Core.Group.list requires admin — auditor gets error 105."""
        mgr = GroupManager(audit_client)
        with pytest.raises(DSMSessionError) as exc_info:
            mgr.list()
        assert exc_info.value.code == 105

    def test_core_share_list_blocked(self, audit_client) -> None:  # noqa: ANN001
        """Core.Share.list requires admin — auditor gets error 105."""
        mgr = ShareManager(audit_client)
        with pytest.raises(DSMSessionError) as exc_info:
            mgr.list()
        assert exc_info.value.code == 105

    def test_core_user_ensure_blocked(self, audit_client) -> None:  # noqa: ANN001
        """Core.User ensure() requires admin — auditor gets error 105."""
        mgr = UserManager(audit_client)
        with pytest.raises(DSMSessionError) as exc_info:
            mgr.ensure("svc-opus", state="present")
        assert exc_info.value.code == 105

    def test_core_group_ensure_blocked(self, audit_client) -> None:  # noqa: ANN001
        """Core.Group ensure() requires admin — auditor gets error 105."""
        mgr = GroupManager(audit_client)
        with pytest.raises(DSMSessionError) as exc_info:
            mgr.ensure("users", state="present")
        assert exc_info.value.code == 105


# ── Client properties — verify audit session ─────────────────────────────────


class TestAuditClientProperties:
    """Verify the audit client session is valid."""

    def test_authenticated(self, audit_client) -> None:  # noqa: ANN001
        """Audit client has a valid session."""
        assert audit_client._sid is not None
        assert audit_client._sid != ""

    def test_has_synotoken(self, audit_client) -> None:  # noqa: ANN001
        """Audit client received a SynoToken."""
        assert audit_client._synotoken is not None
        assert audit_client._synotoken != ""
