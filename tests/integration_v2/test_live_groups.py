# SPDX-License-Identifier: MIT
"""Integration test: v2 CoreGroupManager against live NAS.

Reads credentials from workspace/infra/secrets/infra-synology-nas.json.

Full chain tested:
  secrets/*.json → DSMClient → CoreGroupManager.ensure() → live NAS API
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.client import DSMClient
from synology_dsm_v2.core_group import CoreGroupManager

SECRETS_PATH = (
    Path.home() / ".openclaw" / "workspace" / "infra" / "secrets" / "infra-synology-nas.json"
)
_ENV_FALLBACK = {
    "host": os.environ.get("NAS_HOST", ""),
    "port": os.environ.get("NAS_PORT", "5001"),
    "username": os.environ.get("API_USER", ""),
    "password": os.environ.get("API_PASS", ""),
}

TEST_GROUP = "v2-test-group"


def _load_credentials() -> dict[str, str]:
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            data = json.load(f)
        fields = data.get("fields", {})
        if fields.get("password") and "<REDACTED" not in fields["password"]:
            return fields
    if _ENV_FALLBACK["host"] and _ENV_FALLBACK["password"]:
        return _ENV_FALLBACK
    pytest.skip("No credentials available")
    return {}


@pytest.fixture(scope="module")
def client() -> DSMClient:
    creds = _load_credentials()
    c = DSMClient(host=creds["host"], port=int(creds["port"]), timeout=30)
    c.login(creds["username"], creds["password"])
    yield c
    c.logout()


@pytest.fixture(scope="module")
def groups(client: DSMClient) -> CoreGroupManager:
    return CoreGroupManager(client)


class TestLiveGroupEnsure:
    """Full lifecycle: create → noop → update → dry_run → delete → absent noop."""

    def test_01_ensure_create(self, groups: CoreGroupManager) -> None:
        existing = groups.get(TEST_GROUP)
        if existing:
            groups._delete(TEST_GROUP)

        result = groups.ensure(
            TEST_GROUP,
            state=State.PRESENT,
            description="v2 integration test group",
        )
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        print(f"  Created: {result.to_dict()}")

    def test_02_ensure_noop(self, groups: CoreGroupManager) -> None:
        result = groups.ensure(
            TEST_GROUP,
            state=State.PRESENT,
            description="v2 integration test group",
        )
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop: {result.to_dict()}")

    def test_03_ensure_update(self, groups: CoreGroupManager) -> None:
        # DSM 7.1.x: description is not returned/persisted, excluded from diff.
        # Use members drift to verify update path on live NAS.
        # Note: requires a real user on NAS. Use the API username from credentials.
        import json as _json
        from pathlib import Path as _Path

        creds_path = _Path.home() / ".openclaw/workspace/infra/secrets/infra-synology-nas.json"
        _creds = _json.loads(creds_path.read_text())["fields"]
        _user = _creds.get("svc_rune_username") or _creds.get("username")

        result = groups.ensure(
            TEST_GROUP,
            state=State.PRESENT,
            members=[_user],
        )
        assert result.changed is True
        assert result.action == Action.UPDATED
        print(f"  Updated (members): {result.to_dict()}")

    def test_04_dry_run_would_delete(self, groups: CoreGroupManager) -> None:
        result = groups.ensure(TEST_GROUP, state=State.ABSENT, dry_run=True)
        assert result.changed is False
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        still_exists = groups.get(TEST_GROUP)
        assert still_exists is not None
        print(f"  Dry-run delete: {result.to_dict()}")

    def test_05_ensure_delete(self, groups: CoreGroupManager) -> None:
        result = groups.ensure(TEST_GROUP, state=State.ABSENT)
        assert result.changed is True
        assert result.action == Action.DELETED
        print(f"  Deleted: {result.to_dict()}")

    def test_06_ensure_absent_noop(self, groups: CoreGroupManager) -> None:
        result = groups.ensure(TEST_GROUP, state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop (already absent): {result.to_dict()}")


class TestLiveGroupErrorHandling:
    def test_list_works(self, groups: CoreGroupManager) -> None:
        result = groups.list()
        assert isinstance(result, list)
        assert len(result) > 0
        print(f"  Listed {len(result)} groups")

    def test_get_nonexistent_returns_none(self, groups: CoreGroupManager) -> None:
        result = groups.get("this-group-definitely-does-not-exist-xyzzy")
        assert result is None
