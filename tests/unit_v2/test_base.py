# SPDX-License-Identifier: MIT
"""Tests for BaseManager ABC enforcement, enums, EnsureResult, and ClientProtocol."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from synology_dsm_v2.base import (
    Action,
    BaseManager,
    ClientProtocol,
    EnsureResult,
    State,
)


# -- Fixtures --


def _mock_client() -> MagicMock:
    """Create a mock client that satisfies ClientProtocol."""
    client = MagicMock(spec=["base_url", "request"])
    client.base_url = "https://10.6.224.6:5001/webapi"
    return client


# -- BaseManager ABC enforcement --


class TestBaseManagerABC:
    def test_cannot_instantiate_without_ensure(self) -> None:
        """A manager missing ensure() raises TypeError."""

        class BadManager(BaseManager):
            def __init__(self, client):
                super().__init__(client, api="SYNO.Test", version=1)

            def list(self):  # type: ignore[override]
                return []

            def get(self, name):  # type: ignore[override]
                return None

        with pytest.raises(TypeError, match="ensure"):
            BadManager(_mock_client())  # type: ignore[abstract]

    def test_cannot_instantiate_without_list(self) -> None:
        """A manager missing list() raises TypeError."""

        class BadManager(BaseManager):
            def __init__(self, client):
                super().__init__(client, api="SYNO.Test", version=1)

            def ensure(self, name, state=State.PRESENT, dry_run=False, **kw):  # type: ignore[override]
                return EnsureResult(changed=False, action=Action.NOOP)

            def get(self, name):  # type: ignore[override]
                return None

        with pytest.raises(TypeError, match="list"):
            BadManager(_mock_client())  # type: ignore[abstract]

    def test_cannot_instantiate_without_get(self) -> None:
        """A manager missing get() raises TypeError."""

        class BadManager(BaseManager):
            def __init__(self, client):
                super().__init__(client, api="SYNO.Test", version=1)

            def ensure(self, name, state=State.PRESENT, dry_run=False, **kw):  # type: ignore[override]
                return EnsureResult(changed=False, action=Action.NOOP)

            def list(self):  # type: ignore[override]
                return []

        with pytest.raises(TypeError, match="get"):
            BadManager(_mock_client())  # type: ignore[abstract]

    def test_complete_manager_instantiates(self) -> None:
        """A manager with all abstract methods implemented instantiates."""

        class GoodManager(BaseManager):
            def __init__(self, client):
                super().__init__(client, api="SYNO.Test", version=1)

            def ensure(self, name, state=State.PRESENT, dry_run=False, **kw):  # type: ignore[override]
                return EnsureResult(changed=False, action=Action.NOOP)

            def list(self):  # type: ignore[override]
                return []

            def get(self, name):  # type: ignore[override]
                return None

        mgr = GoodManager(_mock_client())
        assert mgr is not None

    def test_request_helper(self) -> None:
        """_request() calls client.request with the manager's api and version."""

        class TestManager(BaseManager):
            def __init__(self, client):
                super().__init__(client, api="SYNO.Core.Test", version=3)

            def ensure(self, name, state=State.PRESENT, dry_run=False, **kw):  # type: ignore[override]
                return EnsureResult(changed=False, action=Action.NOOP)

            def list(self):  # type: ignore[override]
                return self._request("list")

            def get(self, name):  # type: ignore[override]
                return None

        client = _mock_client()
        client.request.return_value = {"items": []}
        mgr = TestManager(client)
        mgr.list()
        client.request.assert_called_once_with("SYNO.Core.Test", "list", 3)

    def test_api_property(self) -> None:
        """api and version are read-only properties."""
        from synology_dsm_v2.core_user import CoreUserManager

        mgr = CoreUserManager(_mock_client())
        assert mgr.api == "SYNO.Core.User"
        assert mgr.version == 1

    def test_repr(self) -> None:
        """BaseManager.__repr__ shows class name, api, and base_url."""

        class GoodManager(BaseManager):
            def __init__(self, client):
                super().__init__(client, api="SYNO.Test.Api", version=2)

            def ensure(self, name, state=State.PRESENT, dry_run=False, **kw):  # type: ignore[override]
                return EnsureResult(changed=False, action=Action.NOOP)

            def list(self):  # type: ignore[override]
                return []

            def get(self, name):  # type: ignore[override]
                return None

        mgr = GoodManager(_mock_client())
        r = repr(mgr)
        assert "GoodManager" in r
        assert "SYNO.Test.Api" in r
        assert "10.6.224.6" in r


# -- State enum --


class TestState:
    def test_present_value(self) -> None:
        assert State.PRESENT == "present"
        assert State.PRESENT.value == "present"

    def test_absent_value(self) -> None:
        assert State.ABSENT == "absent"
        assert State.ABSENT.value == "absent"

    def test_invalid_state_not_in_enum(self) -> None:
        with pytest.raises(ValueError):
            State("invalid")


# -- Action enum --


class TestAction:
    def test_all_values(self) -> None:
        expected = {
            "created", "updated", "deleted", "uploaded", "downloaded",
            "noop", "would_create", "would_update", "would_delete", "would_upload",
        }
        actual = {a.value for a in Action}
        assert actual == expected

    def test_string_comparison(self) -> None:
        assert Action.CREATED == "created"
        assert Action.NOOP == "noop"


# -- EnsureResult dataclass --


class TestEnsureResult:
    def test_basic_noop(self) -> None:
        r = EnsureResult(changed=False, action=Action.NOOP)
        assert r.changed is False
        assert r.action == Action.NOOP
        assert r.before is None
        assert r.after is None
        assert r.dry_run is False

    def test_created_with_after(self) -> None:
        after = {"name": "bob", "uid": 1001}
        r = EnsureResult(changed=True, action=Action.CREATED, after=after)
        assert r.changed is True
        assert r.action == Action.CREATED
        assert r.after == after

    def test_dry_run(self) -> None:
        r = EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True)
        assert r.dry_run is True
        assert r.changed is False

    def test_frozen_immutable(self) -> None:
        r = EnsureResult(changed=False, action=Action.NOOP)
        with pytest.raises(AttributeError):
            r.changed = True  # type: ignore[misc]

    def test_to_dict_minimal(self) -> None:
        r = EnsureResult(changed=False, action=Action.NOOP)
        d = r.to_dict()
        assert d == {"changed": False, "action": "noop"}

    def test_to_dict_full(self) -> None:
        before = {"name": "bob", "email": "old@example.com"}
        after = {"name": "bob", "email": "new@example.com"}
        r = EnsureResult(
            changed=True,
            action=Action.UPDATED,
            before=before,
            after=after,
        )
        d = r.to_dict()
        assert d == {
            "changed": True,
            "action": "updated",
            "before": before,
            "after": after,
        }

    def test_to_dict_dry_run(self) -> None:
        r = EnsureResult(changed=False, action=Action.WOULD_DELETE, dry_run=True)
        d = r.to_dict()
        assert d["dry_run"] is True
        assert d["action"] == "would_delete"

    def test_repr(self) -> None:
        r = EnsureResult(changed=True, action=Action.CREATED)
        assert "changed=True" in repr(r)
        assert "CREATED" in repr(r)


# -- ClientProtocol --


class TestClientProtocol:
    def test_real_client_satisfies_protocol(self) -> None:
        """DSMClient should satisfy ClientProtocol."""
        from synology_dsm_v2.client import DSMClient

        client = DSMClient("10.6.224.6")
        assert isinstance(client, ClientProtocol)

    def test_dict_does_not_satisfy_protocol(self) -> None:
        assert not isinstance({}, ClientProtocol)
