"""Unit tests — BandwidthManager."""

import json

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

_BW_GET_RESPONSE = {
    "bandwidths": [
        {
            "name": "alice",
            "owner_type": "local_user",
            "protocol": "FileStation",
            "policy": "enabled",
            "upload_limit_1": 1000,
            "download_limit_1": 10000,
            "upload_limit_2": 0,
            "download_limit_2": 0,
            "schedule_plan": "1" * 168,
        },
        {
            "name": "alice",
            "owner_type": "local_user",
            "protocol": "FTP",
            "policy": "disabled",
            "upload_limit_1": 0,
            "download_limit_1": 0,
            "upload_limit_2": 0,
            "download_limit_2": 0,
            "schedule_plan": "1" * 168,
        },
    ]
}


# ------------------------------------------------------------------
# get_group_limit / get_user_limit / get_limit (legacy read methods)
# ------------------------------------------------------------------


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


# ------------------------------------------------------------------
# get (new — returns per-protocol bandwidth list)
# ------------------------------------------------------------------


class TestGet:
    def test_returns_bandwidths_list(self, mock_client):
        mock_client.request.return_value = _BW_GET_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.get("alice", "local_user")
        assert len(result) == 2
        assert result[0]["protocol"] == "FileStation"

    def test_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"bandwidths": []}
        mgr = _mgr(mock_client)
        mgr.get("devops", "local_group")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.BandwidthControl"
        assert call.args[1] == "get"
        assert call.kwargs["version"] == 2
        assert call.kwargs["name"] == "devops"
        assert call.kwargs["owner_type"] == "local_group"

    def test_empty_response_returns_empty_list(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.get("alice", "local_user")
        assert result == []

    def test_invalid_owner_type_raises(self, mock_client):
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid owner_type"):
            mgr.get("alice", "bad_type")


# ------------------------------------------------------------------
# set
# ------------------------------------------------------------------


class TestSet:
    def test_calls_api_with_json_bandwidths(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        bw_list = [{"name": "alice", "protocol": "FileStation", "policy": "enabled"}]
        mgr.set("alice", "local_user", bw_list)
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.BandwidthControl"
        assert call.args[1] == "set"
        assert call.kwargs["version"] == 1
        assert json.loads(call.kwargs["bandwidths"]) == bw_list

    def test_returns_changed_true(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.set("alice", "local_user", [])
        assert result["changed"] is True
        assert result["action"] == "set"

    def test_dry_run_skips_api(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.set("alice", "local_user", [], dry_run=True)
        mock_client.request.assert_not_called()
        assert result["changed"] is True
        assert result["dry_run"] is True

    def test_invalid_owner_type_raises(self, mock_client):
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid owner_type"):
            mgr.set("alice", "bad_type", [])


# ------------------------------------------------------------------
# set_user / set_group
# ------------------------------------------------------------------


class TestSetUser:
    def test_calls_set_with_correct_owner_type(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.set_user("alice", "FileStation", policy="enabled", upload_limit_1=500)
        call = mock_client.request.call_args
        assert call.args[1] == "set"
        bw = json.loads(call.kwargs["bandwidths"])
        assert bw[0]["owner_type"] == "local_user"
        assert bw[0]["name"] == "alice"
        assert bw[0]["protocol"] == "FileStation"
        assert bw[0]["policy"] == "enabled"
        assert bw[0]["upload_limit_1"] == 500

    def test_invalid_policy_raises(self, mock_client):
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid policy"):
            mgr.set_user("alice", "FileStation", policy="turbo")

    def test_dry_run_skips_api(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.set_user("alice", "FileStation", dry_run=True)
        mock_client.request.assert_not_called()
        assert result["dry_run"] is True


class TestSetGroup:
    def test_calls_set_with_correct_owner_type(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.set_group("devops", "FTP", policy="enabled", download_limit_1=2000)
        call = mock_client.request.call_args
        bw = json.loads(call.kwargs["bandwidths"])
        assert bw[0]["owner_type"] == "local_group"
        assert bw[0]["name"] == "devops"
        assert bw[0]["protocol"] == "FTP"
        assert bw[0]["download_limit_1"] == 2000


# ------------------------------------------------------------------
# ensure_user / ensure_group
# ------------------------------------------------------------------


class TestEnsureUser:
    def test_no_change_when_same(self, mock_client):
        """When current state matches desired, return changed=False."""
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "alice",
                    "owner_type": "local_user",
                    "protocol": "FileStation",
                    "policy": "enabled",
                    "upload_limit_1": 1000,
                    "download_limit_1": 5000,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.ensure_user(
            "alice",
            "FileStation",
            policy="enabled",
            upload_limit_1=1000,
            download_limit_1=5000,
        )
        assert result["changed"] is False
        assert result["action"] == "none"
        # Only the get call should have been made, not set
        assert mock_client.request.call_count == 1

    def test_changed_when_different(self, mock_client):
        """When current state differs, return changed=True and call set."""
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "alice",
                    "owner_type": "local_user",
                    "protocol": "FileStation",
                    "policy": "enabled",
                    "upload_limit_1": 500,
                    "download_limit_1": 2000,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.ensure_user(
            "alice",
            "FileStation",
            policy="enabled",
            upload_limit_1=1000,
            download_limit_1=5000,
        )
        assert result["changed"] is True
        assert result["action"] == "updated"
        # get + set = 2 calls
        assert mock_client.request.call_count == 2

    def test_changed_when_no_existing_entry(self, mock_client):
        """When protocol has no existing entry, return changed=True."""
        mock_client.request.return_value = {"bandwidths": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure_user("alice", "FileStation", policy="enabled")
        assert result["changed"] is True
        assert result["action"] == "updated"

    def test_dry_run_never_calls_write(self, mock_client):
        """dry_run=True must not call the set API even when change is needed."""
        mock_client.request.return_value = {"bandwidths": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure_user("alice", "FileStation", policy="enabled", dry_run=True)
        assert result["changed"] is True
        assert result["dry_run"] is True
        # Only the get call
        assert mock_client.request.call_count == 1
        # Verify the single call was a "get", not "set"
        assert mock_client.request.call_args.args[1] == "get"

    def test_dry_run_no_change_includes_flag(self, mock_client):
        """dry_run result includes dry_run=True even when no change needed."""
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "alice",
                    "owner_type": "local_user",
                    "protocol": "FileStation",
                    "policy": "disabled",
                    "upload_limit_1": 0,
                    "download_limit_1": 0,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.ensure_user("alice", "FileStation", policy="disabled", dry_run=True)
        assert result["changed"] is False
        assert result["dry_run"] is True

    def test_invalid_policy_raises(self, mock_client):
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid policy"):
            mgr.ensure_user("alice", "FileStation", policy="turbo")


class TestEnsureGroup:
    def test_no_change_when_same(self, mock_client):
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "devops",
                    "owner_type": "local_group",
                    "protocol": "FTP",
                    "policy": "enabled",
                    "upload_limit_1": 0,
                    "download_limit_1": 3000,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.ensure_group("devops", "FTP", policy="enabled", download_limit_1=3000)
        assert result["changed"] is False
        assert result["action"] == "none"

    def test_changed_when_different(self, mock_client):
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "devops",
                    "owner_type": "local_group",
                    "protocol": "FTP",
                    "policy": "disabled",
                    "upload_limit_1": 0,
                    "download_limit_1": 0,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.ensure_group("devops", "FTP", policy="enabled", download_limit_1=5000)
        assert result["changed"] is True
        assert result["action"] == "updated"


# ------------------------------------------------------------------
# disable_user / disable_group
# ------------------------------------------------------------------


class TestDisableUser:
    def test_sets_policy_disabled(self, mock_client):
        """disable_user should ensure policy='disabled'."""
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "alice",
                    "owner_type": "local_user",
                    "protocol": "FileStation",
                    "policy": "enabled",
                    "upload_limit_1": 1000,
                    "download_limit_1": 5000,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.disable_user("alice", "FileStation")
        assert result["changed"] is True
        assert result["action"] == "updated"

    def test_no_change_when_already_disabled(self, mock_client):
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "alice",
                    "owner_type": "local_user",
                    "protocol": "FileStation",
                    "policy": "disabled",
                    "upload_limit_1": 0,
                    "download_limit_1": 0,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.disable_user("alice", "FileStation")
        assert result["changed"] is False
        assert result["action"] == "none"

    def test_dry_run(self, mock_client):
        mock_client.request.return_value = {"bandwidths": []}
        mgr = _mgr(mock_client)
        result = mgr.disable_user("alice", "FileStation", dry_run=True)
        assert result["dry_run"] is True


class TestDisableGroup:
    def test_sets_policy_disabled(self, mock_client):
        mock_client.request.return_value = {
            "bandwidths": [
                {
                    "name": "devops",
                    "owner_type": "local_group",
                    "protocol": "NFS",
                    "policy": "enabled",
                    "upload_limit_1": 500,
                    "download_limit_1": 1000,
                    "upload_limit_2": 0,
                    "download_limit_2": 0,
                    "schedule_plan": "1" * 168,
                }
            ]
        }
        mgr = _mgr(mock_client)
        result = mgr.disable_group("devops", "NFS")
        assert result["changed"] is True
