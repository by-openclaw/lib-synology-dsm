# SPDX-License-Identifier: MIT
"""Tests for CoreFileServNFSManager — list(), get(), ensure() (the only public methods)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.core_fileserv_nfs import CoreFileServNFSManager

# -- Fixtures --


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.base_url = "https://10.6.224.6:5001/webapi"
    return client


def _nfs_rule(client_host: str = "10.6.224.105", privilege: str = "rw", **kw) -> dict:
    d = {
        "client": client_host,
        "privilege": privilege,
        "root_squash": "root",
        "async": True,
        "insecure": False,
        "crossmnt": False,
        "security_flavor": {
            "sys": True,
            "kerberos": False,
            "kerberos_integrity": False,
            "kerberos_privacy": False,
        },
    }
    d.update(kw)
    return d


# -- Instantiation & repr --


class TestCoreFileServNFSManagerInit:
    def test_instantiation(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        assert mgr is not None

    def test_repr(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        r = repr(mgr)
        assert "CoreFileServNFSManager" in r
        assert "SYNO.Core.FileServ.NFS.SharePrivilege" in r

    def test_api_property(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        assert mgr.api == "SYNO.Core.FileServ.NFS.SharePrivilege"
        assert mgr.version == 1


# -- list() --


class TestCoreFileServNFSManagerList:
    def test_list_returns_rules(self) -> None:
        client = _mock_client()
        client.request.return_value = {
            "rule": [_nfs_rule("10.6.224.105"), _nfs_rule("10.6.224.106")]
        }
        mgr = CoreFileServNFSManager(client)

        result = mgr.list("my-share")
        assert len(result) == 2
        assert result[0]["client"] == "10.6.224.105"

    def test_list_empty(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": []}
        mgr = CoreFileServNFSManager(client)

        result = mgr.list("my-share")
        assert result == []

    def test_list_requires_share_name(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        with pytest.raises(ValueError, match="share_name is required"):
            mgr.list()


# -- get() --


class TestCoreFileServNFSManagerGet:
    def test_get_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": [_nfs_rule("10.6.224.105")]}
        mgr = CoreFileServNFSManager(client)

        result = mgr.get("my-share", hostname="10.6.224.105")
        assert result is not None
        assert result["client"] == "10.6.224.105"

    def test_get_not_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": [_nfs_rule("10.6.224.105")]}
        mgr = CoreFileServNFSManager(client)

        result = mgr.get("my-share", hostname="192.168.1.1")
        assert result is None

    def test_get_requires_hostname(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        with pytest.raises(ValueError, match="hostname kwarg is required"):
            mgr.get("my-share")


# -- ensure(state=PRESENT) --


class TestEnsurePresent:
    def test_create_when_missing(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"rule": []},  # list() inside get() → not found
            {"rule": []},  # list() inside _create() → get current rules
            {},  # _save_rules()
        ]
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, hostname="10.6.224.105", rw=True)
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        assert result.after is not None
        assert result.after["client"] == "10.6.224.105"
        assert result.after["privilege"] == "rw"

    def test_noop_when_matches(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": [_nfs_rule("10.6.224.105")]}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure(
            "my-share",
            state=State.PRESENT,
            hostname="10.6.224.105",
            rw=True,
            root_squash="root",
            async_io=True,
        )
        assert result.changed is False
        assert result.action == Action.NOOP

    def test_update_when_privilege_drifted(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"rule": [_nfs_rule("10.6.224.105", privilege="ro")]},  # get()
            {"rule": [_nfs_rule("10.6.224.105", privilege="ro")]},  # list() in _update()
            {},  # _save_rules()
        ]
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, hostname="10.6.224.105", rw=True)
        assert result.changed is True
        assert result.action == Action.UPDATED
        assert result.before["privilege"] == "ro"
        assert result.after["privilege"] == "rw"

    def test_update_when_root_squash_drifted(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"rule": [_nfs_rule("10.6.224.105", root_squash="all")]},  # get()
            {"rule": [_nfs_rule("10.6.224.105", root_squash="all")]},  # list() in _update()
            {},  # _save_rules()
        ]
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure(
            "my-share", state=State.PRESENT, hostname="10.6.224.105", root_squash="root"
        )
        assert result.changed is True
        assert result.action == Action.UPDATED

    def test_ensure_requires_hostname(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        with pytest.raises(ValueError, match="hostname kwarg is required"):
            mgr.ensure("my-share", state=State.PRESENT)


# -- ensure(state=ABSENT) --


class TestEnsureAbsent:
    def test_delete_when_exists(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"rule": [_nfs_rule("10.6.224.105")]},  # list() inside get()
            {"rule": [_nfs_rule("10.6.224.105")]},  # list() inside _delete()
            {},  # _save_rules()
        ]
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT, hostname="10.6.224.105")
        assert result.changed is True
        assert result.action == Action.DELETED
        assert result.before is not None

    def test_noop_when_already_absent(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": []}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT, hostname="10.6.224.105")
        assert result.changed is False
        assert result.action == Action.NOOP


# -- ensure(dry_run=True) --


class TestEnsureDryRun:
    def test_dry_run_would_create(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": []}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.PRESENT, dry_run=True, hostname="10.6.224.105")
        assert result.changed is False
        assert result.action == Action.WOULD_CREATE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_would_update(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": [_nfs_rule("10.6.224.105", privilege="ro")]}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure(
            "my-share", state=State.PRESENT, dry_run=True, hostname="10.6.224.105", rw=True
        )
        assert result.action == Action.WOULD_UPDATE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_would_delete(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": [_nfs_rule("10.6.224.105")]}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT, dry_run=True, hostname="10.6.224.105")
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_noop(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": [_nfs_rule("10.6.224.105")]}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure(
            "my-share", state=State.PRESENT, dry_run=True, hostname="10.6.224.105", rw=True
        )
        assert result.action == Action.NOOP
        assert result.changed is False


# -- ensure() returns EnsureResult --


class TestEnsureResultType:
    def test_returns_ensure_result_not_dict(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": []}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT, hostname="10.6.224.105")
        assert isinstance(result, EnsureResult)
        assert not isinstance(result, dict)

    def test_to_dict_produces_v1_compatible_format(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": []}
        mgr = CoreFileServNFSManager(client)

        result = mgr.ensure("my-share", state=State.ABSENT, hostname="10.6.224.105")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "changed" in d
        assert "action" in d


# -- Invalid state --


class TestEnsureInvalidState:
    def test_invalid_state_raises(self) -> None:
        client = _mock_client()
        client.request.return_value = {"rule": []}
        mgr = CoreFileServNFSManager(client)

        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("my-share", state="invalid", hostname="10.6.224.105")  # type: ignore[arg-type]


# -- No public CRUD methods --


class TestNoCRUDExposed:
    def test_no_public_create(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        assert not hasattr(mgr, "create")

    def test_no_public_update(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        assert not hasattr(mgr, "update")

    def test_no_public_delete(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        assert not hasattr(mgr, "delete")

    def test_private_crud_exists(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        assert hasattr(mgr, "_create")
        assert hasattr(mgr, "_update")
        assert hasattr(mgr, "_delete")


# -- Rule building --


class TestRuleBuilding:
    def test_build_rule_rw(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        rule = mgr._build_rule("10.6.224.105", rw=True)
        assert rule["client"] == "10.6.224.105"
        assert rule["privilege"] == "rw"
        assert rule["root_squash"] == "root"
        assert rule["async"] is True

    def test_build_rule_ro(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        rule = mgr._build_rule("10.6.224.105", rw=False)
        assert rule["privilege"] == "ro"

    def test_build_rule_custom_squash(self) -> None:
        mgr = CoreFileServNFSManager(_mock_client())
        rule = mgr._build_rule("10.6.224.105", root_squash="no_root_squash")
        assert rule["root_squash"] == "no_root_squash"

    def test_create_appends_to_existing(self) -> None:
        """_create() should append new rule to existing rules."""
        client = _mock_client()
        existing = _nfs_rule("10.6.224.105")
        client.request.side_effect = [
            {"rule": [existing]},  # list() inside _create()
            {},  # _save_rules()
        ]
        mgr = CoreFileServNFSManager(client)

        mgr._create("my-share", "10.6.224.106")
        # Verify save was called with 2 rules
        save_call = client.request.call_args_list[1]
        import json

        saved_rules = json.loads(save_call.kwargs["rule"])
        assert len(saved_rules) == 2

    def test_delete_filters_hostname(self) -> None:
        """_delete() should remove only the matching hostname."""
        client = _mock_client()
        client.request.side_effect = [
            {"rule": [_nfs_rule("10.6.224.105"), _nfs_rule("10.6.224.106")]},  # list()
            {},  # _save_rules()
        ]
        mgr = CoreFileServNFSManager(client)

        mgr._delete("my-share", "10.6.224.105")
        save_call = client.request.call_args_list[1]
        import json

        saved_rules = json.loads(save_call.kwargs["rule"])
        assert len(saved_rules) == 1
        assert saved_rules[0]["client"] == "10.6.224.106"
