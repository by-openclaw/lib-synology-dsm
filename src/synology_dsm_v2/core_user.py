# SPDX-License-Identifier: MIT
"""SYNO.Core.User — local user management.

API: SYNO.Core.User v1
Public methods: list(), get(), ensure()
Internal CRUD: _create(), _update(), _delete() — called by ensure() only.
"""

from __future__ import annotations

import json
from typing import Any

from synology_dsm_v2.base import Action, BaseManager, ClientProtocol, EnsureResult, State


class CoreUserManager(BaseManager):
    """SYNO.Core.User — local user CRUD via ensure().

    Usage::

        users = CoreUserManager(client)

        # Create or update
        result = users.ensure("bob", state=State.PRESENT, password="s3cret", email="bob@example.com")

        # Delete
        result = users.ensure("bob", state=State.ABSENT)

        # Preview
        result = users.ensure("bob", state=State.ABSENT, dry_run=True)

        # Read
        all_users = users.list()
        bob = users.get("bob")
    """

    # Fields compared during ensure() to detect drift.
    _DIFF_FIELDS = ("email", "description")

    def __init__(self, client: ClientProtocol) -> None:
        super().__init__(client, api="SYNO.Core.User", version=1)

    # -- Public: read --

    def list(self) -> list[dict[str, Any]]:
        """List all local users."""
        data = self._request(
            "list",
            offset=0,
            limit=-1,
            additional='["email","description","expired"]',
        )
        return data.get("users", [])

    def get(self, name: str) -> dict[str, Any] | None:
        """Get a single user by name. Returns None if not found."""
        for user in self.list():
            if user.get("name") == name:
                return user
        return None

    # -- Public: write (only ensure) --

    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> EnsureResult:
        """Idempotent user management.

        state=PRESENT: create if missing, update if drifted, noop if matches.
        state=ABSENT: delete if exists, noop if already gone.
        dry_run=True: preview without API calls.
        """
        current = self.get(name)

        if state == State.PRESENT:
            return self._ensure_present(name, current, dry_run, **kwargs)
        elif state == State.ABSENT:
            return self._ensure_absent(name, current, dry_run)
        else:
            raise ValueError(f"Invalid state: {state!r} — use State.PRESENT or State.ABSENT")

    # -- Private: CRUD (called by ensure only) --

    def _create(self, name: str, password: str, **kwargs: Any) -> dict[str, Any]:
        """Create a local user. Called by ensure(state=PRESENT) when user is missing."""
        return self._request(
            "create",
            name=name,
            password=password,
            email=kwargs.get("email", ""),
            description=kwargs.get("description", ""),
        )

    def _update(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Update an existing user. Called by ensure(state=PRESENT) when drift detected."""
        return self._request("set", name=name, **kwargs)

    def _delete(self, name: str) -> dict[str, Any]:
        """Delete a local user. Called by ensure(state=ABSENT)."""
        return self._request("delete", name=json.dumps([name]))

    # -- Private: ensure logic --

    def _ensure_present(
        self,
        name: str,
        current: dict[str, Any] | None,
        dry_run: bool,
        **kwargs: Any,
    ) -> EnsureResult:
        """Create if missing, update if drifted, noop if matches."""
        if current is None:
            if dry_run:
                return EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True)
            password = kwargs.pop("password", "")
            if not password:
                raise ValueError("password is required when creating a user")
            self._create(name, password=password, **kwargs)
            after = self.get(name)
            return EnsureResult(changed=True, action=Action.CREATED, after=after)

        diff = self._compute_diff(current, kwargs)
        if not diff:
            return EnsureResult(changed=False, action=Action.NOOP, before=current)

        if dry_run:
            return EnsureResult(
                changed=False, action=Action.WOULD_UPDATE, before=current, dry_run=True
            )

        update_fields = {k: v for k, v in diff.items() if k != "password"}
        if "password" in kwargs and kwargs["password"]:
            update_fields["password"] = kwargs["password"]

        self._update(name, **update_fields)
        after = self.get(name)
        return EnsureResult(changed=True, action=Action.UPDATED, before=current, after=after)

    def _ensure_absent(
        self,
        name: str,
        current: dict[str, Any] | None,
        dry_run: bool,
    ) -> EnsureResult:
        """Delete if exists, noop if already gone."""
        if current is None:
            return EnsureResult(changed=False, action=Action.NOOP)

        if dry_run:
            return EnsureResult(
                changed=False, action=Action.WOULD_DELETE, before=current, dry_run=True
            )

        self._delete(name)
        return EnsureResult(changed=True, action=Action.DELETED, before=current)

    def _compute_diff(self, current: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
        """Compare current vs desired. Return only changed fields."""
        diff: dict[str, Any] = {}
        for f in self._DIFF_FIELDS:
            if f in desired and current.get(f, "") != desired[f]:
                diff[f] = desired[f]
        return diff
