"""Unit tests — ShareManager."""

import json
import pytest
from synology_dsm.shares import ShareManager


def _mgr(mock_client):
    return ShareManager(mock_client)


class TestShareCreate:
    def test_create_sends_shareinfo_json(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.create("by-data", volume_path="/volume1", description="Data share")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Share"
        assert call.args[1] == "create"
        shareinfo = json.loads(call.kwargs["shareinfo"])
        assert shareinfo["name"] == "by-data"
        assert shareinfo["vol_path"] == "/volume1"
        assert shareinfo["desc"] == "Data share"
        assert "name_org" in shareinfo


class TestShareList:
    def test_list_returns_shares(self, mock_client):
        mock_client.request.return_value = {"shares": [{"name": "data"}, {"name": "backup"}]}
        mgr = _mgr(mock_client)
        shares = mgr.list()
        assert len(shares) == 2
        assert shares[0]["name"] == "data"

    def test_list_empty(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        assert mgr.list() == []

    def test_list_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list()
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Share"
        assert call.args[1] == "list"

    def test_list_with_additional_fields(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list(additional=["share_quota", "encryption"])
        call = mock_client.request.call_args
        additional = json.loads(call.kwargs["additional"])
        assert "share_quota" in additional


class TestShareEnsure:
    def test_ensure_present_creates_when_absent(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("newshare", state="present")
        assert result["changed"] is True
        assert result["action"] == "created"

    def test_ensure_present_noop_when_same(self, mock_client):
        mock_client.request.return_value = {"shares": [{"name": "data", "desc": "same"}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("data", state="present", description="same")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_present_updates_when_diff(self, mock_client):
        mock_client.request.return_value = {"shares": [{"name": "data", "desc": "old desc"}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("data", state="present", description="new desc")
        assert result["changed"] is True
        assert result["action"] == "updated"

    def test_ensure_absent_deletes(self, mock_client):
        mock_client.request.return_value = {"shares": [{"name": "old", "desc": ""}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("old", state="absent")
        assert result["changed"] is True
        assert result["action"] == "deleted"

    def test_ensure_absent_noop_when_gone(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("ghost", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_dry_run_no_create(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("newshare", state="present", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_create"
        create_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "create"]
        assert len(create_calls) == 0

    def test_ensure_dry_run_absent_no_delete(self, mock_client):
        mock_client.request.return_value = {"shares": [{"name": "old", "desc": ""}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("old", state="absent", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_delete"


class TestShareDelete:
    def test_delete_calls_api(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.delete("old-share")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Share"
        assert call.args[1] == "delete"

    def test_delete_dry_run(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.delete("old-share", dry_run=True)
        assert result.get("dry_run") is True
        mock_client.request.assert_not_called()


class TestShareUpdate:
    def test_update_calls_set_api(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.update("my-share", desc="new description")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Share"
        assert call.args[1] == "set"
        assert call.kwargs.get("name") == "my-share"
        assert call.kwargs.get("desc") == "new description"


class TestShareCreateWithPermissions:
    def test_create_no_optional_permissions(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.create_with_permissions("bare-share")
        assert result["user_permissions"] is None
        assert result["group_permissions"] is None
        assert result["nfs"] is None

    def test_create_with_user_permission(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.create_with_permissions("my-share", owner_user="dsm-user")
        assert result["user_permissions"] is not None
        assert result["group_permissions"] is None
        assert result["nfs"] is None

    def test_create_with_group_permission(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.create_with_permissions("my-share", owner_group="administrators")
        assert result["group_permissions"] is not None
        assert result["user_permissions"] is None

    def test_create_with_nfs_rule(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.create_with_permissions("my-share", nfs_client="192.168.1.0/24")
        assert result["nfs"] is not None

    def test_create_with_all_permissions(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.create_with_permissions(
            "my-share",
            owner_user="dsm-user",
            owner_group="administrators",
            nfs_client="192.168.1.0/24",
            nfs_rw=False,
        )
        assert result["user_permissions"] is not None
        assert result["group_permissions"] is not None
        assert result["nfs"] is not None
