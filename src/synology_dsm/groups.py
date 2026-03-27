"""Synology DSM — group management.

API: SYNO.Core.Group (version 1, entry.cgi)

Verified against DSM 7.1.1-42962 Update 9 (nas01).

Notes:
- delete() and similar bulk ops require the name as a JSON array string, e.g. '["grpname"]'
- member_set replaces the full member list; to add/remove, fetch current members first
- Group member listing via 'get' returns the group's metadata; member list comes from 'member_list'
  or equivalent — on some DSM versions member_set (API code 103) is unavailable for non-admin;
  use the admin session (session=DSM) for all write operations.
"""

from __future__ import annotations

import json

from .client import DSMClient


class GroupManager:
    """CRUD and membership operations for Synology DSM groups."""

    def __init__(self, client: DSMClient):
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

    def delete(self, name: str) -> None:
        """Delete a group by name.

        Note: DSM API requires the name as a JSON array string, e.g. '["grpname"]'.
        This mirrors the SYNO.Core.User.delete behaviour.

        Args:
            name: Group name to delete.
        """
        self._c.request("SYNO.Core.Group", "delete", version=1, name=json.dumps([name]))

    def get(self, name: str) -> dict:
        """Get group details by name.

        Returns dict with: name, gid, description, errors.
        """
        data = self._c.request("SYNO.Core.Group", "get", version=1, name=name)
        groups = data.get("groups", [])
        return groups[0] if groups else {}

    def add_member(self, group: str, username: str) -> None:
        """Add a user to a group.

        Fetches current members first to avoid overwriting the existing list.
        Requires admin session (session=DSM).

        Args:
            group: Group name.
            username: Username to add.
        """
        current = self.list_members(group)
        current_names = [m.get("name", m) if isinstance(m, dict) else m for m in current]
        if username not in current_names:
            current_names.append(username)
        self._c.request(
            "SYNO.Core.Group",
            "member_set",
            version=1,
            name=group,
            members=json.dumps(current_names),
        )

    def remove_member(self, group: str, username: str) -> None:
        """Remove a user from a group.

        Fetches current members first and removes the specified user.
        Requires admin session (session=DSM).

        Args:
            group: Group name.
            username: Username to remove.
        """
        current = self.list_members(group)
        current_names = [m.get("name", m) if isinstance(m, dict) else m for m in current]
        updated = [n for n in current_names if n != username]
        self._c.request(
            "SYNO.Core.Group",
            "member_set",
            version=1,
            name=group,
            members=json.dumps(updated),
        )

    def list_members(self, group: str) -> list[dict]:
        """List members of a group.

        Falls back to SYNO.Core.Group.get if member_list is unavailable (DSM version dependent).

        Args:
            group: Group name.

        Returns:
            List of user dicts (at minimum: name).
        """
        try:
            data = self._c.request("SYNO.Core.Group", "member_list", version=1, name=group)
            return data.get("users", data.get("members", []))
        except RuntimeError:
            # Fallback: get returns members under 'members' or 'users' key
            data = self._c.request("SYNO.Core.Group", "get", version=1, name=group)
            return data.get("members", data.get("users", []))
