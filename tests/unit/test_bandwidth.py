"""Unit tests — BandwidthManager."""

import pytest

from synology_dsm.bandwidth import BandwidthManager


def _mgr(mock_client):
    return BandwidthManager(mock_client)


_BW_RESPONSE = {
    "upload_limit": 0,
    "download_limit": 10240,
    "protocol_list": [
        {"protocol": "smb", "upload_limit": 0, "download_limit": 10240},
        {"protocol": "ftp", "upload_limit": 0, "download_limit": 5120},
    ],
}


class TestGetGroupLimit:
    def test_returns_limit_dict(self, mock_client):
        mock_client.request.return_value = _BW_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.get_group_limit("administrators")
        assert result["upload_limit"] == 0
        assert result["download_limit"] == 10240

    def test_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_group_limit("svc-automation")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.BandwidthControl"
        assert call.args[1] == "get"

    def test_version_2_required(self, mock_client):
        """version=2 is required — version=1 returns error 102 on DSM 7.x."""
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_group_limit("administrators")
        call = mock_client.request.call_args
        assert call.kwargs.get("version") == 2

    def test_owner_type_is_local_group(self, mock_client):
        """owner_type must be 'local_group' — matches DevTools payload."""
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_group_limit("administrators")
        call = mock_client.request.call_args
        assert call.kwargs.get("owner_type") == "local_group"
        assert call.kwargs.get("name") == "administrators"

    def test_protocol_list_returned(self, mock_client):
        mock_client.request.return_value = _BW_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.get_group_limit("svc-automation")
        assert len(result["protocol_list"]) == 2
        assert result["protocol_list"][0]["protocol"] == "smb"


class TestGetUserLimit:
    def test_owner_type_is_local_user(self, mock_client):
        """owner_type must be 'local_user' for user queries."""
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_user_limit("alice")
        call = mock_client.request.call_args
        assert call.kwargs.get("owner_type") == "local_user"
        assert call.kwargs.get("name") == "alice"

    def test_returns_limit_dict(self, mock_client):
        mock_client.request.return_value = {"upload_limit": 2048, "download_limit": 0}
        mgr = _mgr(mock_client)
        result = mgr.get_user_limit("alice")
        assert result["upload_limit"] == 2048
        assert result["download_limit"] == 0  # 0 = unlimited


class TestGetLimit:
    def test_local_group_owner_type(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_limit("devops", "local_group")
        call = mock_client.request.call_args
        assert call.kwargs.get("owner_type") == "local_group"

    def test_local_user_owner_type(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.get_limit("alice", "local_user")
        call = mock_client.request.call_args
        assert call.kwargs.get("owner_type") == "local_user"

    def test_invalid_owner_type_raises(self, mock_client):
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid owner_type"):
            mgr.get_limit("alice", "domain_user")
