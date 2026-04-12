# SPDX-License-Identifier: MIT
"""Tests for CoreUserManager — list(), get(), ensure() (the only public methods)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.exceptions import DSMResourceNotFoundError
from synology_dsm_v2.core_user import CoreUserManager


# -- Fixtures --


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.base_url = "https://10.6.224.6:5001/webapi"
    return client


def _user_dict(name: str = "bob", email: str = "bob@example.com", **kw) -> dict:
    d = {"name": name, "uid": 1001, "email": email, "description": ""}
    d.update(kw)
    return d


# -- Instantiation & repr --


class TestCoreUserManagerInit:
    def test_instantiation(self) -> None:
        mgr = CoreUserManager(_mock_client())
        assert mgr is not None

    def test_repr(self) -> None:
        mgr = CoreUserManager(_mock_client())
        r = repr(mgr)
        assert "CoreUserManager" in r
        assert "SYNO.Core.User" in r
        assert "10.6.224.6" in r

    def test_api_property(self) -> None:
        mgr = CoreUserManager(_mock_client())
        assert mgr.api == "SYNO.Core.User"
        assert mgr.version == 1


# -- list() --


class TestCoreUserManagerList:
    def test_list_returns_users(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": [_user_dict("alice"), _user_dict("bob")]}
        mgr = CoreUserManager(client)

        result = mgr.list()
        assert len(result) == 2
        assert result[0]["name"] == "alice"
        # Verify _request() calls client.request with api + version positionally
        client.request.assert_called_once()
        args = client.request.call_args
        assert args[0][0] == "SYNO.Core.User"
        assert args[0][1] == "list"
        assert args[0][2] == 1

    def test_list_empty(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": []}
        mgr = CoreUserManager(client)

        result = mgr.list()
        assert result == []


# -- get() --


class TestCoreUserManagerGet:
    def test_get_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": [_user_dict("bob")]}
        mgr = CoreUserManager(client)

        result = mgr.get("bob")
        assert result is not None
        assert result["name"] == "bob"

    def test_get_not_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": [_user_dict("alice")]}
        mgr = CoreUserManager(client)

        result = mgr.get("nonexistent")
        assert result is None


# -- ensure(state=PRESENT) --


class TestEnsurePresent:
    def test_create_when_missing(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"users": []},                       # list() inside get() → not found
            {},                                   # _create()
            {"users": [_user_dict("bob")]},       # list() inside get() for after
        ]
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.PRESENT, password="s3cret")
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        assert result.after is not None
        assert result.after["name"] == "bob"

    def test_noop_when_matches(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": [_user_dict("bob", email="bob@example.com")]}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.PRESENT, email="bob@example.com")
        assert result.changed is False
        assert result.action == Action.NOOP
        assert result.before is not None

    def test_update_when_drifted(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"users": [_user_dict("bob", email="old@example.com")]},   # get() in ensure
            {},                                                         # _update()
            {"users": [_user_dict("bob", email="new@example.com")]},   # get() for after
        ]
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.PRESENT, email="new@example.com")
        assert result.changed is True
        assert result.action == Action.UPDATED
        assert result.before["email"] == "old@example.com"
        assert result.after["email"] == "new@example.com"

    def test_create_without_password_raises(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": []}
        mgr = CoreUserManager(client)

        with pytest.raises(ValueError, match="password is required"):
            mgr.ensure("bob", state=State.PRESENT)


# -- ensure(state=ABSENT) --


class TestEnsureAbsent:
    def test_delete_when_exists(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"users": [_user_dict("bob")]},   # get()
            {},                                # _delete()
        ]
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.ABSENT)
        assert result.changed is True
        assert result.action == Action.DELETED
        assert result.before is not None
        assert result.before["name"] == "bob"

    def test_noop_when_already_absent(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": []}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP


# -- ensure(dry_run=True) --


class TestEnsureDryRun:
    def test_dry_run_would_create(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": []}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.PRESENT, dry_run=True, password="s3cret")
        assert result.changed is False
        assert result.action == Action.WOULD_CREATE
        assert result.dry_run is True
        assert client.request.call_count == 1  # Only list() for get() — no write

    def test_dry_run_would_update(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": [_user_dict("bob", email="old@example.com")]}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.PRESENT, dry_run=True, email="new@example.com")
        assert result.action == Action.WOULD_UPDATE
        assert result.dry_run is True
        assert result.before is not None
        assert client.request.call_count == 1  # Only list() — no write

    def test_dry_run_would_delete(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": [_user_dict("bob")]}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.ABSENT, dry_run=True)
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        assert result.before is not None
        assert client.request.call_count == 1  # Only list() — no write

    def test_dry_run_noop(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": [_user_dict("bob", email="bob@example.com")]}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.PRESENT, dry_run=True, email="bob@example.com")
        assert result.action == Action.NOOP
        assert result.changed is False


# -- ensure() returns EnsureResult (not dict) --


class TestEnsureResultType:
    def test_returns_ensure_result_not_dict(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": []}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.ABSENT)
        assert isinstance(result, EnsureResult)
        assert not isinstance(result, dict)

    def test_to_dict_produces_v1_compatible_format(self) -> None:
        client = _mock_client()
        client.request.return_value = {"users": []}
        mgr = CoreUserManager(client)

        result = mgr.ensure("bob", state=State.ABSENT)
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
        client.request.return_value = {"users": []}
        mgr = CoreUserManager(client)

        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("bob", state="invalid")  # type: ignore[arg-type]


# -- No public CRUD methods --


class TestNoCRUDExposed:
    """CRUD is private. Only list(), get(), ensure() are public."""

    def test_no_public_create(self) -> None:
        mgr = CoreUserManager(_mock_client())
        assert not hasattr(mgr, "create")

    def test_no_public_update(self) -> None:
        mgr = CoreUserManager(_mock_client())
        assert not hasattr(mgr, "update")

    def test_no_public_delete(self) -> None:
        mgr = CoreUserManager(_mock_client())
        assert not hasattr(mgr, "delete")

    def test_private_crud_exists(self) -> None:
        mgr = CoreUserManager(_mock_client())
        assert hasattr(mgr, "_create")
        assert hasattr(mgr, "_update")
        assert hasattr(mgr, "_delete")
