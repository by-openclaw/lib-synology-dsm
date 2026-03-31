"""Synology DSM — share permission (ACL) management.

API: SYNO.Core.Share.Permission (version 1, entry.cgi)

Manages per-user and per-group ACL entries on shared folders.
Wraps and formalises the permission operations previously available
only through ShareManager.set_permission().

Permission values: "read_write", "read_only", "deny", "no_access"
"""

from __future__ import annotations

import builtins
import json
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .client import DSMClient


def _perm_from_flags(entry: dict) -> str:
    """Convert DSM boolean flags to a permission string."""
    if entry.get("is_deny"):
        return "deny"
    if entry.get("is_writable"):
        return "read_write"
    if entry.get("is_readonly"):
        return "read_only"
    return "no_access"


def _flags_from_perm(perm: str) -> dict[str, bool]:
    """Convert a permission string to DSM boolean flags."""
    return {
        "is_writable": perm == "read_write",
        "is_readonly": perm == "read_only",
        "is_deny": perm == "deny",
        "is_custom": False,
    }


class SharePermissionManager:
    """Share permission (ACL) management.

    Provides full ACL lifecycle for Synology shared folders — list,
    set individual, set bulk, and idempotent ensure().

    Uses SYNO.Core.Share.Permission (version 1).
    """

    def __init__(self, client: DSMClient) -> None:
        self._c = client

    def list(self, share: str) -> builtins.list[dict]:
        """Get current permissions for a share.

        Args:
            share: Share name.

        Returns:
            List of permission dicts, each with keys:
            ``name``, ``is_group`` (bool), ``perm`` (str).
        """
        data = self._c.request(
            "SYNO.Core.Share.Permission",
            "list",
            version=1,
            name=share,
            action="load",
            user_group_type="local_user",
        )
        user_entries = cast(list[dict[str, Any]], data.get("items", []))

        data_group = self._c.request(
            "SYNO.Core.Share.Permission",
            "list",
            version=1,
            name=share,
            action="load",
            user_group_type="local_group",
        )
        group_entries = cast(list[dict[str, Any]], data_group.get("items", []))

        result: list[dict] = []
        for entry in user_entries:
            result.append(
                {
                    "name": entry["name"],
                    "is_group": False,
                    "perm": _perm_from_flags(entry),
                }
            )
        for entry in group_entries:
            result.append(
                {
                    "name": entry["name"],
                    "is_group": True,
                    "perm": _perm_from_flags(entry),
                }
            )
        return result

    def set(
        self,
        share: str,
        subject: str,
        perm: str,
        is_group: bool = False,
        dry_run: bool = False,
    ) -> dict:
        """Set permission for one user or group on a share.

        Args:
            share: Share name.
            subject: User or group name.
            perm: Permission level: ``"read_write"``, ``"read_only"``,
                  ``"deny"``, or ``"no_access"``.
            is_group: True if subject is a group.
            dry_run: If True, return what would happen without making changes.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str).
        """
        if dry_run:
            return {
                "changed": True,
                "dry_run": True,
                "action": "would_set",
                "share": share,
                "subject": subject,
                "perm": perm,
            }

        flags = _flags_from_perm(perm)
        entry = {"name": subject, **flags}
        user_group_type = "local_group" if is_group else "local_user"

        self._c.request(
            "SYNO.Core.Share.Permission",
            "set",
            version=1,
            name=share,
            user_group_type=user_group_type,
            permissions=json.dumps([entry]),
        )
        return {"changed": True, "action": "set", "share": share, "subject": subject}

    def set_bulk(
        self,
        share: str,
        permissions: builtins.list[dict],
        dry_run: bool = False,
    ) -> dict:
        """Replace ALL permissions on a share atomically.

        Args:
            share: Share name.
            permissions: List of dicts, each with keys:
                         ``name``, ``is_group`` (bool), ``perm`` (str).
            dry_run: If True, return what would happen without making changes.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str), ``count`` (int).
        """
        if dry_run:
            return {
                "changed": True,
                "dry_run": True,
                "action": "would_set_bulk",
                "share": share,
                "count": len(permissions),
            }

        user_entries: list[dict] = []
        group_entries: list[dict] = []
        for p in permissions:
            flags = _flags_from_perm(p["perm"])
            entry = {"name": p["name"], **flags}
            if p.get("is_group"):
                group_entries.append(entry)
            else:
                user_entries.append(entry)

        if user_entries:
            self._c.request(
                "SYNO.Core.Share.Permission",
                "set",
                version=1,
                name=share,
                user_group_type="local_user",
                permissions=json.dumps(user_entries),
            )
        if group_entries:
            self._c.request(
                "SYNO.Core.Share.Permission",
                "set",
                version=1,
                name=share,
                user_group_type="local_group",
                permissions=json.dumps(group_entries),
            )

        return {
            "changed": True,
            "action": "set_bulk",
            "share": share,
            "count": len(permissions),
        }

    def ensure(
        self,
        share: str,
        subject: str,
        perm: str,
        is_group: bool = False,
        state: str = "present",
        dry_run: bool = False,
    ) -> dict:
        """Ensure one permission entry matches desired state — idempotent.

        Args:
            share: Share name.
            subject: User or group name.
            perm: Desired permission: ``"read_write"``, ``"read_only"``,
                  ``"deny"``, or ``"no_access"``.
            is_group: True if subject is a group.
            state: ``"present"`` to set perm if missing or different;
                   ``"absent"`` to remove (set to ``"no_access"``) if present.
            dry_run: If True, return what would happen without making changes.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str).

        Raises:
            ValueError: If ``state`` is not ``"present"`` or ``"absent"``.
        """
        if state not in ("present", "absent"):
            raise ValueError(f"Invalid state '{state}'. Use 'present' or 'absent'.")

        current_perms = self.list(share)
        existing = {(p["name"], p["is_group"]): p["perm"] for p in current_perms}
        current_perm = existing.get((subject, is_group))

        if state == "present":
            if current_perm == perm:
                return {"changed": False, "action": "noop"}

            if dry_run:
                return {
                    "changed": True,
                    "dry_run": True,
                    "action": "would_set",
                    "before": current_perm,
                    "after": perm,
                }

            self.set(share, subject, perm, is_group=is_group)
            return {
                "changed": True,
                "action": "set",
                "before": current_perm,
                "after": perm,
            }

        else:  # absent
            if current_perm is None or current_perm == "no_access":
                return {"changed": False, "action": "noop"}

            if dry_run:
                return {
                    "changed": True,
                    "dry_run": True,
                    "action": "would_remove",
                    "before": current_perm,
                }

            self.set(share, subject, "no_access", is_group=is_group)
            return {
                "changed": True,
                "action": "removed",
                "before": current_perm,
            }
