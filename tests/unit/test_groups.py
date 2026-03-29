"""Unit tests — GroupManager."""

import json

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
        # list() + get() both return the same description — noop
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"groups": [{"name": "devops", "description": "DevOps group"}]}
        )
        mgr = _mgr(mock_client)
        result = mgr.ensure("devops", state="present", description="DevOps group")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_present_updates_when_diff(self, mock_client):
        # list() returns group; get() returns accurate description
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"groups": [{"name": "devops", "description": "old"}]}
            if method in ("list", "get")
            else {}
        )
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


class TestGroupDelete:
    def test_delete_calls_api(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.delete("old-group")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Group"
        assert call.args[1] == "delete"

    def test_delete_dry_run(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.delete("old-group", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_delete"
        mock_client.request.assert_not_called()


class TestGroupGet:
    def test_get_returns_first_match(self, mock_client):
        mock_client.request.return_value = {
            "groups": [{"name": "devops", "gid": 1001, "description": "DevOps"}]
        }
        mgr = _mgr(mock_client)
        group = mgr.get("devops")
        assert group["name"] == "devops"
        assert group["gid"] == 1001

    def test_get_returns_empty_dict_when_not_found(self, mock_client):
        mock_client.request.return_value = {"groups": []}
        mgr = _mgr(mock_client)
        group = mgr.get("ghost")
        assert group == {}


class TestGroupListMembers:
    def test_list_members_via_member_list(self, mock_client):
        mock_client.request.return_value = {"users": [{"name": "alice"}, {"name": "bob"}]}
        mgr = _mgr(mock_client)
        members = mgr.list_members("devops")
        assert len(members) == 2

    def test_list_members_fallback_to_get(self, mock_client):
        """Falls back to SYNO.Core.Group.get when member_list raises RuntimeError."""

        def side_effect(api, method, **kw):
            if method == "member_list":
                raise RuntimeError("API error [SYNO.Core.Group.member_list]: 102")
            return {"members": [{"name": "fallback-user"}]}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        members = mgr.list_members("devops")
        assert any(
            m.get("name") == "fallback-user" if isinstance(m, dict) else m == "fallback-user"
            for m in members
        )


class TestRemoveMember:
    def test_remove_member_calls_set_without_user(self, mock_client):
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"users": [{"name": "alice"}, {"name": "bob"}]} if method == "member_list" else {}
        )
        mgr = _mgr(mock_client)
        result = mgr.remove_member("devops", "alice")
        assert result["changed"] is True
        assert result["action"] == "removed"
        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        assert len(set_calls) == 1
        members_arg = json.loads(set_calls[0].kwargs["members"])
        assert "alice" not in members_arg
        assert "bob" in members_arg

    def test_remove_member_noop_when_not_in_group(self, mock_client):
        """remove_member returns noop without calling set when user not in group."""
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"users": [{"name": "bob"}]} if method == "member_list" else {}
        )
        mgr = _mgr(mock_client)
        result = mgr.remove_member("devops", "alice")
        assert result["changed"] is False
        assert result["action"] == "noop"
        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        assert len(set_calls) == 0  # no write when user not present


class TestListMembersFallbackChain:
    def test_list_members_returns_empty_when_both_apis_fail(self, mock_client):
        """Both member_list and get fail — list_members returns [] safely."""
        mock_client.request.side_effect = Exception("network error")
        mgr = _mgr(mock_client)
        result = mgr.list_members("devops")
        assert result == []


class TestRemoveMemberFallback:
    def test_remove_member_applies_unconditionally_when_list_unavailable(self, mock_client):
        """When member_list returns nothing, remove_member always applies and warns."""
        mock_client.request.side_effect = lambda api, method, **kw: {}
        mgr = _mgr(mock_client)
        result = mgr.remove_member("devops", "alice")
        assert result["changed"] is True
        assert result["action"] == "removed"
        assert "warning" in result
        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        assert len(set_calls) == 1


class TestGroupEnsureDryRunUpdate:
    def test_ensure_dry_run_would_update(self, mock_client):
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"groups": [{"name": "devops", "description": "old"}]}
            if method in ("list", "get")
            else {}
        )
        mgr = _mgr(mock_client)
        result = mgr.ensure("devops", state="present", description="new", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_update"

    def test_ensure_dry_run_would_delete(self, mock_client):
        mock_client.request.return_value = {"groups": [{"name": "devops", "description": ""}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("devops", state="absent", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_delete"

    def test_ensure_invalid_state_raises(self, mock_client):
        mock_client.request.return_value = {"groups": []}
        mgr = _mgr(mock_client)
        import pytest

        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("devops", state="broken")


class TestAddMember:
    def test_add_member_fetches_and_appends(self, mock_client):
        """add_member fetches current members then calls set with merged list."""

        def side_effect(api, method, **kw):
            if method == "member_list":
                return {"users": [{"name": "existing"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.add_member("devops", "newuser")
        assert result["changed"] is True
        assert result["action"] == "added"

        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        assert len(set_calls) == 1
        members_arg = json.loads(set_calls[0].kwargs["members"])
        assert "existing" in members_arg
        assert "newuser" in members_arg

    def test_add_member_idempotent(self, mock_client):
        """add_member returns noop without calling set when user already in group (list readable)."""
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"users": [{"name": "alice"}]} if method == "member_list" else {}
        )
        mgr = _mgr(mock_client)
        result = mgr.add_member("devops", "alice")
        assert result["changed"] is False
        assert result["action"] == "noop"
        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        assert len(set_calls) == 0  # no write when already member

    def test_add_member_applies_unconditionally_when_list_unavailable(self, mock_client):
        """When member_list and get both fail, add_member always applies and warns."""
        mock_client.request.side_effect = lambda api, method, **kw: (
            {} if method in ("member_list", "get") else {}
        )
        # member_list returns {} → users=[] → list_members returns []
        mock_client.request.side_effect = lambda api, method, **kw: {}
        mgr = _mgr(mock_client)
        result = mgr.add_member("devops", "alice")
        assert result["changed"] is True
        assert result["action"] == "added"
        assert "warning" in result
        set_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "set"]
        assert len(set_calls) == 1
