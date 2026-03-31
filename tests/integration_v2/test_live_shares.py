# SPDX-License-Identifier: MIT
"""Integration test: v2 CoreShareManager against live NAS.

Reads credentials from workspace/infra/secrets/infra-synology-nas.json.

Full chain tested:
  secrets/*.json → DSMClient → CoreShareManager.ensure() → live NAS API

WARNING: This test creates and deletes a real shared folder on the NAS.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.client import DSMClient
from synology_dsm_v2.core_share import CoreShareManager

SECRETS_PATH = Path.home() / ".openclaw" / "workspace" / "infra" / "secrets" / "infra-synology-nas.json"
_ENV_FALLBACK = {
    "host": os.environ.get("NAS_HOST", ""),
    "port": os.environ.get("NAS_PORT", "5001"),
    "username": os.environ.get("API_USER", ""),
    "password": os.environ.get("API_PASS", ""),
}

TEST_SHARE = "v2-test-share"


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
def shares(client: DSMClient) -> CoreShareManager:
    return CoreShareManager(client)


class TestLiveShareEnsure:
    """Full lifecycle: create → noop → update → dry_run → delete → absent noop."""

    def test_01_ensure_create(self, shares: CoreShareManager) -> None:
        existing = shares.get(TEST_SHARE)
        if existing:
            shares._delete(TEST_SHARE)

        result = shares.ensure(
            TEST_SHARE, state=State.PRESENT,
            vol_path="/volume1", description="v2 integration test share",
        )
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        print(f"  Created: {result.to_dict()}")

    def test_02_ensure_noop(self, shares: CoreShareManager) -> None:
        result = shares.ensure(
            TEST_SHARE, state=State.PRESENT,
            description="v2 integration test share",
        )
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop: {result.to_dict()}")

    def test_03_ensure_update(self, shares: CoreShareManager) -> None:
        result = shares.ensure(
            TEST_SHARE, state=State.PRESENT,
            description="v2 integration test share — updated",
        )
        assert result.changed is True
        assert result.action == Action.UPDATED
        print(f"  Updated: {result.to_dict()}")

    def test_04_dry_run_would_delete(self, shares: CoreShareManager) -> None:
        result = shares.ensure(TEST_SHARE, state=State.ABSENT, dry_run=True)
        assert result.changed is False
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        still_exists = shares.get(TEST_SHARE)
        assert still_exists is not None
        print(f"  Dry-run delete: {result.to_dict()}")

    def test_05_ensure_delete(self, shares: CoreShareManager) -> None:
        result = shares.ensure(TEST_SHARE, state=State.ABSENT)
        assert result.changed is True
        assert result.action == Action.DELETED
        print(f"  Deleted: {result.to_dict()}")

    def test_06_ensure_absent_noop(self, shares: CoreShareManager) -> None:
        result = shares.ensure(TEST_SHARE, state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop (already absent): {result.to_dict()}")


class TestLiveShareErrorHandling:
    def test_list_works(self, shares: CoreShareManager) -> None:
        result = shares.list()
        assert isinstance(result, list)
        assert len(result) > 0
        print(f"  Listed {len(result)} shares")

    def test_get_nonexistent_returns_none(self, shares: CoreShareManager) -> None:
        result = shares.get("this-share-definitely-does-not-exist-xyzzy")
        assert result is None
