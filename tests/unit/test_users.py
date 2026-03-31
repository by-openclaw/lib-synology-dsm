"""Unit tests — UserManager."""

import pytest

from synology_dsm.exceptions import DSMNotFoundError
from synology_dsm.users import UserManager


def _mgr(mock_client):
    return UserManager(mock_client)


class TestUserCreate:
    def test_create_calls_api(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.create("alice", password="secret", email="a@b.com", description="Test")
        mock_client.request.assert_called_once_with(
            "SYNO.Core.User",
            "create",
            version=1,
            name="alice",
            password="secret",
            email="a@b.com",
            description="Test",
        )


class TestUserListDetailed:
    def test_list_detailed_normalizes_2fa_status(self, mock_client):
        """list_detailed normalizes 2fa_status → 2fa_enabled and expired → enabled."""
        mock_client.request.return_value = {
            "users": [
                {
                    "name": "alice",
                    "email": "alice@example.com",
                    "description": "test user",
                    "expired": "normal",
                    "2fa_status": True,
                },
                {
                    "name": "bob",
                    "email": "bob@example.com",
                    "description": "",
                    "expired": "expired",
                    "2fa_status": False,
                },
            ]
        }
        mgr = UserManager(mock_client)
        result = mgr.list_detailed()
        assert len(result) == 2

        alice = result[0]
        assert alice["2fa_enabled"] is True
        assert alice["enabled"] is True  # expired="normal" → enabled

        bob = result[1]
        assert bob["2fa_enabled"] is False
        assert bob["enabled"] is False  # expired="expired" → disabled


class TestUserGet:
    def test_get_returns_none_when_user_missing(self, mock_client):
        """get() returns None when user not found."""
        mock_client.request.return_value = {"users": [{"name": "other"}]}
        from synology_dsm import UserManager

        mgr = UserManager(mock_client)
        assert mgr.get("nonexistent") is None

    def test_get_returns_user_when_found(self, mock_client):
        """get() returns user dict when found."""
        mock_client.request.return_value = {"users": [{"name": "alice", "email": "a@b.com"}]}
        from synology_dsm import UserManager

        mgr = UserManager(mock_client)
        result = mgr.get("alice")
        assert result is not None
        assert result["name"] == "alice"


class TestUserEnsure:
    def _setup(self, mock_client, existing_users=None):
        """Configure mock to return given list of users."""
        users = existing_users or []
        # list() returns name dicts; list_detailed() returns full dicts
        mock_client.request.side_effect = lambda api, method, **kw: (
            {"users": [{"name": u["name"]} for u in users]}
            if method == "list" and "additional" not in kw
            else {"users": users}
        )

    def test_ensure_present_creates_when_absent(self, mock_client):
        # User does not exist — get() returns None
        mgr = _mgr(mock_client)
        # list_detailed returns empty list
        mock_client.request.return_value = {"users": []}
        result = mgr.ensure("bob", state="present", password="pw", description="Bob")
        assert result["changed"] is True
        assert result["action"] == "created"
        # create was called
        calls = [c for c in mock_client.request.call_args_list if c.args[1] == "create"]
        assert len(calls) == 1

    def test_ensure_present_noop_when_data_matches(self, mock_client):
        mgr = _mgr(mock_client)
        existing = [
            {
                "name": "alice",
                "email": "a@b.com",
                "description": "same",
                "expired": "normal",
                "2fa_enabled": False,
                "enabled": True,
            }
        ]
        mock_client.request.return_value = {"users": existing}
        result = mgr.ensure("alice", state="present", email="a@b.com", description="same")
        assert result["changed"] is False
        assert result["action"] == "noop"
        # no create or set called
        calls = [c for c in mock_client.request.call_args_list if c.args[1] in ("create", "set")]
        assert len(calls) == 0

    def test_ensure_present_updates_when_diff(self, mock_client):
        mgr = _mgr(mock_client)
        existing = [
            {
                "name": "alice",
                "email": "old@b.com",
                "description": "old",
                "expired": "normal",
                "2fa_enabled": False,
                "enabled": True,
            }
        ]
        mock_client.request.return_value = {"users": existing}
        result = mgr.ensure("alice", state="present", email="new@b.com", description="new")
        assert result["changed"] is True
        assert result["action"] == "updated"
        assert result["after"]["email"] == "new@b.com"

    def test_ensure_absent_deletes_when_exists(self, mock_client):
        mgr = _mgr(mock_client)
        existing = [
            {
                "name": "alice",
                "email": "",
                "description": "",
                "expired": "normal",
                "2fa_enabled": False,
                "enabled": True,
            }
        ]
        mock_client.request.return_value = {"users": existing}
        result = mgr.ensure("alice", state="absent")
        assert result["changed"] is True
        assert result["action"] == "deleted"
        delete_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "delete"]
        assert len(delete_calls) == 1

    def test_ensure_absent_noop_when_already_gone(self, mock_client):
        mgr = _mgr(mock_client)
        mock_client.request.return_value = {"users": []}
        result = mgr.ensure("ghost", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_dry_run_no_api_create(self, mock_client):
        mgr = _mgr(mock_client)
        mock_client.request.return_value = {"users": []}
        result = mgr.ensure("newuser", state="present", password="pw", dry_run=True)
        assert result["changed"] is True
        assert result["dry_run"] is True
        assert result["action"] == "would_create"
        # no create call
        create_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "create"]
        assert len(create_calls) == 0

    def test_ensure_dry_run_absent_no_delete(self, mock_client):
        mgr = _mgr(mock_client)
        existing = [
            {
                "name": "alice",
                "email": "",
                "description": "",
                "expired": "normal",
                "2fa_enabled": False,
                "enabled": True,
            }
        ]
        mock_client.request.return_value = {"users": existing}
        result = mgr.ensure("alice", state="absent", dry_run=True)
        assert result["changed"] is True
        assert result["dry_run"] is True
        assert result["action"] == "would_delete"
        delete_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "delete"]
        assert len(delete_calls) == 0


class TestUserDelete:
    def test_delete_raises_not_found_on_missing(self, mock_client):
        mgr = _mgr(mock_client)
        mock_client.request.return_value = {"users": []}
        with pytest.raises(DSMNotFoundError) as exc_info:
            mgr.delete("ghost")
        assert exc_info.value.code == 404

    def test_delete_calls_api_for_existing(self, mock_client):
        import json

        mgr = _mgr(mock_client)
        mock_client.request.return_value = {"users": [{"name": "alice"}]}
        mgr.delete("alice")
        delete_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "delete"]
        assert len(delete_calls) == 1
        assert delete_calls[0].kwargs["name"] == json.dumps(["alice"])

    def test_delete_dry_run(self, mock_client):
        mgr = _mgr(mock_client)
        mock_client.request.return_value = {"users": [{"name": "alice"}]}
        result = mgr.delete("alice", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_delete"
        assert result["target"] == "alice"
        delete_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "delete"]
        assert len(delete_calls) == 0


class TestUserUpdate:
    def test_update_returns_changed_dict(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.update("alice", description="new desc")
        assert result["changed"] is True
        assert result["action"] == "updated"
        assert result["target"] == "alice"


class TestUserDisable:
    def test_disable_calls_set_expired(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.disable("alice")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.User"
        assert call.args[1] == "set"
        assert call.kwargs.get("name") == "alice"
        assert call.kwargs.get("expired") == "true"

    def test_disable_returns_changed_dict(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.disable("alice")
        assert result["changed"] is True
        assert result["action"] == "disabled"
        assert result["target"] == "alice"


class TestUserListGroups:
    def test_list_groups_emits_deprecation_warning(self, mock_client):
        """list_groups() must emit DeprecationWarning directing to GroupManager."""
        import warnings

        mock_client.request.return_value = {"groups": []}
        from synology_dsm import UserManager

        mgr = UserManager(mock_client)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            mgr.list_groups()
        dep = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(dep) >= 1
        assert "GroupManager" in str(dep[0].message)

    def test_list_groups_returns_groups(self, mock_client):
        mock_client.request.return_value = {
            "groups": [{"name": "administrators"}, {"name": "users"}]
        }
        mgr = _mgr(mock_client)
        groups = mgr.list_groups()
        assert len(groups) == 2
        assert groups[0]["name"] == "administrators"

    def test_list_groups_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"groups": []}
        mgr = _mgr(mock_client)
        mgr.list_groups()
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Group"
        assert call.args[1] == "list"


class TestUserAddToGroup:
    def test_add_to_group_delegates_to_group_manager(self, mock_client):
        # alice NOT in group — list returns only "other"
        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 1, "users": [{"name": "other"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.add_to_group("alice", "devops")
        assert result["changed"] is True
        add_calls = [
            c
            for c in mock_client.request.call_args_list
            if c.args[0] == "SYNO.Core.Group.Member" and c.args[1] == "add"
        ]
        assert len(add_calls) == 1


class TestUserRemoveFromGroup:
    def test_remove_from_group_delegates_to_group_manager(self, mock_client):
        def side_effect(api, method, **kw):
            if api == "SYNO.Core.Group.Member" and method == "list":
                return {"offset": 0, "total": 2, "users": [{"name": "alice"}, {"name": "bob"}]}
            return {}

        mock_client.request.side_effect = side_effect
        mgr = _mgr(mock_client)
        result = mgr.remove_from_group("alice", "devops")
        assert result["changed"] is True
        remove_calls = [
            c
            for c in mock_client.request.call_args_list
            if c.args[0] == "SYNO.Core.Group.Member" and c.args[1] == "remove"
        ]
        assert len(remove_calls) == 1
        assert remove_calls[0].kwargs["name"] == "alice"


class TestUserEnsureDryRunEdgeCases:
    def test_ensure_dry_run_would_update(self, mock_client):
        existing = [
            {
                "name": "alice",
                "email": "old@b.com",
                "description": "",
                "expired": "normal",
                "2fa_enabled": False,
                "enabled": True,
            }
        ]
        mock_client.request.return_value = {"users": existing}
        mgr = _mgr(mock_client)
        result = mgr.ensure("alice", state="present", email="new@b.com", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_update"

    def test_ensure_invalid_state_raises(self, mock_client):
        mock_client.request.return_value = {"users": []}
        mgr = _mgr(mock_client)
        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("alice", state="broken")
