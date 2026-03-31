# SPDX-License-Identifier: MIT
"""Tests for CoreGroupManager — list(), get(), ensure() (the only public methods)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.core_group import CoreGroupManager


# -- Fixtures --


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.base_url = "https://10.6.224.6:5001/webapi"
    return client


def _group_dict(name: str = "svc-auto", description: str = "Automation", **kw) -> dict:
    d = {"name": name, "gid": 65536, "description": description}
    d.update(kw)
    return d


# -- Instantiation & repr --


class TestCoreGroupManagerInit:
    def test_instantiation(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        assert mgr is not None

    def test_repr(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        r = repr(mgr)
        assert "CoreGroupManager" in r
        assert "SYNO.Core.Group" in r
        assert "10.6.224.6" in r

    def test_api_property(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        assert mgr.api == "SYNO.Core.Group"
        assert mgr.version == 1


# -- list() --


class TestCoreGroupManagerList:
    def test_list_returns_groups(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("admins"), _group_dict("users")]}
        mgr = CoreGroupManager(client)

        result = mgr.list()
        assert len(result) == 2
        assert result[0]["name"] == "admins"
        client.request.assert_called_once()
        args = client.request.call_args
        assert args[0][0] == "SYNO.Core.Group"
        assert args[0][1] == "list"
        assert args[0][2] == 1

    def test_list_empty(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": []}
        mgr = CoreGroupManager(client)

        result = mgr.list()
        assert result == []


# -- get() --


class TestCoreGroupManagerGet:
    def test_get_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("svc-auto")]}
        mgr = CoreGroupManager(client)

        result = mgr.get("svc-auto")
        assert result is not None
        assert result["name"] == "svc-auto"

    def test_get_not_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("other")]}
        mgr = CoreGroupManager(client)

        result = mgr.get("nonexistent")
        assert result is None


# -- ensure(state=PRESENT) --


class TestEnsurePresent:
    def test_create_when_missing(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"groups": []},                          # list() inside get() → not found
            {},                                      # _create()
            {"groups": [_group_dict("svc-auto")]},   # list() inside get() for after
        ]
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, description="Automation")
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        assert result.after is not None
        assert result.after["name"] == "svc-auto"

    def test_create_with_members(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"groups": []},                          # list() inside get() → not found
            {},                                      # _create()
            {},                                      # _add_member("alice")
            {},                                      # _add_member("bob")
            {"groups": [_group_dict("svc-auto")]},   # list() inside get() for after
        ]
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, members=["alice", "bob"])
        assert result.changed is True
        assert result.action == Action.CREATED
        # Verify _add_member was called via client.request for SYNO.Core.Group.Member
        member_calls = [
            c for c in client.request.call_args_list
            if c.kwargs.get("api") == "SYNO.Core.Group.Member" or
            (len(c.args) > 0 and c.args[0] == "SYNO.Core.Group.Member")
        ]
        assert len(member_calls) == 2

    def test_noop_when_matches(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("svc-auto", description="Automation")]}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, description="Automation")
        assert result.changed is False
        assert result.action == Action.NOOP
        assert result.before is not None

    def test_description_is_noop_on_drift(self) -> None:
        """DSM 7.1.x: group description is not persisted/returned — always excluded from diff.
        Passing a different description is a no-op (best-effort on create only).
        """
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("svc-auto", description="old")]}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, description="new")
        assert result.changed is False
        assert result.action == Action.NOOP

    def test_update_when_members_drifted(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"groups": [_group_dict("svc-auto")]},                  # get()
            # _list_members (diff check): SYNO.Core.Group.Member list
            {"offset": 0, "users": [{"name": "alice"}]},
            # _list_members (apply): SYNO.Core.Group.Member list
            {"offset": 0, "users": [{"name": "alice"}]},
            {},                                                      # _add_member("bob")
            {"groups": [_group_dict("svc-auto")]},                  # get() for after
        ]
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, members=["alice", "bob"])
        assert result.changed is True
        assert result.action == Action.UPDATED


# -- ensure(state=ABSENT) --


class TestEnsureAbsent:
    def test_delete_when_exists(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"groups": [_group_dict("svc-auto")]},   # get()
            {},                                       # _delete()
        ]
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.ABSENT)
        assert result.changed is True
        assert result.action == Action.DELETED
        assert result.before is not None
        assert result.before["name"] == "svc-auto"

    def test_noop_when_already_absent(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": []}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP


# -- ensure(dry_run=True) --


class TestEnsureDryRun:
    def test_dry_run_would_create(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": []}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, dry_run=True)
        assert result.changed is False
        assert result.action == Action.WOULD_CREATE
        assert result.dry_run is True
        assert client.request.call_count == 1  # Only list() — no write

    def test_dry_run_description_drift_is_noop(self) -> None:
        """DSM 7.1.x: description excluded from diff — dry_run with description drift = NOOP."""
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("svc-auto", description="old")]}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, dry_run=True, description="new")
        assert result.action == Action.NOOP
        assert result.changed is False

    def test_dry_run_would_delete(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("svc-auto")]}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.ABSENT, dry_run=True)
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        assert result.before is not None
        assert client.request.call_count == 1

    def test_dry_run_noop(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": [_group_dict("svc-auto", description="Automation")]}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, dry_run=True, description="Automation")
        assert result.action == Action.NOOP
        assert result.changed is False

    def test_dry_run_would_update_members(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"groups": [_group_dict("svc-auto")]},                # get()
            {"offset": 0, "users": [{"name": "alice"}]},          # _list_members
        ]
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.PRESENT, dry_run=True, members=["alice", "bob"])
        assert result.action == Action.WOULD_UPDATE
        assert result.dry_run is True


# -- ensure() returns EnsureResult (not dict) --


class TestEnsureResultType:
    def test_returns_ensure_result_not_dict(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": []}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.ABSENT)
        assert isinstance(result, EnsureResult)
        assert not isinstance(result, dict)

    def test_to_dict_produces_v1_compatible_format(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": []}
        mgr = CoreGroupManager(client)

        result = mgr.ensure("svc-auto", state=State.ABSENT)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "changed" in d
        assert "action" in d
        assert isinstance(d["changed"], bool)
        assert isinstance(d["action"], str)


# -- Invalid state --


class TestEnsureInvalidState:
    def test_invalid_state_raises(self) -> None:
        client = _mock_client()
        client.request.return_value = {"groups": []}
        mgr = CoreGroupManager(client)

        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("svc-auto", state="invalid")  # type: ignore[arg-type]


# -- No public CRUD methods --


class TestNoCRUDExposed:
    """CRUD is private. Only list(), get(), ensure() are public."""

    def test_no_public_create(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        assert not hasattr(mgr, "create")

    def test_no_public_update(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        assert not hasattr(mgr, "update")

    def test_no_public_delete(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        assert not hasattr(mgr, "delete")

    def test_private_crud_exists(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        assert hasattr(mgr, "_create")
        assert hasattr(mgr, "_update")
        assert hasattr(mgr, "_delete")

    def test_private_membership_exists(self) -> None:
        mgr = CoreGroupManager(_mock_client())
        assert hasattr(mgr, "_list_members")
        assert hasattr(mgr, "_add_member")
        assert hasattr(mgr, "_remove_member")


# -- Membership fallback chain --


class TestMembershipFallback:
    def test_list_members_primary(self) -> None:
        """Primary: SYNO.Core.Group.Member list with offset key."""
        client = _mock_client()
        client.request.return_value = {"offset": 0, "users": [{"name": "alice"}, {"name": "bob"}]}
        mgr = CoreGroupManager(client)

        result = mgr._list_members("svc-auto")
        assert result == ["alice", "bob"]

    def test_list_members_fallback_member_list(self) -> None:
        """Fallback: SYNO.Core.Group member_list."""
        client = _mock_client()
        # Primary fails, then member_list succeeds
        client.request.side_effect = [
            Exception("error 103"),
            {"users": [{"name": "charlie"}]},
        ]
        mgr = CoreGroupManager(client)

        result = mgr._list_members("svc-auto")
        assert result == ["charlie"]

    def test_list_members_fallback_get(self) -> None:
        """Last resort: SYNO.Core.Group get + parse."""
        client = _mock_client()
        client.request.side_effect = [
            Exception("error 103"),                                     # primary fails
            Exception("not supported"),                                 # member_list fails
            {"groups": [{"name": "grp", "members": [{"name": "dave"}]}]},  # get succeeds
        ]
        mgr = CoreGroupManager(client)

        result = mgr._list_members("grp")
        assert result == ["dave"]

    def test_list_members_all_fail_returns_empty(self) -> None:
        """All fallbacks fail → empty list."""
        client = _mock_client()
        client.request.side_effect = Exception("all fail")
        mgr = CoreGroupManager(client)

        result = mgr._list_members("grp")
        assert result == []
