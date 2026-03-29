"""Unit tests — ShareManager.list_shares_for_group."""

import json

from synology_dsm.shares import ShareManager


def _mgr(mock_client):
    return ShareManager(mock_client)


_SHARES_RESPONSE = {
    "shares": [
        {"name": "by-data", "is_writable": True, "is_readonly": False, "is_deny": False},
        {"name": "by-backup", "is_writable": False, "is_readonly": True, "is_deny": False},
        {"name": "by-private", "is_writable": False, "is_readonly": False, "is_deny": True},
    ]
}


class TestListSharesForGroup:
    def test_returns_share_list(self, mock_client):
        mock_client.request.return_value = _SHARES_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.list_shares_for_group("administrators")
        assert len(result) == 3
        assert result[0]["name"] == "by-data"

    def test_returns_empty_when_no_shares(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        result = mgr.list_shares_for_group("no-shares-group")
        assert result == []

    def test_returns_empty_on_missing_key(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.list_shares_for_group("administrators")
        assert result == []

    def test_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list_shares_for_group("svc-automation")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Share.Permission"
        assert call.args[1] == "list_by_group"
        assert call.kwargs.get("version") == 1

    def test_user_group_type_is_local_group(self, mock_client):
        """user_group_type must be 'local_group' — matches DevTools payload."""
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list_shares_for_group("administrators")
        call = mock_client.request.call_args
        assert call.kwargs.get("user_group_type") == "local_group"
        assert call.kwargs.get("name") == "administrators"

    def test_default_share_type_covers_all_types(self, mock_client):
        """Default share_type matches the full list observed in DevTools Image 3."""
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list_shares_for_group("administrators")
        call = mock_client.request.call_args
        share_type = json.loads(call.kwargs["share_type"])
        assert "local" in share_type
        assert "usb" in share_type
        assert "cold_storage" in share_type

    def test_custom_share_type_subset(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list_shares_for_group("administrators", share_type=["local"])
        call = mock_client.request.call_args
        share_type = json.loads(call.kwargs["share_type"])
        assert share_type == ["local"]

    def test_additional_fields_sent_when_provided(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list_shares_for_group("administrators", additional=["hidden", "encryption"])
        call = mock_client.request.call_args
        additional = json.loads(call.kwargs["additional"])
        assert "hidden" in additional
        assert "encryption" in additional

    def test_no_additional_param_when_not_provided(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        mgr.list_shares_for_group("administrators")
        call = mock_client.request.call_args
        assert "additional" not in call.kwargs

    def test_permission_flags_accessible(self, mock_client):
        mock_client.request.return_value = _SHARES_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.list_shares_for_group("administrators")
        rw_share = next(s for s in result if s["name"] == "by-data")
        ro_share = next(s for s in result if s["name"] == "by-backup")
        deny_share = next(s for s in result if s["name"] == "by-private")
        assert rw_share["is_writable"] is True
        assert ro_share["is_readonly"] is True
        assert deny_share["is_deny"] is True
