"""Synology DSM — user and group management.

API: SYNO.Core.User (version 1, entry.cgi)

Verified against DSM 7.1.1-42962 Update 9 (nas01).

Notes:
- delete() requires name as a JSON array string: '["username"]'
- disable() uses expired="true" to soft-disable without deleting (preferred — preserves audit trail)
- add_to_group / remove_from_group delegate to GroupManager for consistency
"""
from __future__ import annotations

import json

from .client import DSMClient


class UserManager:
    """User and group CRUD operations."""

    def __init__(self, client: DSMClient):
        self._c = client

    def list(self) -> list[dict]:
        """List all users.

        Returns a list of dicts with at minimum: name.
        Pass additional=['description','email','expired','2fa_status'] for richer output.
        """
        data = self._c.request("SYNO.Core.User", "list", version=1)
        return data.get("users", [])

    def create(self, name: str, password: str, email: str = "", description: str = "") -> dict:
        """Create a user.

        Args:
            name: Username (alphanumeric, hyphen, underscore).
            password: Initial password.
            email: Email address (optional but recommended for notifications).
            description: Human-readable description. Always set — missing descriptions
                are flagged as a security gap during audits.

        Returns:
            Dict with user info from the API.
        """
        return self._c.request(
            "SYNO.Core.User", "create", version=1,
            name=name, password=password, email=email, description=description,
        )

    def delete(self, name: str) -> None:
        """Delete a user by name.

        Note: DSM API requires name as a JSON array string e.g. '["username"]'.
        Prefer disable() to preserve audit trail unless hard cleanup is needed.

        Args:
            name: Username to delete.
        """
        self._c.request("SYNO.Core.User", "delete", version=1,
                         name=json.dumps([name]))

    def disable(self, name: str) -> None:
        """Disable a user (preferred over delete — audit trail preserved).

        Args:
            name: Username to disable.
        """
        self._c.request("SYNO.Core.User", "set", version=1,
                         name=name, expired="true")

    def list_groups(self) -> list[dict]:
        """List all groups.

        Returns a list of dicts with at minimum: name, description.
        Delegates to SYNO.Core.Group.list.
        """
        data = self._c.request("SYNO.Core.Group", "list", version=1)
        return data.get("groups", [])

    def add_to_group(self, username: str, group: str) -> None:
        """Add a user to a group.

        Fetches current group members first to avoid overwriting existing membership.
        Requires admin session (session=DSM).

        Args:
            username: Username to add.
            group: Target group name.
        """
        from .groups import GroupManager
        GroupManager(self._c).add_member(group, username)

    def remove_from_group(self, username: str, group: str) -> None:
        """Remove a user from a group.

        Fetches current group members first and removes the specified user.
        Requires admin session (session=DSM).

        Args:
            username: Username to remove.
            group: Group name to remove from.
        """
        from .groups import GroupManager
        GroupManager(self._c).remove_member(group, username)
