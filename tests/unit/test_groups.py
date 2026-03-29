"""Unit tests — GroupManager."""

import pytest
import json
from unittest.mock import MagicMock
from synology_dsm.groups import GroupManager


def _mgr(mock_client):
    return GroupManager(mock_client)


class TestGroupEnsure:
    def test_ensure_present_creates_when_absent(self, mock_client):
        mock_client.request.return_value = {"groups": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("devops", state="present", description="DevOps group")
        assert result["changed"] is True
        assert result["action"] == "created"
        create_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "create"]
        assert len(create_calls) == 1

    def test_ensure_present_noop_when_same(self, mock_client):
        mock_client.request.return_value = {"groups": [{"name": "devops", "description": "DevOps group"}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("devops", state="present", description="DevOps group")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_present_updates_when_diff(self, mock_client):
        mock_client.request.return_value = {"groups": [{"name": "devops", "description": "old"}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("devops", state="present", description="new")
        assert result["changed"] is True
        assert result["action"] == "updated"
        assert result["after"]["description"] == "new"

    def test_ensure_absent_deletes(self, mock_client):
        mock_client.request.return_value = {"groups": [{"name": "devops", "description": ""}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("devops", state="absent")
        assert result["changed"] is True
        assert result["action"] == "deleted"

    def test_ensure_absent_noop_when_gone(self, mock_client):
        mock_client.request.return_value = {"groups": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("ghost", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_dry_run_no_create(self, mock_client):
        mock_client.request.return_value = {"groups": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("newgroup", state="present", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_create"
        create_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "create"]
        assert len(create_calls) == 0


class TestAddMember:
    def test_add_member_fetches_and_appends(self, mock_client):
        """add_member fetches current members then calls set with merged list."""
        # list_members falls back to member_list — mock it to return empty
        def side_effect(api, method, **kw):
            if method == "member_list":
                return {"users": [{"name": "existing"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        mgr.add_member("devops", "newuser")

        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        assert len(set_calls) == 1
        members_arg = json.loads(set_calls[0].kwargs["members"])
        assert "existing" in members_arg
        assert "newuser" in members_arg

    def test_add_member_idempotent(self, mock_client):
        """add_member does not duplicate if user already in group."""
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"users": [{"name": "alice"}]} if method == "member_list" else {}
        )
        mgr = _mgr(mock_client)
        mgr.add_member("devops", "alice")
        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        members_arg = json.loads(set_calls[0].kwargs["members"])
        assert members_arg.count("alice") == 1
