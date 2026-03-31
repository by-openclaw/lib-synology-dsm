# SPDX-License-Identifier: MIT
"""SYNO.Core.Group — local group management.

API: SYNO.Core.Group v1
Member API: SYNO.Core.Group.Member v1
Public methods: list(), get(), ensure()
Internal CRUD: _create(), _update(), _delete() — called by ensure() only.
Internal membership: _list_members(), _add_member(), _remove_member().

Known DSM quirk (DSM 7.1.x):
    SYNO.Core.Group.Member list may return error 103. Fallback chain:
    1. SYNO.Core.Group.Member list ingroup=true (primary — matches DSM UI)
    2. SYNO.Core.Group member_list (may work on DSM 7.2.x+)
    3. SYNO.Core.Group get + parse members field (last resort)
"""

from __future__ import annotations

import json
from typing import Any

from synology_dsm_v2.base import Action, BaseManager, ClientProtocol, EnsureResult, State


class CoreGroupManager(BaseManager):
    """SYNO.Core.Group — local group CRUD + membership via ensure().

    Usage::

        groups = CoreGroupManager(client)

        # Create group with members
        result = groups.ensure("svc-automation", state=State.PRESENT,
                               description="Automation accounts",
                               members=["alice", "bob"])

        # Delete
        result = groups.ensure("svc-automation", state=State.ABSENT)

        # Read
        all_groups = groups.list()
        grp = groups.get("svc-automation")
    """

    _DIFF_FIELDS = ("description",)

    def __init__(self, client: ClientProtocol) -> None:
        super().__init__(client, api="SYNO.Core.Group", version=1)

    # -- Public: read --

    def list(self) -> list[dict[str, Any]]:
        """List all local groups."""
        data = self._request("list")
        return data.get("groups", [])

    def get(self, name: str) -> dict[str, Any] | None:
        """Get a single group by name. Returns None if not found."""
        for group in self.list():
            if group.get("name") == name:
                return group
        return None

    # -- Public: write (only ensure) --

    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> EnsureResult:
        """Idempotent group management.

        state=PRESENT: create if missing, update if drifted, noop if matches.
            kwargs: description, members (list[str]).
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
        """Create a local group."""
        return self._request(
            "create",
            name=name,
            description=kwargs.get("description", ""),
        )

    def _update(self, name: str, **kwargs: Any) -> dict[str, Any]:
        """Update an existing group."""
        return self._request("set", name=name, **kwargs)

    def _delete(self, name: str) -> dict[str, Any]:
        """Delete a local group."""
        return self._request("delete", name=json.dumps([name]))

    # -- Private: membership --

    def _list_members(self, group: str) -> list[str]:
        """List members of a group. Returns list of usernames.

        Uses a fallback chain for DSM version compatibility:
        1. SYNO.Core.Group.Member list ingroup=true (primary)
        2. SYNO.Core.Group member_list
        3. SYNO.Core.Group get + parse members field
        """
        # Multi-API: direct client call — BaseManager contract preserved
        # Primary: SYNO.Core.Group.Member list (matches DSM UI)
        try:
            data = self._client.request(
                api="SYNO.Core.Group.Member",
                method="list",
                version=1,
                group=group,
                ingroup="true",
            )
            if "offset" in data:
                users = data.get("users", [])
                return [u.get("name", u) if isinstance(u, dict) else u for u in users]
        except Exception:
            pass

        # Fallback: SYNO.Core.Group member_list
        try:
            data = self._request("member_list", name=group)
            users = data.get("users", data.get("members", []))
            if users:
                return [u.get("name", u) if isinstance(u, dict) else u for u in users]
        except Exception:
            pass

        # Last resort: SYNO.Core.Group get + parse
        try:
            data = self._request("get", name=group)
            groups_data = data.get("groups", [])
            current = groups_data[0] if groups_data else data
            members = current.get("members", current.get("users", []))
            if members:
                return [m.get("name", m) if isinstance(m, dict) else m for m in members]
        except Exception:
            pass

        return []

    def _add_member(self, group: str, username: str) -> dict[str, Any]:
        """Add a user to a group."""
        # Multi-API: direct client call — BaseManager contract preserved
        return self._client.request(
            api="SYNO.Core.Group.Member",
            method="add",
            version=1,
            group=group,
            name=username,
        )

    def _remove_member(self, group: str, username: str) -> dict[str, Any]:
        """Remove a user from a group."""
        # Multi-API: direct client call — BaseManager contract preserved
        return self._client.request(
            api="SYNO.Core.Group.Member",
            method="remove",
            version=1,
            group=group,
            name=username,
        )

    # -- Private: ensure logic --

    def _ensure_present(
        self,
        name: str,
        current: dict[str, Any] | None,
        dry_run: bool,
        **kwargs: Any,
    ) -> EnsureResult:
        """Create if missing, update if drifted, noop if matches."""
        desired_members: list[str] | None = kwargs.pop("members", None)

        if current is None:
            if dry_run:
                return EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True)
            self._create(name, **kwargs)
            if desired_members is not None:
                for user in desired_members:
                    self._add_member(name, user)
            after = self.get(name)
            return EnsureResult(changed=True, action=Action.CREATED, after=after)

        # Group exists — check for drift
        diff = self._compute_diff(current, kwargs)
        members_changed = False

        if desired_members is not None:
            current_members = set(self._list_members(name))
            desired_set = set(desired_members)
            members_changed = current_members != desired_set

        if not diff and not members_changed:
            return EnsureResult(changed=False, action=Action.NOOP, before=current)

        if dry_run:
            return EnsureResult(changed=False, action=Action.WOULD_UPDATE, before=current, dry_run=True)

        if diff:
            self._update(name, **diff)

        if members_changed and desired_members is not None:
            current_members = set(self._list_members(name))
            desired_set = set(desired_members)
            for user in desired_set - current_members:
                self._add_member(name, user)
            for user in current_members - desired_set:
                self._remove_member(name, user)

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
