# SPDX-License-Identifier: MIT
"""Integration test: v2 FileStationManager against live NAS.

Reads credentials from workspace/infra/secrets/infra-synology-nas.json.

Full chain tested:
  secrets/*.json → DSMClient → FileStationManager.ensure() → live NAS API

Prerequisite: A shared folder must exist on the NAS.
Uses the first available share for folder operations.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.client import DSMClient
from synology_dsm_v2.filestation import FileStationManager

SECRETS_PATH = (
    Path.home() / ".openclaw" / "workspace" / "infra" / "secrets" / "infra-synology-nas.json"
)
_ENV_FALLBACK = {
    "host": os.environ.get("NAS_HOST", ""),
    "port": os.environ.get("NAS_PORT", "5001"),
    "username": os.environ.get("API_USER", ""),
    "password": os.environ.get("API_PASS", ""),
}

TEST_FOLDER = "v2-test-folder"


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
    # FileStation requires session="FileStation" — not the default "DSM" session.
    c.login(creds["username"], creds["password"], session="FileStation")
    yield c
    c.logout()


@pytest.fixture(scope="module")
def fs(client: DSMClient) -> FileStationManager:
    return FileStationManager(client)


@pytest.fixture(scope="module")
def test_share(fs: FileStationManager) -> str:
    """Get the first available share path for testing."""
    shares = fs.list()
    if not shares:
        pytest.skip("No shares available on NAS for FileStation testing")
    return "/" + shares[0]["name"]


class TestLiveFileStationEnsure:
    """Full lifecycle: create → noop → dry_run → delete → absent noop."""

    def test_01_ensure_create(self, fs: FileStationManager, test_share: str) -> None:
        folder_path = f"{test_share}/{TEST_FOLDER}"
        # Clean up from previous run
        existing = fs.get(folder_path)
        if existing:
            fs._delete_path(folder_path)

        result = fs.ensure(folder_path, state=State.PRESENT)
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        print(f"  Created: {result.to_dict()}")

    def test_02_ensure_noop(self, fs: FileStationManager, test_share: str) -> None:
        folder_path = f"{test_share}/{TEST_FOLDER}"
        result = fs.ensure(folder_path, state=State.PRESENT)
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop: {result.to_dict()}")

    def test_03_dry_run_would_delete(self, fs: FileStationManager, test_share: str) -> None:
        folder_path = f"{test_share}/{TEST_FOLDER}"
        result = fs.ensure(folder_path, state=State.ABSENT, dry_run=True)
        assert result.changed is False
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        still_exists = fs.get(folder_path)
        assert still_exists is not None
        print(f"  Dry-run delete: {result.to_dict()}")

    def test_04_ensure_delete(self, fs: FileStationManager, test_share: str) -> None:
        folder_path = f"{test_share}/{TEST_FOLDER}"
        result = fs.ensure(folder_path, state=State.ABSENT)
        assert result.changed is True
        assert result.action == Action.DELETED
        print(f"  Deleted: {result.to_dict()}")

    def test_05_ensure_absent_noop(self, fs: FileStationManager, test_share: str) -> None:
        folder_path = f"{test_share}/{TEST_FOLDER}"
        result = fs.ensure(folder_path, state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop (already absent): {result.to_dict()}")


class TestLiveFileStationErrorHandling:
    def test_list_shares_works(self, fs: FileStationManager) -> None:
        result = fs.list()
        assert isinstance(result, list)
        assert len(result) > 0
        print(f"  Listed {len(result)} shares")

    def test_get_nonexistent_returns_none(self, fs: FileStationManager) -> None:
        result = fs.get("/this-share-does-not-exist/nonexistent")
        assert result is None
