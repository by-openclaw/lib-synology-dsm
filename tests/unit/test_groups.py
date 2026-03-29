"""Unit tests — GroupManager."""

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
    def test_list_members_via_group_member_api(self, mock_client):
        """Primary path: SYNO.Core.Group.Member list ingroup=true — offset key required."""
        mock_client.request.return_value = {
            "offset": 0,
            "total": 2,
            "users": [{"name": "alice"}, {"name": "bob"}],
        }
        mgr = _mgr(mock_client)
        members = mgr.list_members("devops")
        assert len(members) == 2
        assert members[0]["name"] == "alice"
        # Confirm primary path used — only 1 API call
        assert mock_client.request.call_count == 1
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Group.Member"
        assert call.args[1] == "list"
        assert call.kwargs.get("ingroup") == "true"

    def test_list_members_primary_path_offset_detection(self, mock_client):
        """Primary path skipped when offset key absent — falls to secondary."""

        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member":
                return {"users": []}  # no offset key → primary skips
            if method == "member_list":
                return {"users": [{"name": "fallback-user"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        members = mgr.list_members("devops")
        assert any(m.get("name") == "fallback-user" for m in members)

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
        # list returns alice+bob (via SYNO.Core.Group.Member list ingroup=true)
        # remove is called via SYNO.Core.Group.Member remove
        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 2, "users": [{"name": "alice"}, {"name": "bob"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.remove_member("devops", "alice")
        assert result["changed"] is True
        assert result["action"] == "removed"
        remove_calls = [
            c
            for c in mock_client.request.call_args_list
            if c.args[0] == "SYNO.Core.Group.Member" and c.args[1] == "remove"
        ]
        assert len(remove_calls) == 1
        assert remove_calls[0].kwargs["name"] == "alice"

    def test_remove_member_noop_when_not_in_group(self, mock_client):
        """remove_member returns noop without calling remove when user not in group."""

        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 1, "users": [{"name": "bob"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.remove_member("devops", "alice")
        assert result["changed"] is False
        assert result["action"] == "noop"
        remove_calls = [
            c
            for c in mock_client.request.call_args_list
            if c.args[0] == "SYNO.Core.Group.Member" and c.args[1] == "remove"
        ]
        assert len(remove_calls) == 0  # no write when user not present


class TestListMembersFallbackChain:
    def test_list_members_returns_empty_when_both_apis_fail(self, mock_client):
        """Both member_list and get fail — list_members returns [] safely."""
        mock_client.request.side_effect = Exception("network error")
        mgr = _mgr(mock_client)
        result = mgr.list_members("devops")
        assert result == []


class TestRemoveMemberFallback:
    def test_remove_member_on_empty_group_is_noop(self, mock_client):
        """remove_member returns noop when group is empty (total=0, users=[])."""

        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 0, "users": []}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.remove_member("devops", "alice")
        assert result["changed"] is False
        assert result["action"] == "noop"


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
    def test_add_member_reads_list_and_calls_add(self, mock_client):
        """add_member reads current members via SYNO.Core.Group.Member list, then calls add."""

        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 1, "users": [{"name": "existing"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.add_member("devops", "newuser")
        assert result["changed"] is True
        assert result["action"] == "added"
        add_calls = [
            c
            for c in mock_client.request.call_args_list
            if c.args[0] == "SYNO.Core.Group.Member" and c.args[1] == "add"
        ]
        assert len(add_calls) == 1
        assert add_calls[0].kwargs["name"] == "newuser"

    def test_add_member_idempotent(self, mock_client):
        """add_member returns noop without calling add when user already in group."""

        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 1, "users": [{"name": "alice"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.add_member("devops", "alice")
        assert result["changed"] is False
        assert result["action"] == "noop"
        add_calls = [
            c
            for c in mock_client.request.call_args_list
            if c.args[0] == "SYNO.Core.Group.Member" and c.args[1] == "add"
        ]
        assert len(add_calls) == 0  # no API write when already member

    def test_add_member_on_empty_group(self, mock_client):
        """add_member on empty group (total=0, users=[]) calls add — not a noop."""

        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 0, "users": []}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.add_member("devops", "alice")
        assert result["changed"] is True
        assert result["action"] == "added"
        assert "warning" not in result
