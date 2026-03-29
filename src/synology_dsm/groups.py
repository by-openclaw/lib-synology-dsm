"""Synology DSM — group management.

API: SYNO.Core.Group (version 1, entry.cgi)

Verified against DSM 7.1.1-42962 Update 9 (DS1513+).

MEMBER MANAGEMENT — CORRECT METHOD (discovered via live API probing 2026-03-28):
    DSM error 103 (invalid parameter) on member_set/member_add/add_member is because
    the correct method for member management is SYNO.Core.Group.set with 'members' param.
    NOT member_set. This replaces the full member list atomically.

    Correct shape:
        api=SYNO.Core.Group method=set name=<group> members=["user1","user2"] description="..."

    Requires: X-SYNO-TOKEN header (write op) + session=DSM + admin user.

Notes:
- delete() requires name as JSON array string: '["grpname"]'
- set() with members= replaces the full list — fetch current members first to add/remove
- X-SYNO-TOKEN is required for all write ops (set, create, delete)
"""

from __future__ import annotations

import builtins
import json

from .client import DSMClient


class GroupManager:
    """CRUD and membership operations for Synology DSM groups."""

    def __init__(self, client: DSMClient) -> None:
        """Initialise the manager with an authenticated DSMClient.

        Args:
            client: An authenticated :class:`DSMClient` instance.
        """
        self._c = client

    def list(self) -> list[dict]:
        """List all groups.

        Returns a list of dicts with at minimum: name, description, gid.
        """
        data = self._c.request("SYNO.Core.Group", "list", version=1)
        return data.get("groups", [])

    def create(self, name: str, description: str = "") -> dict:
        """Create a new group.

        Args:
            name: Group name (no spaces, alphanumeric + hyphen/underscore).
            description: Human-readable description. Always set — missing descriptions
                are flagged as a security gap during audits.

        Returns:
            Dict with group info from the API.
        """
        return self._c.request(
            "SYNO.Core.Group",
            "create",
            version=1,
            name=name,
            description=description,
        )

    def update(self, name: str, **kwargs: object) -> None:
        """Update group attributes.

        Updatable fields (verified against DSM 7.1.1):
            description (str)

        Args:
            name: Group name to update.
            **kwargs: Fields to update.

        Example:
            mgr.update("svc-automation", description="BY-SYSTEMS automation service accounts")
        """
        self._c.request("SYNO.Core.Group", "set", version=1, name=name, **kwargs)

    def delete(self, name: str, dry_run: bool = False) -> dict | None:
        """Delete a group by name.

        Note: DSM API requires the name as a JSON array string, e.g. '["grpname"]'.
        This mirrors the SYNO.Core.User.delete behaviour.

        Args:
            name: Group name to delete.
            dry_run: If True, return what would happen without making changes.

        Returns:
            None (or dry_run result dict).
        """
        if dry_run:
            return {"changed": True, "dry_run": True, "action": "would_delete", "target": name}
        self._c.request("SYNO.Core.Group", "delete", version=1, name=json.dumps([name]))
        return None

    def get(self, name: str) -> dict:
        """Get group details by name.

        Returns dict with: name, gid, description, errors.
        """
        data = self._c.request("SYNO.Core.Group", "get", version=1, name=name)
        groups = data.get("groups", [])
        return groups[0] if groups else {}

    def add_member(self, group: str, username: str) -> dict:
        """Add a user to a group (idempotent).

        Uses SYNO.Core.Group.Member add/list — the correct DSM UI API pair,
        discovered via DevTools F12 on DSM 7.1.1-42962 Update 9 (DS1513+).

        Args:
            group:    Group name.
            username: Username to add.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str).
        """
        current = self.list_members(group)
        current_names = [m.get("name", m) if isinstance(m, dict) else m for m in current]
        if username in current_names:
            return {"changed": False, "action": "noop"}
        self._c.request("SYNO.Core.Group.Member", "add", version=1, group=group, name=username)
        return {"changed": True, "action": "added", "user": username, "group": group}

    def remove_member(self, group: str, username: str) -> dict:
        """Remove a user from a group (idempotent).

        Uses SYNO.Core.Group.Member remove/list — the correct DSM UI API pair,
        discovered via DevTools F12 on DSM 7.1.1-42962 Update 9 (DS1513+).

        Args:
            group:    Group name.
            username: Username to remove.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str).
        """
        current = self.list_members(group)
        current_names = [m.get("name", m) if isinstance(m, dict) else m for m in current]
        if username not in current_names:
            return {"changed": False, "action": "noop"}
        self._c.request("SYNO.Core.Group.Member", "remove", version=1, group=group, name=username)
        return {"changed": True, "action": "removed", "user": username, "group": group}

    def list_members(self, group: str) -> builtins.list[dict]:
        """List members of a group.

        Falls back to SYNO.Core.Group.get if member_list is unavailable (DSM version dependent).

        Args:
            group: Group name.

        Returns:
            List of user dicts (at minimum: name).
        """
        # Primary: SYNO.Core.Group.Member list with group= + ingroup=true
        # Discovered via DevTools F12 — this is what DSM web UI calls.
        # Works on DSM 7.1.1-42962 Update 9 (DS1513+).
        # Returns total=N + users=[...] where N is count of users IN the group.
        try:
            data = self._c.request(
                "SYNO.Core.Group.Member",
                "list",
                version=1,
                group=group,
                ingroup="true",
            )
            # "offset" key is present on success (even for empty group: total=0, users=[])
            if "offset" in data:
                return data.get("users", [])
        except Exception:
            pass

        # Fallback: SYNO.Core.Group member_list (may work on DSM 7.2.x+)
        try:
            data = self._c.request("SYNO.Core.Group", "member_list", version=1, name=group)
            if "users" in data or "members" in data:
                return data.get("users", data.get("members", []))
        except Exception:
            pass

        # Last resort: SYNO.Core.Group get
        try:
            data = self._c.request("SYNO.Core.Group", "get", version=1, name=group)
            groups_data = data.get("groups", [])
            current = groups_data[0] if groups_data else data
            members = current.get("members", current.get("users", []))
            if members:
                return members
        except Exception:
            pass

        return []

    def ensure(
        self,
        name: str,
        state: str = "present",
        description: str = "",
        dry_run: bool = False,
    ) -> dict:
        """Ensure a group exists or is absent — idempotent.

        Mirrors Ansible state semantics:
            state="present" → create if not exists, update description if changed
            state="absent"  → delete if exists, no-op if already gone

        Args:
            name: Group name.
            state: "present" or "absent".
            description: Human-readable description.
            dry_run: If True, return what would happen without making changes.

        Returns:
            Dict with keys:
              - changed (bool)
              - action (str: created/updated/deleted/noop or would_* prefix for dry_run)
              - dry_run (bool, only when dry_run=True)
              - before/after (dicts, when changed and not noop)
        """
        existing_list = self.list()
        existing_map = {g["name"]: g for g in existing_list}

        if state == "present":
            if name not in existing_map:
                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_create",
                        "after": {"name": name, "description": description},
                    }
                self.create(name, description=description)
                return {
                    "changed": True,
                    "action": "created",
                    "after": {"name": name, "description": description},
                }
            else:
                # Use get() for accurate field values — list() returns empty description on some DSM versions
                current = self.get(name) or existing_map[name]
                diff = {}
                if current.get("description", "") != description:
                    diff["description"] = description

                if not diff:
                    return {"changed": False, "action": "noop"}

                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_update",
                        "before": {k: current.get(k) for k in diff},
                        "after": diff,
                    }
                self.update(name, **diff)
                return {
                    "changed": True,
                    "action": "updated",
                    "before": {k: current.get(k) for k in diff},
                    "after": diff,
                }

        elif state == "absent":
            if name in existing_map:
                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_delete",
                        "before": existing_map[name],
                    }
                self._c.request("SYNO.Core.Group", "delete", version=1, name=json.dumps([name]))
                return {"changed": True, "action": "deleted", "before": existing_map[name]}
            return {"changed": False, "action": "noop"}

        else:
            raise ValueError(f"Invalid state '{state}'. Use 'present' or 'absent'.")
