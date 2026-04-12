# SPDX-License-Identifier: MIT
"""Base abstractions for all DSM resource managers.

Defines:
    - ClientProtocol: minimum interface any transport client must implement.
    - BaseManager: ABC with DI (client + api + version), shared _request(),
      enforces ensure(), list(), get().
    - State: enum for ensure() state parameter.
    - Action: enum for ensure() result action values.
    - EnsureResult: frozen dataclass returned by all ensure() calls.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ClientProtocol(Protocol):
    """Minimum interface any transport client must implement.

    DSMClient implements this for HTTP/urllib. A future Go CLI wrapper
    or SNMP client would implement the same protocol — type checking
    still works across transports.
    """

    @property
    def base_url(self) -> str:
        """Base URL or connection identifier."""
        ...

    def request(
        self,
        api: str,
        method: str,
        version: int = 1,
        **params: Any,
    ) -> dict[str, Any]:
        """Execute an authenticated API call and return the response data."""
        ...


class State(StrEnum):
    """Target state for ensure() operations."""

    PRESENT = "present"
    ABSENT = "absent"


class Action(StrEnum):
    """Action taken (or that would be taken) by an ensure() call."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    UPLOADED = "uploaded"
    DOWNLOADED = "downloaded"
    NOOP = "noop"
    # dry_run variants
    WOULD_CREATE = "would_create"
    WOULD_UPDATE = "would_update"
    WOULD_DELETE = "would_delete"
    WOULD_UPLOAD = "would_upload"


@dataclass(frozen=True)
class EnsureResult:
    """Immutable result from ensure().

    Attributes:
        changed: True if state was actually modified.
        action: What happened (or would happen in dry_run mode).
        before: Previous state snapshot (None if resource didn't exist).
        after: New state snapshot (None if resource was deleted).
        dry_run: True if this was a preview — no API calls were made.
    """

    changed: bool
    action: Action
    before: dict[str, Any] | None = field(default=None, repr=False)
    after: dict[str, Any] | None = field(default=None, repr=False)
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dict for Ansible module compatibility.

        Returns the same shape as v1: {"changed": bool, "action": str, ...}
        """
        d: dict[str, Any] = {
            "changed": self.changed,
            "action": self.action.value,
        }
        if self.before is not None:
            d["before"] = self.before
        if self.after is not None:
            d["after"] = self.after
        if self.dry_run:
            d["dry_run"] = True
        return d


class BaseManager(ABC):
    """Abstract base for all DSM resource managers.

    Every manager inherits from this class. It provides:
        - DI: client, api namespace, and api version injected at construction
        - _request(): shared method — all API calls go through here
        - api / version: read-only properties
        - __repr__: shows class name, API namespace, and base URL

    Every manager MUST implement:
        - list(): return all resources
        - get(): return a single resource by name
        - ensure(): idempotent create/update/delete (the only public write method)

    Internal CRUD (_create, _update, _delete) is private — callers use ensure() only.
    """

    def __init__(self, client: ClientProtocol, api: str, version: int = 1) -> None:
        """Initialize manager with injected dependencies.

        Args:
            client: Authenticated transport client (DSMClient or any ClientProtocol).
            api: SYNO API namespace (e.g., "SYNO.Core.User").
            version: API version (default 1).
        """
        self._client = client
        self._api = api
        self._version = version

    @property
    def api(self) -> str:
        """SYNO API namespace this manager wraps (read-only)."""
        return self._api

    @property
    def version(self) -> int:
        """API version (read-only)."""
        return self._version

    def _request(self, method: str, **params: Any) -> dict[str, Any]:
        """Execute an API call using the manager's api and version.

        All API calls in all managers go through this method.
        Never call self._client.request() directly — use self._request().
        """
        return self._client.request(self._api, method, self._version, **params)

    @abstractmethod
    def list(self) -> list[dict[str, Any]]:
        """List all resources of this type."""
        ...

    @abstractmethod
    def get(self, name: str) -> dict[str, Any] | None:
        """Get a single resource by name. Returns None if not found."""
        ...

    @abstractmethod
    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> EnsureResult:
        """Idempotent resource management — the only public write method.

        state=PRESENT: create if missing, update if drifted, noop if matches.
        state=ABSENT: delete if exists, noop if already gone.
        dry_run=True: preview without making any API calls.

        Internal CRUD (_create, _update, _delete) is private.
        Callers always use ensure().
        """
        ...

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"api={self._api!r}, "
            f"version={self._version}, "
            f"base_url={self._client.base_url!r})"
        )
