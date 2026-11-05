"""Unit tests for the by_systems.synology_dsm Ansible modules (ansible/ansible_collections/...).

The modules hold no API logic: each passes its options to a v2 manager's ensure() and maps the
EnsureResult. These tests check that mapping with a recording fake manager — no network.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("ansible.module_utils.basic")

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ansible"))

from ansible_collections.by_systems.synology_dsm.plugins.module_utils import (  # noqa: E402
    synology_dsm_common as common,
)
from ansible_collections.by_systems.synology_dsm.plugins.modules import (  # noqa: E402
    synology_dsm_nfs,
    synology_dsm_share,
)

from synology_dsm_v2 import Action, EnsureResult, State  # noqa: E402

CONN = {
    "host": "nas.example.com",
    "port": 5001,
    "username": "svc-test",
    "password": "not-a-secret",  # pragma: allowlist secret
    "verify_ssl": False,
    "timeout": 30,
}


class FakeManager:
    """Records the ensure() call and answers with the configured EnsureResult."""

    calls: list[tuple[str, dict[str, Any]]] = []
    answer = EnsureResult(changed=False, action=Action.NOOP)

    def __init__(self, client: Any) -> None:
        self.client = client

    def ensure(self, name: str, **kwargs: Any) -> EnsureResult:
        FakeManager.calls.append((name, kwargs))
        return FakeManager.answer


@pytest.fixture(autouse=True)
def _reset() -> None:
    FakeManager.calls = []
    FakeManager.answer = EnsureResult(changed=False, action=Action.NOOP)


def share_params(**over: Any) -> dict[str, Any]:
    return {
        **CONN,
        "name": "br-pmox-03-backup",
        "state": "present",
        "vol_path": "/volume1",
        "description": None,
        **over,
    }


def nfs_params(**over: Any) -> dict[str, Any]:
    p = {
        "share": "br-pmox-03-backup",
        "client": "10.6.239.177",
        "state": "present",
        "privilege": "rw",
    }
    return {**CONN, **p, "root_squash": "admin", "async_io": True, **over}


class TestCommon:
    def test_dry_run_change_is_changed(self) -> None:
        r = common.to_result(EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True))
        assert r["changed"] is True
        assert r["action"] == "would_create"

    def test_noop_is_unchanged(self) -> None:
        assert common.to_result(EnsureResult(changed=False, action=Action.NOOP))["changed"] is False

    def test_applied_change_is_changed(self) -> None:
        r = common.to_result(
            EnsureResult(changed=True, action=Action.UPDATED, before={"a": 1}, after={"a": 2})
        )
        assert r["changed"] is True
        assert r["before"] == {"a": 1}
        assert r["after"] == {"a": 2}

    def test_open_session_logs_in(self) -> None:
        seen: dict[str, Any] = {}

        class FakeClient:
            def __init__(self, host: str, **kw: Any) -> None:
                seen["init"] = (host, kw)

            def login(self, user: str, password: str) -> None:
                seen["login"] = (user, password)

        common.open_session(CONN, FakeClient)
        assert seen["init"] == (
            "nas.example.com",
            {"port": 5001, "https": True, "verify_ssl": False, "timeout": 30},
        )
        assert seen["login"] == ("svc-test", "not-a-secret")


class TestShare:
    def test_present_passes_volume_and_description(self) -> None:
        FakeManager.answer = EnsureResult(changed=True, action=Action.CREATED, after={"name": "x"})
        r = synology_dsm_share.run(
            share_params(description="node backups"), False, object(), FakeManager, State
        )
        name, kw = FakeManager.calls[0]
        assert name == "br-pmox-03-backup"
        assert kw == {
            "state": State.PRESENT,
            "dry_run": False,
            "vol_path": "/volume1",
            "description": "node backups",
        }
        assert r["changed"] is True and r["action"] == "created"

    def test_no_description_is_not_compared(self) -> None:
        synology_dsm_share.run(share_params(), False, object(), FakeManager, State)
        assert "description" not in FakeManager.calls[0][1]

    def test_check_mode_is_dry_run(self) -> None:
        FakeManager.answer = EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True)
        r = synology_dsm_share.run(share_params(), True, object(), FakeManager, State)
        assert FakeManager.calls[0][1]["dry_run"] is True
        assert r["changed"] is True

    def test_absent_sends_no_attributes(self) -> None:
        synology_dsm_share.run(share_params(state="absent"), False, object(), FakeManager, State)
        assert FakeManager.calls[0][1] == {"state": State.ABSENT, "dry_run": False}


class TestNfs:
    def test_present_maps_privilege_and_squash(self) -> None:
        synology_dsm_nfs.run(nfs_params(), False, object(), FakeManager, State)
        name, kw = FakeManager.calls[0]
        assert name == "br-pmox-03-backup"
        assert kw == {
            "state": State.PRESENT,
            "dry_run": False,
            "hostname": "10.6.239.177",
            "rw": True,
            "root_squash": "admin",
            "async_io": True,
        }

    def test_read_only(self) -> None:
        synology_dsm_nfs.run(nfs_params(privilege="ro"), False, object(), FakeManager, State)
        assert FakeManager.calls[0][1]["rw"] is False

    def test_absent_names_only_the_client(self) -> None:
        synology_dsm_nfs.run(nfs_params(state="absent"), False, object(), FakeManager, State)
        assert FakeManager.calls[0][1] == {
            "state": State.ABSENT,
            "dry_run": False,
            "hostname": "10.6.239.177",
        }

    def test_noop_unchanged(self) -> None:
        r = synology_dsm_nfs.run(nfs_params(), False, object(), FakeManager, State)
        assert r == {"changed": False, "action": "noop"}


class TestDocs:
    @pytest.mark.parametrize("mod", [synology_dsm_share, synology_dsm_nfs])
    def test_module_documented(self, mod: Any) -> None:
        for attr in ("DOCUMENTATION", "EXAMPLES", "RETURN"):
            assert getattr(mod, attr).strip()
