# SPDX-License-Identifier: MIT
"""Integration test: v2 CoreFileServNFSManager against live NAS.

Reads credentials from workspace/infra/secrets/fabric/infra-synology-nas.json.

Full chain tested:
  secrets/*.json → DSMClient → CoreFileServNFSManager.ensure() → live NAS API

Prerequisite: A shared folder must exist on the NAS for NFS rule testing.
Uses an existing share (first one found) — does NOT create/delete shares.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.client import DSMClient
from synology_dsm_v2.core_fileserv_nfs import CoreFileServNFSManager
from synology_dsm_v2.core_share import CoreShareManager

SECRETS_PATH = (
    Path.home() / ".openclaw" / "workspace" / "infra" / "secrets" / "fabric/infra-synology-nas.json"
)
_ENV_FALLBACK = {
    "host": os.environ.get("NAS_HOST", ""),
    "port": os.environ.get("NAS_PORT", "5001"),
    "username": os.environ.get("API_USER", ""),
    "password": os.environ.get("API_PASS", ""),
}

TEST_HOSTNAME = "10.99.99.99"


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
def nfs(client: DSMClient) -> CoreFileServNFSManager:
    return CoreFileServNFSManager(client)


@pytest.fixture(scope="module")
def test_share(client: DSMClient) -> str:
    """Get an existing share name for NFS testing."""
    shares = CoreShareManager(client)
    share_list = shares.list()
    if not share_list:
        pytest.skip("No shares available on NAS for NFS testing")
    return share_list[0]["name"]


class TestLiveNFSEnsure:
    """Full lifecycle: create → noop → update → dry_run → delete → absent noop."""

    def test_01_ensure_create(self, nfs: CoreFileServNFSManager, test_share: str) -> None:
        # Clean up from previous run
        existing = nfs.get(test_share, hostname=TEST_HOSTNAME)
        if existing:
            nfs._delete(test_share, TEST_HOSTNAME)

        result = nfs.ensure(
            test_share,
            state=State.PRESENT,
            hostname=TEST_HOSTNAME,
            rw=True,
            root_squash="root",
        )
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        print(f"  Created NFS rule: {result.to_dict()}")

    def test_02_ensure_noop(self, nfs: CoreFileServNFSManager, test_share: str) -> None:
        result = nfs.ensure(
            test_share,
            state=State.PRESENT,
            hostname=TEST_HOSTNAME,
            rw=True,
            root_squash="root",
            async_io=True,
        )
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop: {result.to_dict()}")

    def test_03_ensure_update(self, nfs: CoreFileServNFSManager, test_share: str) -> None:
        result = nfs.ensure(
            test_share,
            state=State.PRESENT,
            hostname=TEST_HOSTNAME,
            rw=False,
        )
        assert result.changed is True
        assert result.action == Action.UPDATED
        print(f"  Updated: {result.to_dict()}")

    def test_04_dry_run_would_delete(self, nfs: CoreFileServNFSManager, test_share: str) -> None:
        result = nfs.ensure(test_share, state=State.ABSENT, hostname=TEST_HOSTNAME, dry_run=True)
        assert result.changed is False
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        still_exists = nfs.get(test_share, hostname=TEST_HOSTNAME)
        assert still_exists is not None
        print(f"  Dry-run delete: {result.to_dict()}")

    def test_05_ensure_delete(self, nfs: CoreFileServNFSManager, test_share: str) -> None:
        result = nfs.ensure(test_share, state=State.ABSENT, hostname=TEST_HOSTNAME)
        assert result.changed is True
        assert result.action == Action.DELETED
        print(f"  Deleted: {result.to_dict()}")

    def test_06_ensure_absent_noop(self, nfs: CoreFileServNFSManager, test_share: str) -> None:
        result = nfs.ensure(test_share, state=State.ABSENT, hostname=TEST_HOSTNAME)
        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop (already absent): {result.to_dict()}")


class TestLiveNFSErrorHandling:
    def test_list_works(self, nfs: CoreFileServNFSManager, test_share: str) -> None:
        result = nfs.list(share_name=test_share)
        assert isinstance(result, list)
        print(f"  Listed {len(result)} NFS rules on {test_share}")

    def test_get_nonexistent_returns_none(
        self, nfs: CoreFileServNFSManager, test_share: str
    ) -> None:
        result = nfs.get(test_share, hostname="192.168.255.255")
        assert result is None
