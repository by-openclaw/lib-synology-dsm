"""Unit tests — TrafficControlManager."""

import json

import pytest

from synology_dsm.trafficcontrol import TrafficControlManager


def _mgr(mock_client):
    return TrafficControlManager(mock_client)


_RULE_NFS_SSH = {
    "id": 0,
    "enabled": True,
    "port_type": "SYS",
    "port_num": "nfs,ssh",
    "port_direction": "src",
    "protocol": "all",
    "minrate": 1000,
    "maxrate": 3000,
    "source": "all",
    "ip_direction": "dest",
}

_RULE_FTP = {
    "id": 1,
    "enabled": True,
    "port_type": "SYS",
    "port_num": "ftp",
    "port_direction": "src",
    "protocol": "tcp",
    "minrate": 0,
    "maxrate": 5000,
    "source": "all",
    "ip_direction": "dest",
}

_LOAD_RESPONSE = {"rules": [_RULE_NFS_SSH, _RULE_FTP], "total": 2}


# ------------------------------------------------------------------
# load
# ------------------------------------------------------------------


class TestLoad:
    def test_returns_rules_list(self, mock_client):
        mock_client.request.return_value = _LOAD_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.load("eth0")
        assert len(result) == 2
        assert result[0]["port_num"] == "nfs,ssh"

    def test_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"rules": []}
        mgr = _mgr(mock_client)
        mgr.load("ovs_eth0")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Network.TrafficControl.Rules"
        assert call.args[1] == "load"
        assert call.kwargs["version"] == 1
        assert call.kwargs["adapter"] == "ovs_eth0"

    def test_empty_response_returns_empty_list(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.load("eth0")
        assert result == []


# ------------------------------------------------------------------
# save
# ------------------------------------------------------------------


class TestSave:
    def test_calls_api_with_json_rules(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        rules = [_RULE_NFS_SSH]
        mgr.save("eth0", rules)
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Network.TrafficControl.Rules"
        assert call.args[1] == "save"
        assert call.kwargs["adapter"] == "eth0"
        assert json.loads(call.kwargs["rules"]) == rules

    def test_returns_changed_true(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.save("eth0", [_RULE_NFS_SSH])
        assert result["changed"] is True
        assert result["action"] == "save"

    def test_dry_run_skips_api(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.save("eth0", [_RULE_NFS_SSH], dry_run=True)
        mock_client.request.assert_not_called()
        assert result["changed"] is True
        assert result["dry_run"] is True


# ------------------------------------------------------------------
# add_rule
# ------------------------------------------------------------------


class TestAddRule:
    def test_loads_then_saves_with_new_rule(self, mock_client):
        mock_client.request.side_effect = [
            {"rules": [_RULE_NFS_SSH]},  # load
            {},  # save
        ]
        mgr = _mgr(mock_client)
        new_rule = {
            "enabled": True,
            "port_type": "CUSTOM",
            "port_num": "8080",
            "port_direction": "src",
            "protocol": "tcp",
            "minrate": 0,
            "maxrate": 1000,
            "source": "all",
            "ip_direction": "dest",
        }
        result = mgr.add_rule("eth0", new_rule)
        assert result["changed"] is True
        assert result["action"] == "added"
        # Verify save was called with 2 rules
        save_call = mock_client.request.call_args_list[1]
        saved_rules = json.loads(save_call.kwargs["rules"])
        assert len(saved_rules) == 2
        assert saved_rules[1]["id"] == 1  # auto-assigned id
        assert saved_rules[1]["port_num"] == "8080"

    def test_dry_run_skips_save(self, mock_client):
        mock_client.request.return_value = {"rules": []}
        mgr = _mgr(mock_client)
        result = mgr.add_rule("eth0", {"port_type": "ALL"}, dry_run=True)
        assert result["dry_run"] is True
        assert result["changed"] is True
        # Only the load call
        assert mock_client.request.call_count == 1

    def test_auto_assigns_next_id(self, mock_client):
        """New rule gets id = max(existing ids) + 1."""
        mock_client.request.side_effect = [
            {"rules": [{"id": 0}, {"id": 3}]},  # load — ids 0, 3
            {},  # save
        ]
        mgr = _mgr(mock_client)
        result = mgr.add_rule("eth0", {"port_type": "ALL"})
        assert result["changed"] is True
        save_call = mock_client.request.call_args_list[1]
        saved_rules = json.loads(save_call.kwargs["rules"])
        assert saved_rules[-1]["id"] == 4


# ------------------------------------------------------------------
# remove_rule
# ------------------------------------------------------------------


class TestRemoveRule:
    def test_loads_then_saves_without_removed_rule(self, mock_client):
        mock_client.request.side_effect = [
            {"rules": [_RULE_NFS_SSH, _RULE_FTP]},  # load
            {},  # save
        ]
        mgr = _mgr(mock_client)
        result = mgr.remove_rule("eth0", rule_id=0)
        assert result["changed"] is True
        assert result["action"] == "removed"
        save_call = mock_client.request.call_args_list[1]
        saved_rules = json.loads(save_call.kwargs["rules"])
        assert len(saved_rules) == 1
        assert saved_rules[0]["id"] == 1  # only FTP rule remains

    def test_no_change_when_id_not_found(self, mock_client):
        mock_client.request.return_value = {"rules": [_RULE_NFS_SSH]}
        mgr = _mgr(mock_client)
        result = mgr.remove_rule("eth0", rule_id=99)
        assert result["changed"] is False
        assert result["action"] == "none"

    def test_dry_run_skips_save(self, mock_client):
        mock_client.request.return_value = {"rules": [_RULE_NFS_SSH]}
        mgr = _mgr(mock_client)
        result = mgr.remove_rule("eth0", rule_id=0, dry_run=True)
        assert result["dry_run"] is True
        assert result["changed"] is True
        # Only the load call, no save
        assert mock_client.request.call_count == 1

    def test_dry_run_no_change_includes_flag(self, mock_client):
        mock_client.request.return_value = {"rules": []}
        mgr = _mgr(mock_client)
        result = mgr.remove_rule("eth0", rule_id=99, dry_run=True)
        assert result["changed"] is False
        assert result["dry_run"] is True


# ------------------------------------------------------------------
# clear_rules
# ------------------------------------------------------------------


class TestClearRules:
    def test_saves_empty_list(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.clear_rules("eth0")
        assert result["changed"] is True
        assert result["action"] == "cleared"
        call = mock_client.request.call_args
        assert json.loads(call.kwargs["rules"]) == []

    def test_dry_run_skips_save(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.clear_rules("eth0", dry_run=True)
        mock_client.request.assert_not_called()
        assert result["dry_run"] is True
        assert result["changed"] is True


# ------------------------------------------------------------------
# ensure_rule
# ------------------------------------------------------------------


class TestEnsureRule:
    def test_no_change_when_identical(self, mock_client):
        """Matching rule with identical fields → changed=False."""
        mock_client.request.return_value = {"rules": [_RULE_NFS_SSH]}
        mgr = _mgr(mock_client)
        result = mgr.ensure_rule("eth0", _RULE_NFS_SSH)
        assert result["changed"] is False
        assert result["action"] == "none"
        # Only the load call
        assert mock_client.request.call_count == 1

    def test_updated_when_different(self, mock_client):
        """Matching rule with different maxrate → changed=True, action=updated."""
        mock_client.request.side_effect = [
            {"rules": [_RULE_NFS_SSH]},  # load
            {},  # save
        ]
        mgr = _mgr(mock_client)
        modified = {**_RULE_NFS_SSH, "maxrate": 9999}
        result = mgr.ensure_rule("eth0", modified)
        assert result["changed"] is True
        assert result["action"] == "updated"
        save_call = mock_client.request.call_args_list[1]
        saved_rules = json.loads(save_call.kwargs["rules"])
        assert saved_rules[0]["maxrate"] == 9999

    def test_added_when_no_match(self, mock_client):
        """No matching rule → changed=True, action=added."""
        mock_client.request.side_effect = [
            {"rules": [_RULE_NFS_SSH]},  # load
            {},  # save
        ]
        mgr = _mgr(mock_client)
        new_rule = {
            "enabled": True,
            "port_type": "CUSTOM",
            "port_num": "443",
            "port_direction": "src",
            "protocol": "tcp",
            "minrate": 0,
            "maxrate": 2000,
            "source": "all",
            "ip_direction": "dest",
        }
        result = mgr.ensure_rule("eth0", new_rule)
        assert result["changed"] is True
        assert result["action"] == "added"
        save_call = mock_client.request.call_args_list[1]
        saved_rules = json.loads(save_call.kwargs["rules"])
        assert len(saved_rules) == 2

    def test_dry_run_no_change(self, mock_client):
        mock_client.request.return_value = {"rules": [_RULE_NFS_SSH]}
        mgr = _mgr(mock_client)
        result = mgr.ensure_rule("eth0", _RULE_NFS_SSH, dry_run=True)
        assert result["changed"] is False
        assert result["dry_run"] is True

    def test_dry_run_with_change_skips_save(self, mock_client):
        mock_client.request.return_value = {"rules": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure_rule("eth0", _RULE_NFS_SSH, dry_run=True)
        assert result["changed"] is True
        assert result["action"] == "added"
        assert result["dry_run"] is True
        # Only the load call
        assert mock_client.request.call_count == 1

    def test_match_uses_port_type_port_num_protocol(self, mock_client):
        """Rules are matched by port_type + port_num + protocol, not id."""
        existing = {**_RULE_NFS_SSH, "id": 5}
        mock_client.request.return_value = {"rules": [existing]}
        mgr = _mgr(mock_client)
        # Same port_type/port_num/protocol, different id
        desired = {**_RULE_NFS_SSH, "id": 99}
        result = mgr.ensure_rule("eth0", desired)
        assert result["changed"] is False
        assert result["action"] == "none"
