# SPDX-License-Identifier: MIT
"""Integration test: v2 CoreUserManager against live NAS.

Reads credentials from workspace/infra/secrets/fabric/infra-synology-nas.json
(Vault KV v2 format — ADR-0009).

Full chain tested:
  secrets/*.json → DSMClient → CoreUserManager.ensure() → live NAS API

Usage:
    .venv/bin/python3 -m pytest tests/integration_v2/ -v -s

Requirements:
    - NAS reachable at host:port from JSON
    - rune-api account with administrators group + DSM Allow
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.client import DSMClient
from synology_dsm_v2.core_user import CoreUserManager

# -- Secrets loading --

SECRETS_PATH = (
    Path.home() / ".openclaw" / "workspace" / "infra" / "secrets" / "fabric/infra-synology-nas.json"
)
# Fallback: use environment variables if JSON not found
_ENV_FALLBACK = {
    "host": os.environ.get("NAS_HOST", ""),
    "port": os.environ.get("NAS_PORT", "5001"),
    "username": os.environ.get("API_USER", ""),
    "password": os.environ.get("API_PASS", ""),
}

TEST_USER = "v2-test-user"
TEST_PASSWORD = "V2T3st!Pass_2026"  # pragma: allowlist secret


def _load_credentials() -> dict[str, str]:
    """Load NAS credentials from JSON secret file or env vars."""
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            data = json.load(f)
        fields = data.get("fields", {})
        if fields.get("password") and "<REDACTED" not in fields["password"]:
            return fields

    # Fallback to env vars
    if _ENV_FALLBACK["host"] and _ENV_FALLBACK["password"]:
        return _ENV_FALLBACK

    pytest.skip(
        f"No credentials available. Either:\n"
        f"  - Fill {SECRETS_PATH} with real values, or\n"
        f"  - Set NAS_HOST, API_USER, API_PASS environment variables"
    )
    return {}  # unreachable, but satisfies type checker


@pytest.fixture(scope="module")
def client() -> DSMClient:
    """Authenticated DSMClient for the test session."""
    creds = _load_credentials()
    c = DSMClient(
        host=creds["host"],
        port=int(creds["port"]),
        timeout=30,
    )
    c.login(creds["username"], creds["password"])
    yield c
    c.logout()


@pytest.fixture(scope="module")
def users(client: DSMClient) -> CoreUserManager:
    """CoreUserManager instance."""
    return CoreUserManager(client)


# -- Tests: full ensure() lifecycle --


class TestLiveUserEnsure:
    """Full lifecycle: create → verify → update → verify → delete → verify."""

    def test_01_ensure_create(self, users: CoreUserManager) -> None:
        """ensure(state=PRESENT) creates a user that doesn't exist."""
        # Clean up if left over from a previous failed run
        existing = users.get(TEST_USER)
        if existing:
            users.delete(TEST_USER)

        result = users.ensure(
            TEST_USER,
            state=State.PRESENT,
            password=TEST_PASSWORD,
            email="v2test@by-systems.be",
            description="v2 PoC integration test user",
        )

        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED
        assert result.after is not None
        assert result.after["name"] == TEST_USER
        print(f"  Created: {result.to_dict()}")

    def test_02_ensure_noop(self, users: CoreUserManager) -> None:
        """ensure(state=PRESENT) with same fields is a no-op."""
        result = users.ensure(
            TEST_USER,
            state=State.PRESENT,
            email="v2test@by-systems.be",
            description="v2 PoC integration test user",
        )

        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop: {result.to_dict()}")

    def test_03_ensure_update(self, users: CoreUserManager) -> None:
        """ensure(state=PRESENT) with different fields updates the user."""
        result = users.ensure(
            TEST_USER,
            state=State.PRESENT,
            email="v2test-updated@by-systems.be",
        )

        assert result.changed is True
        assert result.action == Action.UPDATED
        assert result.before is not None
        assert result.after is not None
        print(f"  Updated: {result.to_dict()}")

    def test_04_ensure_dry_run_would_delete(self, users: CoreUserManager) -> None:
        """ensure(state=ABSENT, dry_run=True) previews deletion."""
        result = users.ensure(TEST_USER, state=State.ABSENT, dry_run=True)

        assert result.changed is False
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        assert result.before is not None

        # Verify user still exists (dry_run didn't actually delete)
        still_exists = users.get(TEST_USER)
        assert still_exists is not None
        print(f"  Dry-run delete: {result.to_dict()}")

    def test_05_ensure_delete(self, users: CoreUserManager) -> None:
        """ensure(state=ABSENT) deletes the user."""
        result = users.ensure(TEST_USER, state=State.ABSENT)

        assert result.changed is True
        assert result.action == Action.DELETED
        assert result.before is not None
        print(f"  Deleted: {result.to_dict()}")

    def test_06_ensure_absent_noop(self, users: CoreUserManager) -> None:
        """ensure(state=ABSENT) on already-deleted user is a no-op."""
        result = users.ensure(TEST_USER, state=State.ABSENT)

        assert result.changed is False
        assert result.action == Action.NOOP
        print(f"  Noop (already absent): {result.to_dict()}")


# -- Tests: return type validation --


class TestLiveResultTypes:
    def test_ensure_returns_ensure_result(self, users: CoreUserManager) -> None:
        """Live ensure() returns EnsureResult, not dict."""
        result = users.ensure(TEST_USER, state=State.ABSENT)
        assert isinstance(result, EnsureResult)
        assert not isinstance(result, dict)

    def test_to_dict_is_v1_compatible(self, users: CoreUserManager) -> None:
        """to_dict() produces v1-compatible format for Ansible."""
        result = users.ensure(TEST_USER, state=State.ABSENT)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "changed" in d
        assert "action" in d
        assert isinstance(d["changed"], bool)
        assert isinstance(d["action"], str)


# -- Tests: error handling --


class TestLiveErrorHandling:
    def test_list_works(self, users: CoreUserManager) -> None:
        """list() returns a list without errors."""
        result = users.list()
        assert isinstance(result, list)
        assert len(result) > 0  # At least admin user exists
        print(f"  Listed {len(result)} users")

    def test_get_nonexistent_returns_none(self, users: CoreUserManager) -> None:
        """get() on nonexistent user returns None, not exception."""
        result = users.get("this-user-definitely-does-not-exist-xyzzy")
        assert result is None

    def test_ensure_absent_nonexistent_is_noop(self, users: CoreUserManager) -> None:
        """ensure(state=ABSENT) on nonexistent user is noop, not error."""
        result = users.ensure("this-user-definitely-does-not-exist-xyzzy", state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP


# -- Tests: client properties --


class TestLiveClientProperties:
    def test_client_is_authenticated(self, client: DSMClient) -> None:
        assert client.is_authenticated is True

    def test_client_sid_not_none(self, client: DSMClient) -> None:
        assert client.sid is not None

    def test_client_repr_shows_authenticated(self, client: DSMClient) -> None:
        r = repr(client)
        assert "authenticated" in r
        assert "not authenticated" not in r
