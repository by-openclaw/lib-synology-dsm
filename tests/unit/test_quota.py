"""Unit tests — QuotaManager."""

import pytest
from synology_dsm.quota import QuotaManager


def _mgr(mock_client):
    return QuotaManager(mock_client)


_QUOTA_RESPONSE = {
    "quota": 10240,
    "usage": 2048,
    "share_quota": [
        {"share_name": "by-data", "usage": 1024, "quota": 5120},
        {"share_name": "by-backup", "usage": 1024, "quota": 5120},
    ],
}


class TestGetGroupQuota:
    def test_returns_quota_dict(self, mock_client):
        mock_client.request.return_value = _QUOTA_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.get_group_quota("administrators")
        assert result["quota"] == 10240
        assert result["usage"] == 2048

    def test_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_group_quota("svc-automation")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Quota"
        assert call.args[1] == "get"
        assert call.kwargs.get("version") == 1

    def test_subject_type_is_group(self, mock_client):
        """subject_type must be 'group' — matches DevTools payload."""
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_group_quota("administrators")
        call = mock_client.request.call_args
        assert call.kwargs.get("subject_type") == "group"
        assert call.kwargs.get("name") == "administrators"

    def test_support_share_quota_true_by_default(self, mock_client):
        """support_share_quota=true is the default — matches DevTools payload."""
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_group_quota("administrators")
        call = mock_client.request.call_args
        assert call.kwargs.get("support_share_quota") == "true"

    def test_support_share_quota_can_be_disabled(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_group_quota("administrators", support_share_quota=False)
        call = mock_client.request.call_args
        assert call.kwargs.get("support_share_quota") == "false"

    def test_share_quota_breakdown_present(self, mock_client):
        mock_client.request.return_value = _QUOTA_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.get_group_quota("administrators")
        assert len(result["share_quota"]) == 2
        assert result["share_quota"][0]["share_name"] == "by-data"


class TestGetUserQuota:
    def test_calls_correct_api_with_user_subject_type(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_user_quota("alice")
        call = mock_client.request.call_args
        assert call.kwargs.get("subject_type") == "user"
        assert call.kwargs.get("name") == "alice"

    def test_returns_quota_dict(self, mock_client):
        mock_client.request.return_value = {"quota": 0, "usage": 512}
        mgr = _mgr(mock_client)
        result = mgr.get_user_quota("alice")
        assert result["quota"] == 0  # 0 = unlimited
        assert result["usage"] == 512


class TestGetQuota:
    def test_valid_group_subject_type(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_quota("devops", "group")
        call = mock_client.request.call_args
        assert call.kwargs.get("subject_type") == "group"

    def test_valid_user_subject_type(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_quota("alice", "user")
        call = mock_client.request.call_args
        assert call.kwargs.get("subject_type") == "user"

    def test_invalid_subject_type_raises(self, mock_client):
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid subject_type"):
            mgr.get_quota("alice", "robot")


class TestSetQuota:
    def test_set_user_quota(self, mock_client):
        """quota_mb=10240 passed directly to API — no conversion."""
        import json

        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.set_user_quota("alice", "/volume1", 10240)
        assert result == {"changed": True, "action": "set", "quota_mb": 10240, "volume": "/volume1"}
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Quota"
        assert call.args[1] == "set"
        user_quota = json.loads(call.kwargs["user_quota"])
        assert user_quota == [{"volume": "/volume1", "quota": 10240}]

    def test_set_group_quota(self, mock_client):
        """quota_mb=10240 passed directly to API via group_quota key (verified via F12)."""
        import json

        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.set_group_quota("devops", "/volume1", 10240)
        assert result == {"changed": True, "action": "set", "quota_mb": 10240, "volume": "/volume1"}
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Quota"
        assert call.args[1] == "set"
        group_quota = json.loads(call.kwargs["group_quota"])
        assert group_quota == [{"volume": "/volume1", "quota": 10240}]

    def test_set_user_quota_dry_run(self, mock_client):
        """dry_run=True — no API call, dict has dry_run=True."""
        mgr = _mgr(mock_client)
        result = mgr.set_user_quota("alice", "/volume1", 10240, dry_run=True)
        mock_client.request.assert_not_called()
        assert result["dry_run"] is True
        assert result["changed"] is True
        assert result["action"] == "set"


class TestEnsure:
    def test_ensure_present_no_change(self, mock_client):
        """Current quota matches desired (MB) → changed=False, action=none."""
        mock_client.request.return_value = {"quota": 51200, "usage": 0}
        mgr = _mgr(mock_client)
        result = mgr.ensure("alice", "user", "/volume1", quota_mb=51200)
        assert result == {"changed": False, "action": "none"}

    def test_ensure_present_update(self, mock_client):
        """Current quota differs → set called → changed=True, action=updated."""
        mock_client.request.return_value = {"quota": 20480, "usage": 0}
        mgr = _mgr(mock_client)
        result = mgr.ensure("alice", "user", "/volume1", quota_mb=51200)
        assert result["changed"] is True
        assert result["action"] == "updated"
        # set_user_quota must have been called (request called more than once: get + set)
        assert mock_client.request.call_count >= 2

    def test_ensure_present_create(self, mock_client):
        """Current quota is 0 (unset) → set called → changed=True, action=created."""
        mock_client.request.return_value = {"quota": 0, "usage": 0}
        mgr = _mgr(mock_client)
        result = mgr.ensure("alice", "user", "/volume1", quota_mb=51200)
        assert result["changed"] is True
        assert result["action"] == "created"

    def test_ensure_absent_removes(self, mock_client):
        """Current quota > 0 → set to 0 → changed=True, action=removed."""
        mock_client.request.return_value = {"quota": 51200, "usage": 0}
        mgr = _mgr(mock_client)
        result = mgr.ensure("alice", "user", "/volume1", state="absent")
        assert result["changed"] is True
        assert result["action"] == "removed"

    def test_ensure_absent_no_change(self, mock_client):
        """Current quota already 0 → changed=False, action=none."""
        mock_client.request.return_value = {"quota": 0, "usage": 0}
        mgr = _mgr(mock_client)
        result = mgr.ensure("alice", "user", "/volume1", state="absent")
        assert result == {"changed": False, "action": "none"}

    def test_ensure_dry_run(self, mock_client):
        """dry_run=True → no API write, result has dry_run=True."""
        mock_client.request.return_value = {"quota": 0, "usage": 0}
        mgr = _mgr(mock_client)
        result = mgr.ensure("alice", "user", "/volume1", quota_mb=51200, dry_run=True)
        assert result["dry_run"] is True
        assert result["changed"] is True
        assert result["action"] == "created"
        # Only the get call should have happened, not set
        mock_client.request.assert_called_once()

    def test_ensure_invalid_subject_type(self, mock_client):
        """Invalid subject_type raises ValueError."""
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid subject_type"):
            mgr.ensure("alice", "robot", "/volume1", quota_mb=51200)
