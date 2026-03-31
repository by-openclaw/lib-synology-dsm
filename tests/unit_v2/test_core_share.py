# SPDX-License-Identifier: MIT
"""Tests for CoreShareManager — list(), get(), ensure() (the only public methods)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.core_share import CoreShareManager


# -- Fixtures --


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.base_url = "https://10.6.224.6:5001/webapi"
    return client


def _share_dict(name: str = "my-share", desc: str = "Test share", **kw) -> dict:
    d = {"name": name, "vol_path": "/volume1", "desc": desc, "isdir": True}
    d.update(kw)
    return d


# -- Instantiation & repr --


class TestCoreShareManagerInit:
    def test_instantiation(self) -> None:
        mgr = CoreShareManager(_mock_client())
        assert mgr is not None

    def test_repr(self) -> None:
        mgr = CoreShareManager(_mock_client())
        r = repr(mgr)
        assert "CoreShareManager" in r
        assert "SYNO.Core.Share" in r
        assert "10.6.224.6" in r

    def test_api_property(self) -> None:
        mgr = CoreShareManager(_mock_client())
        assert mgr.api == "SYNO.Core.Share"
        assert mgr.version == 1


# -- list() --


class TestCoreShareManagerList:
    def test_list_returns_shares(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [_share_dict("share-a"), _share_dict("share-b")]}
        mgr = CoreShareManager(client)

        result = mgr.list()
        assert len(result) == 2
        assert result[0]["name"] == "share-a"
        client.request.assert_called_once()
        args = client.request.call_args
        assert args[0][0] == "SYNO.Core.Share"
        assert args[0][1] == "list"

    def test_list_empty(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": []}
        mgr = CoreShareManager(client)

        result = mgr.list()
        assert result == []


# -- get() --


class TestCoreShareManagerGet:
    def test_get_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [_share_dict("my-share")]}
        mgr = CoreShareManager(client)

        result = mgr.get("my-share")
        assert result is not None
        assert result["name"] == "my-share"

    def test_get_not_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [_share_dict("other")]}
        mgr = CoreShareManager(client)

        result = mgr.get("nonexistent")
        assert result is None


# -- ensure(state=PRESENT) --


class TestEnsurePresent:
    def test_create_when_missing(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"shares": []},                         # list() inside get() → not found
            {},                                     # _create()
            {"shares": [_share_dict("my-share")]},  # list() inside get() for after
        ]
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, vol_path="/volume1")
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        assert result.after is not None
        assert result.after["name"] == "my-share"

    def test_create_uses_shareinfo_json(self) -> None:
        """Verify create passes shareinfo as JSON object (DSM 7.x requirement)."""
        client = _mock_client()
        client.request.side_effect = [
            {"shares": []},                         # list() inside get()
            {},                                     # _create()
            {"shares": [_share_dict("my-share")]},  # list() inside get() for after
        ]
        mgr = CoreShareManager(client)

        mgr.ensure("my-share", state=State.PRESENT, vol_path="/volume1", description="My data")
        # The _create call should include shareinfo kwarg
        create_call = client.request.call_args_list[1]
        assert "shareinfo" in create_call.kwargs

    def test_noop_when_matches(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [_share_dict("my-share", desc="Test share")]}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, description="Test share")
        assert result.changed is False
        assert result.action == Action.NOOP
        assert result.before is not None

    def test_update_when_description_drifted(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"shares": [_share_dict("my-share", desc="old")]},   # get()
            {},                                                    # _update()
            {"shares": [_share_dict("my-share", desc="new")]},   # get() for after
        ]
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, description="new")
        assert result.changed is True
        assert result.action == Action.UPDATED
        assert result.before["desc"] == "old"
        assert result.after["desc"] == "new"


# -- ensure(state=ABSENT) --


class TestEnsureAbsent:
    def test_delete_when_exists(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"shares": [_share_dict("my-share")]},   # get()
            {},                                       # _delete()
        ]
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT)
        assert result.changed is True
        assert result.action == Action.DELETED
        assert result.before is not None

    def test_noop_when_already_absent(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": []}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP


# -- ensure(dry_run=True) --


class TestEnsureDryRun:
    def test_dry_run_would_create(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": []}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, dry_run=True)
        assert result.changed is False
        assert result.action == Action.WOULD_CREATE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_would_update(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [_share_dict("my-share", desc="old")]}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, dry_run=True, description="new")
        assert result.action == Action.WOULD_UPDATE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_would_delete(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [_share_dict("my-share")]}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT, dry_run=True)
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_noop(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [_share_dict("my-share", desc="Test share")]}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, dry_run=True, description="Test share")
        assert result.action == Action.NOOP
        assert result.changed is False


# -- ensure() returns EnsureResult (not dict) --


class TestEnsureResultType:
    def test_returns_ensure_result_not_dict(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": []}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT)
        assert isinstance(result, EnsureResult)
        assert not isinstance(result, dict)

    def test_to_dict_produces_v1_compatible_format(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": []}
        mgr = CoreShareManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "changed" in d
        assert "action" in d


# -- Invalid state --


class TestEnsureInvalidState:
    def test_invalid_state_raises(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": []}
        mgr = CoreShareManager(client)

        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("my-share", state="invalid")  # type: ignore[arg-type]


# -- No public CRUD methods --


class TestNoCRUDExposed:
    def test_no_public_create(self) -> None:
        mgr = CoreShareManager(_mock_client())
        assert not hasattr(mgr, "create")

    def test_no_public_update(self) -> None:
        mgr = CoreShareManager(_mock_client())
        assert not hasattr(mgr, "update")

    def test_no_public_delete(self) -> None:
        mgr = CoreShareManager(_mock_client())
        assert not hasattr(mgr, "delete")

    def test_private_crud_exists(self) -> None:
        mgr = CoreShareManager(_mock_client())
        assert hasattr(mgr, "_create")
        assert hasattr(mgr, "_update")
        assert hasattr(mgr, "_delete")
