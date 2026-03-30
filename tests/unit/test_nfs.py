"""Unit tests — NFSManager."""

import json

import pytest

from synology_dsm.nfs import NFSManager


def _mgr(mock_client):
    return NFSManager(mock_client)


class TestGetRules:
    def test_get_rules_returns_rule_list(self, mock_client):
        mock_client.request.return_value = {
            "rule": [{"client": "192.168.1.0/24", "privilege": "rw"}]
        }
        mgr = _mgr(mock_client)
        rules = mgr.get_rules("my-share")
        assert len(rules) == 1
        assert rules[0]["privilege"] == "rw"

    def test_get_rules_empty_when_no_rules(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        rules = mgr.get_rules("my-share")
        assert rules == []

    def test_get_rules_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"rule": []}
        mgr = _mgr(mock_client)
        mgr.get_rules("test-share")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.FileServ.NFS.SharePrivilege"
        assert call.args[1] == "load"
        assert call.kwargs.get("share_name") == "test-share"


class TestSetRules:
    def test_set_rules_calls_save(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        rules = [{"client": "10.0.0.0/8", "privilege": "rw"}]
        result = mgr.set_rules("my-share", rules)
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.FileServ.NFS.SharePrivilege"
        assert call.args[1] == "save"
        assert result["changed"] is True
        assert result["action"] == "rules_set"

    def test_set_rules_dry_run(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.set_rules("my-share", [], dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_set_rules"
        mock_client.request.assert_not_called()

    def test_set_rules_passes_json_encoded_rules(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        rules = [{"client": "10.0.0.1", "privilege": "ro"}]
        mgr.set_rules("my-share", rules)
        call = mock_client.request.call_args
        rule_arg = json.loads(call.kwargs["rule"])
        assert rule_arg[0]["client"] == "10.0.0.1"


class TestEnsurePresent:
    def test_ensure_creates_when_no_rules(self, mock_client):
        mock_client.request.return_value = {"rule": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "192.168.1.0/24", state="present", rw=True)
        assert result["changed"] is True
        assert result["action"] == "created"
        save_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "save"]
        assert len(save_calls) == 1

    def test_ensure_noop_when_rule_matches(self, mock_client):
        existing_rule = {
            "client": "192.168.1.0/24",
            "privilege": "rw",
            "root_squash": "root",
            "async": True,
        }
        mock_client.request.return_value = {"rule": [existing_rule]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "192.168.1.0/24", state="present", rw=True)
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_updates_when_privilege_differs(self, mock_client):
        existing_rule = {
            "client": "192.168.1.0/24",
            "privilege": "ro",
            "root_squash": "root",
            "async": True,
        }
        mock_client.request.return_value = {"rule": [existing_rule]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "192.168.1.0/24", state="present", rw=True)
        assert result["changed"] is True
        assert result["action"] == "updated"
        assert result["after"]["privilege"] == "rw"

    def test_ensure_dry_run_would_create(self, mock_client):
        mock_client.request.return_value = {"rule": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "10.0.0.1", state="present", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_create"
        save_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "save"]
        assert len(save_calls) == 0

    def test_ensure_dry_run_would_update(self, mock_client):
        existing_rule = {
            "client": "10.0.0.1",
            "privilege": "ro",
            "root_squash": "root",
            "async": True,
        }
        mock_client.request.return_value = {"rule": [existing_rule]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "10.0.0.1", state="present", rw=True, dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_update"

    def test_ensure_rw_false_sets_ro(self, mock_client):
        mock_client.request.return_value = {"rule": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "10.0.0.1", state="present", rw=False)
        assert result["action"] == "created"
        assert result["after"]["privilege"] == "ro"


class TestEnsureAbsent:
    def test_ensure_absent_removes_rule(self, mock_client):
        existing_rule = {
            "client": "192.168.1.0/24",
            "privilege": "rw",
            "root_squash": "root",
            "async": True,
        }
        mock_client.request.return_value = {"rule": [existing_rule]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "192.168.1.0/24", state="absent")
        assert result["changed"] is True
        assert result["action"] == "deleted"
        save_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "save"]
        assert len(save_calls) == 1

    def test_ensure_absent_noop_when_not_present(self, mock_client):
        mock_client.request.return_value = {"rule": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "10.0.0.1", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_absent_dry_run(self, mock_client):
        existing_rule = {
            "client": "10.0.0.1",
            "privilege": "rw",
            "root_squash": "root",
            "async": True,
        }
        mock_client.request.return_value = {"rule": [existing_rule]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "10.0.0.1", state="absent", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_delete"
        save_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "save"]
        assert len(save_calls) == 0

    def test_ensure_invalid_state_raises(self, mock_client):
        mock_client.request.return_value = {"rule": []}
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("my-share", "10.0.0.1", state="broken")
