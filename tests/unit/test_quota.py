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
