# SPDX-License-Identifier: MIT
"""SYNO.Core.Share — shared folder management.

API: SYNO.Core.Share v1
Public methods: list(), get(), ensure()
Internal CRUD: _create(), _update(), _delete() — called by ensure() only.

Known DSM quirk:
    Share create requires 'shareinfo' JSON object, NOT flat params.
    Flat params return 403 regardless of permissions.
    Share delete requires name as JSON array string: '["name"]'.
"""

from __future__ import annotations

import json
from typing import Any

from synology_dsm_v2.base import Action, BaseManager, ClientProtocol, EnsureResult, State


class CoreShareManager(BaseManager):
    """SYNO.Core.Share — shared folder CRUD via ensure().

    Usage::

        shares = CoreShareManager(client)

        # Create share
        result = shares.ensure("my-share", state=State.PRESENT,
                               vol_path="/volume1", description="My data")

        # Delete
        result = shares.ensure("my-share", state=State.ABSENT)

        # Read
        all_shares = shares.list()
        share = shares.get("my-share")
    """

    _DIFF_FIELDS = ("desc",)

    def __init__(self, client: ClientProtocol) -> None:
        super().__init__(client, api="SYNO.Core.Share", version=1)

    # -- Public: read --

    def list(self) -> list[dict[str, Any]]:
        """List all shared folders."""
        data = self._request("list", additional="[]")
        return data.get("shares", [])

    def get(self, name: str) -> dict[str, Any] | None:
        """Get a single share by name. Returns None if not found."""
        for share in self.list():
            if share.get("name") == name:
                return share
        return None

    # -- Public: write (only ensure) --

    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> EnsureResult:
        """Idempotent shared folder management.

        state=PRESENT: create if missing, update if drifted, noop if matches.
            kwargs: vol_path (required on create), description.
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

    def _create(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Create a shared folder using shareinfo JSON object (DSM 7.x required format)."""
        vol_path = kwargs.get("vol_path", "/volume1")
        description = kwargs.get("description", "")
        shareinfo = json.dumps({
            "name": name,
            "vol_path": vol_path,
            "desc": description,
            "name_org": "",
        })
        return self._request("create", name=name, shareinfo=shareinfo)

    def _update(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Update an existing shared folder."""
        return self._request("set", name=name, **kwargs)

    def _delete(self, name: str) -> dict[str, Any]:
        """Delete a shared folder."""
        return self._request("delete", name=name)

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
            vol_path = kwargs.pop("vol_path", "/volume1")
            self._create(name, vol_path=vol_path, **kwargs)
            after = self.get(name)
            return EnsureResult(changed=True, action=Action.CREATED, after=after)

        # Map user-facing "description" kwarg to DSM API "desc" field for diff
        if "description" in kwargs:
            kwargs["desc"] = kwargs.pop("description")

        diff = self._compute_diff(current, kwargs)
        if not diff:
            return EnsureResult(changed=False, action=Action.NOOP, before=current)

        if dry_run:
            return EnsureResult(changed=False, action=Action.WOULD_UPDATE, before=current, dry_run=True)

        self._update(name, **diff)
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
            return EnsureResult(changed=False, action=Action.WOULD_DELETE, before=current, dry_run=True)

        self._delete(name)
        return EnsureResult(changed=True, action=Action.DELETED, before=current)

    def _compute_diff(self, current: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
        """Compare current vs desired. Return only changed fields."""
        diff: dict[str, Any] = {}
        for f in self._DIFF_FIELDS:
            if f in desired and current.get(f, "") != desired[f]:
                diff[f] = desired[f]
        return diff
