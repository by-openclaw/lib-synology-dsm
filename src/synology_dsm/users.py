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
from .exceptions import DSMNotFoundError


class UserManager:
    """User and group CRUD operations."""

    def __init__(self, client: DSMClient):
        self._c = client

    def list(self) -> list[dict]:
        """List all users (names only).

        Returns a list of dicts with at minimum: name.
        Use list_detailed() for full user records.
        """
        data = self._c.request("SYNO.Core.User", "list", version=1)
        return data.get("users", [])

    def list_detailed(self) -> list[dict]:
        """List all users with full details.

        Returns fields: name, description, email, expired, 2fa_status.

        Normalized output — compatible with NetBox/Authentik user schema:
            - name: str
            - email: str
            - description: str
            - expired: str — "normal" | "expired" | "never"
            - 2fa_status: bool — True if 2FA is enabled
            - enabled: bool — derived from expired field (True = not expired)

        Returns:
            List of normalized user dicts.
        """
        data = self._c.request(
            "SYNO.Core.User",
            "list",
            version=1,
            additional=json.dumps(["description", "email", "expired", "2fa_status"]),
        )
        users = data.get("users", [])
        # Normalize for NetBox/Authentik compatibility
        result = []
        for u in users:
            result.append(
                {
                    "name": u.get("name", ""),
                    "email": u.get("email", ""),
                    "description": u.get("description", ""),
                    "expired": u.get("expired", "normal"),
                    "2fa_enabled": u.get("2fa_status", False),
                    # expired values: "normal"=active, "now"=expires today, "expired"=disabled
                    "enabled": u.get("expired", "normal") not in ("expired", "true"),
                }
            )
        return result

    def get(self, name: str) -> dict | None:
        """Get a single user with full details.

        Args:
            name: Username to retrieve.

        Returns:
            Normalized user dict, or None if not found.
        """
        users = self.list_detailed()
        for u in users:
            if u["name"] == name:
                return u
        return None

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
            "SYNO.Core.User",
            "create",
            version=1,
            name=name,
            password=password,
            email=email,
            description=description,
        )

    def delete(self, name: str, dry_run: bool = False) -> dict | None:
        """Delete a user by name.

        Note: DSM API requires name as a JSON array string e.g. '["username"]'.
        Prefer disable() to preserve audit trail unless hard cleanup is needed.

        Args:
            name: Username to delete.
            dry_run: If True, return what would happen without making changes.

        Returns:
            None (or dry_run result dict).

        Raises:
            DSMNotFoundError: If the user does not exist.
        """
        existing = {u["name"] for u in self.list()}
        if name not in existing:
            raise DSMNotFoundError(f"User '{name}' not found", code=408)
        if dry_run:
            return {"changed": True, "dry_run": True, "action": "would_delete", "target": name}
        self._c.request("SYNO.Core.User", "delete", version=1, name=json.dumps([name]))
        return None

    def update(self, name: str, **kwargs: object) -> None:
        """Update user attributes.

        Updatable fields (verified against DSM 7.1.1):
            description (str), email (str), expired (bool as "true"/"false"),
            password (str — triggers password change)

        Args:
            name: Username to update.
            **kwargs: Fields to update.

        Example:
            mgr.update("rune-api", description="Updated description", email="new@example.com")
        """
        self._c.request("SYNO.Core.User", "set", version=1, name=name, **kwargs)

    def disable(self, name: str) -> None:
        """Disable a user (preferred over delete — audit trail preserved).

        Args:
            name: Username to disable.
        """
        self._c.request("SYNO.Core.User", "set", version=1, name=name, expired="true")

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

    def ensure(
        self,
        name: str,
        state: str = "present",
        password: str = "",
        email: str = "",
        description: str = "",
        dry_run: bool = False,
    ) -> dict:
        """Ensure a user exists or is absent — idempotent.

        Mirrors Ansible state semantics:
            state="present" → create if not exists, update description/email if changed
            state="absent"  → delete if exists, no-op if already gone

        Args:
            name: Username.
            state: "present" or "absent".
            password: Required when creating (ignored on update).
            email: Email address.
            description: Human-readable description.
            dry_run: If True, return what would happen without making changes.

        Returns:
            Dict with keys:
              - changed (bool)
              - action (str: created/updated/deleted/noop or would_* prefix for dry_run)
              - dry_run (bool, only when dry_run=True)
              - before/after (dicts, when changed and not noop)
        """
        existing = self.get(name)

        if state == "present":
            if existing is None:
                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_create",
                        "after": {
                            "name": name,
                            "email": email,
                            "description": description,
                        },
                    }
                self.create(name, password=password, email=email, description=description)
                return {
                    "changed": True,
                    "action": "created",
                    "after": {"name": name, "email": email, "description": description},
                }
            else:
                # Check for actual diff
                diff = {}
                if existing.get("description", "") != description:
                    diff["description"] = description
                if existing.get("email", "") != email:
                    diff["email"] = email

                if not diff:
                    return {"changed": False, "action": "noop"}

                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_update",
                        "before": {k: existing.get(k) for k in diff},
                        "after": diff,
                    }
                self.update(name, **diff)
                return {
                    "changed": True,
                    "action": "updated",
                    "before": {k: existing.get(k) for k in diff},
                    "after": diff,
                }

        elif state == "absent":
            if existing is not None:
                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_delete",
                        "before": existing,
                    }
                self._c.request("SYNO.Core.User", "delete", version=1, name=json.dumps([name]))
                return {"changed": True, "action": "deleted", "before": existing}
            return {"changed": False, "action": "noop"}

        else:
            raise ValueError(f"Invalid state '{state}'. Use 'present' or 'absent'.")
