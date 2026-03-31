"""Unit tests — SharePermissionManager."""

import json

import pytest

from synology_dsm.share_permissions import SharePermissionManager


def _mgr(mock_client):
    return SharePermissionManager(mock_client)


_USER_ITEMS = [
    {"name": "admin", "is_writable": True, "is_readonly": False, "is_deny": False},
    {"name": "guest", "is_writable": False, "is_readonly": True, "is_deny": False},
    {"name": "blocked", "is_writable": False, "is_readonly": False, "is_deny": True},
    {"name": "nobody", "is_writable": False, "is_readonly": False, "is_deny": False},
]

_GROUP_ITEMS = [
    {"name": "administrators", "is_writable": True, "is_readonly": False, "is_deny": False},
]


def _mock_list_responses(mock_client, user_items=None, group_items=None):
    """Configure mock_client.request to return user then group items for list()."""
    if user_items is None:
        user_items = []
    if group_items is None:
        group_items = []

    def side_effect(*args, **kwargs):
        if kwargs.get("user_group_type") == "local_group":
            return {"items": group_items}
        return {"items": user_items}

    mock_client.request.side_effect = side_effect


class TestList:
    def test_returns_combined_user_and_group_perms(self, mock_client):
        _mock_list_responses(mock_client, _USER_ITEMS, _GROUP_ITEMS)
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        assert len(result) == 5
        names = [p["name"] for p in result]
        assert "admin" in names
        assert "administrators" in names

    def test_user_perm_read_write(self, mock_client):
        _mock_list_responses(mock_client, _USER_ITEMS)
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        admin = next(p for p in result if p["name"] == "admin")
        assert admin["perm"] == "read_write"
        assert admin["is_group"] is False

    def test_user_perm_read_only(self, mock_client):
        _mock_list_responses(mock_client, _USER_ITEMS)
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        guest = next(p for p in result if p["name"] == "guest")
        assert guest["perm"] == "read_only"

    def test_user_perm_deny(self, mock_client):
        _mock_list_responses(mock_client, _USER_ITEMS)
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        blocked = next(p for p in result if p["name"] == "blocked")
        assert blocked["perm"] == "deny"

    def test_user_perm_no_access(self, mock_client):
        _mock_list_responses(mock_client, _USER_ITEMS)
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        nobody = next(p for p in result if p["name"] == "nobody")
        assert nobody["perm"] == "no_access"

    def test_group_perm_is_group_true(self, mock_client):
        _mock_list_responses(mock_client, [], _GROUP_ITEMS)
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        assert len(result) == 1
        assert result[0]["is_group"] is True
        assert result[0]["perm"] == "read_write"

    def test_empty_when_no_items(self, mock_client):
        _mock_list_responses(mock_client, [], [])
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        assert result == []

    def test_empty_on_missing_items_key(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.list("my-share")
        assert result == []

    def test_calls_correct_api_for_users(self, mock_client):
        _mock_list_responses(mock_client)
        mgr = _mgr(mock_client)
        mgr.list("test-share")
        calls = mock_client.request.call_args_list
        user_call = calls[0]
        assert user_call.args[0] == "SYNO.Core.Share.Permission"
        assert user_call.args[1] == "list"
        assert user_call.kwargs.get("name") == "test-share"
        assert user_call.kwargs.get("user_group_type") == "local_user"
        assert user_call.kwargs.get("action") == "load"

    def test_calls_correct_api_for_groups(self, mock_client):
        _mock_list_responses(mock_client)
        mgr = _mgr(mock_client)
        mgr.list("test-share")
        calls = mock_client.request.call_args_list
        group_call = calls[1]
        assert group_call.kwargs.get("user_group_type") == "local_group"


class TestSet:
    def test_set_user_permission(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.set("my-share", "admin", "read_write")
        assert result["changed"] is True
        assert result["action"] == "set"
        assert result["subject"] == "admin"

    def test_set_group_permission(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.set("my-share", "developers", "read_only", is_group=True)
        call = mock_client.request.call_args
        assert call.kwargs.get("user_group_type") == "local_group"

    def test_set_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.set("my-share", "admin", "deny")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Share.Permission"
        assert call.args[1] == "set"
        perms = json.loads(call.kwargs["permissions"])
        assert perms[0]["name"] == "admin"
        assert perms[0]["is_deny"] is True
        assert perms[0]["is_writable"] is False

    def test_set_read_only_flags(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.set("my-share", "user1", "read_only")
        call = mock_client.request.call_args
        perms = json.loads(call.kwargs["permissions"])
        assert perms[0]["is_readonly"] is True
        assert perms[0]["is_writable"] is False
        assert perms[0]["is_deny"] is False

    def test_set_no_access_flags(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.set("my-share", "user1", "no_access")
        call = mock_client.request.call_args
        perms = json.loads(call.kwargs["permissions"])
        assert perms[0]["is_readonly"] is False
        assert perms[0]["is_writable"] is False
        assert perms[0]["is_deny"] is False

    def test_set_dry_run(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.set("my-share", "admin", "read_write", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_set"
        assert result["perm"] == "read_write"
        mock_client.request.assert_not_called()


class TestSetBulk:
    def test_set_bulk_users_only(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        perms = [
            {"name": "admin", "is_group": False, "perm": "read_write"},
            {"name": "guest", "is_group": False, "perm": "read_only"},
        ]
        result = mgr.set_bulk("my-share", perms)
        assert result["changed"] is True
        assert result["action"] == "set_bulk"
        assert result["count"] == 2
        # Only one API call (user batch)
        assert mock_client.request.call_count == 1

    def test_set_bulk_groups_only(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        perms = [
            {"name": "developers", "is_group": True, "perm": "read_write"},
        ]
        result = mgr.set_bulk("my-share", perms)
        assert result["changed"] is True
        assert result["count"] == 1
        call = mock_client.request.call_args
        assert call.kwargs.get("user_group_type") == "local_group"

    def test_set_bulk_mixed_users_and_groups(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        perms = [
            {"name": "admin", "is_group": False, "perm": "read_write"},
            {"name": "developers", "is_group": True, "perm": "read_only"},
        ]
        result = mgr.set_bulk("my-share", perms)
        assert result["count"] == 2
        # Two API calls (user batch + group batch)
        assert mock_client.request.call_count == 2

    def test_set_bulk_empty_list(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.set_bulk("my-share", [])
        assert result["changed"] is True
        assert result["count"] == 0
        mock_client.request.assert_not_called()

    def test_set_bulk_dry_run(self, mock_client):
        mgr = _mgr(mock_client)
        perms = [{"name": "admin", "is_group": False, "perm": "read_write"}]
        result = mgr.set_bulk("my-share", perms, dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_set_bulk"
        assert result["count"] == 1
        mock_client.request.assert_not_called()


class TestEnsurePresent:
    def test_ensure_present_noop_when_matches(self, mock_client):
        _mock_list_responses(
            mock_client,
            [{"name": "admin", "is_writable": True, "is_readonly": False, "is_deny": False}],
        )
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "admin", "read_write")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_present_sets_when_different(self, mock_client):
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if args[1] == "list":
                if kwargs.get("user_group_type") == "local_group":
                    return {"items": []}
                return {
                    "items": [
                        {
                            "name": "admin",
                            "is_writable": False,
                            "is_readonly": True,
                            "is_deny": False,
                        }
                    ]
                }
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "admin", "read_write")
        assert result["changed"] is True
        assert result["action"] == "set"
        assert result["before"] == "read_only"
        assert result["after"] == "read_write"

    def test_ensure_present_sets_when_not_found(self, mock_client):
        def side_effect(*args, **kwargs):
            if args[1] == "list":
                return {"items": []}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "newuser", "read_write")
        assert result["changed"] is True
        assert result["action"] == "set"
        assert result["before"] is None
        assert result["after"] == "read_write"

    def test_ensure_present_group(self, mock_client):
        def side_effect(*args, **kwargs):
            if args[1] == "list":
                if kwargs.get("user_group_type") == "local_group":
                    return {
                        "items": [
                            {
                                "name": "devs",
                                "is_writable": True,
                                "is_readonly": False,
                                "is_deny": False,
                            }
                        ]
                    }
                return {"items": []}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "devs", "read_write", is_group=True)
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_present_dry_run_would_set(self, mock_client):
        _mock_list_responses(mock_client, [], [])
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "admin", "read_write", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_set"
        assert result["before"] is None
        assert result["after"] == "read_write"

    def test_ensure_present_dry_run_noop_no_api_call_for_set(self, mock_client):
        _mock_list_responses(
            mock_client,
            [{"name": "admin", "is_writable": True, "is_readonly": False, "is_deny": False}],
        )
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "admin", "read_write", dry_run=True)
        assert result["changed"] is False
        assert result["action"] == "noop"


class TestEnsureAbsent:
    def test_ensure_absent_removes_when_has_perm(self, mock_client):
        def side_effect(*args, **kwargs):
            if args[1] == "list":
                if kwargs.get("user_group_type") == "local_group":
                    return {"items": []}
                return {
                    "items": [
                        {
                            "name": "admin",
                            "is_writable": True,
                            "is_readonly": False,
                            "is_deny": False,
                        }
                    ]
                }
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "admin", "read_write", state="absent")
        assert result["changed"] is True
        assert result["action"] == "removed"
        assert result["before"] == "read_write"

    def test_ensure_absent_noop_when_no_access(self, mock_client):
        _mock_list_responses(
            mock_client,
            [{"name": "admin", "is_writable": False, "is_readonly": False, "is_deny": False}],
        )
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "admin", "read_write", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_absent_noop_when_not_found(self, mock_client):
        _mock_list_responses(mock_client, [], [])
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "unknown", "read_write", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_absent_dry_run(self, mock_client):
        def side_effect(*args, **kwargs):
            if args[1] == "list":
                if kwargs.get("user_group_type") == "local_group":
                    return {"items": []}
                return {
                    "items": [
                        {
                            "name": "admin",
                            "is_writable": True,
                            "is_readonly": False,
                            "is_deny": False,
                        }
                    ]
                }
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "admin", "read_write", state="absent", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_remove"
        assert result["before"] == "read_write"

    def test_ensure_absent_group(self, mock_client):
        def side_effect(*args, **kwargs):
            if args[1] == "list":
                if kwargs.get("user_group_type") == "local_group":
                    return {
                        "items": [
                            {
                                "name": "devs",
                                "is_writable": False,
                                "is_readonly": True,
                                "is_deny": False,
                            }
                        ]
                    }
                return {"items": []}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.ensure("my-share", "devs", "read_only", is_group=True, state="absent")
        assert result["changed"] is True
        assert result["action"] == "removed"


class TestEnsureInvalidState:
    def test_ensure_invalid_state_raises(self, mock_client):
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("my-share", "admin", "read_write", state="broken")
