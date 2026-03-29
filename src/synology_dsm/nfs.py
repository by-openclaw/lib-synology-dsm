"""Synology DSM — NFS management.

Uses SYNO.Core.FileServ.NFS.SharePrivilege — the correct API on DSM 7.x.
SYNO.Core.Share.NFS does NOT exist on DSM 7.x and will return error 102.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import DSMClient


class NFSManager:
    """NFS export management per share.

    Manages NFS export rules for Synology shared folders.
    Uses SYNO.Core.FileServ.NFS.SharePrivilege (DSM 7.x).
    """

    def __init__(self, client: DSMClient) -> None:
        self._c = client

    def get_rules(self, share_name: str) -> list[dict]:
        """Get NFS rules for a share.

        Args:
            share_name: Share name to query.

        Returns:
            List of NFS rule dicts. Each dict contains: client, privilege,
            root_squash, async, insecure, crossmnt, security_flavor.
        """
        data = self._c.request(
            "SYNO.Core.FileServ.NFS.SharePrivilege",
            "load",
            version=1,
            share_name=share_name,
        )
        return data.get("rule", [])

    def set_rules(self, share_name: str, rules: list[dict], dry_run: bool = False) -> dict:
        """Replace all NFS rules for a share.

        Overwrites all existing rules. Pass ``rules=[]`` to remove all NFS access.

        Args:
            share_name: Share name to update.
            rules: List of NFS rule dicts. Each must contain at minimum:
                   ``client`` (IP or CIDR), ``privilege`` (``"rw"`` or ``"ro"``).
            dry_run: If True, return what would be applied without making changes.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str), optionally ``dry_run``.
        """
        if dry_run:
            return {
                "changed": True,
                "dry_run": True,
                "action": "would_set_rules",
                "share": share_name,
                "rules": rules,
            }
        self._c.request(
            "SYNO.Core.FileServ.NFS.SharePrivilege",
            "save",
            version=1,
            share_name=share_name,
            rule=json.dumps(rules),
        )
        return {"changed": True, "action": "rules_set", "share": share_name}

    def ensure(
        self,
        share_name: str,
        hostname: str,
        state: str = "present",
        rw: bool = True,
        root_squash: str = "root",
        async_io: bool = True,
        dry_run: bool = False,
    ) -> dict:
        """Ensure an NFS rule for a specific client is present or absent on a share.

        Fetches current rules, diffs against desired state, and only calls
        the API if a change is needed (idempotent).

        Args:
            share_name:  Share name to manage.
            hostname:    Client IP or CIDR to allow/deny (e.g. ``"192.168.1.0/24"``).
            state:       ``"present"`` to add/update the rule, ``"absent"`` to remove it.
            rw:          Read-write access (True) or read-only (False). Only for ``state="present"``.
            root_squash: Root squash mode: ``"root"`` (default), ``"all"``, or ``"no_root_squash"``.
            async_io:    Enable async I/O (True, default).
            dry_run:     If True, return what would change without calling the API.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str), and optionally
            ``dry_run``, ``before``, ``after``.

        Raises:
            ValueError: If ``state`` is not ``"present"`` or ``"absent"``.
        """
        if state not in ("present", "absent"):
            raise ValueError(f"Invalid state '{state}'. Use 'present' or 'absent'.")

        current_rules: list[dict] = self.get_rules(share_name)
        existing = {r.get("client"): r for r in current_rules}

        if state == "present":
            desired = {
                "client": hostname,
                "privilege": "rw" if rw else "ro",
                "root_squash": root_squash,
                "async": async_io,
                "insecure": False,
                "crossmnt": False,
                "security_flavor": {
                    "sys": True,
                    "kerberos": False,
                    "kerberos_integrity": False,
                    "kerberos_privacy": False,
                },
            }

            if hostname in existing:
                current = existing[hostname]
                diff = {
                    k: desired[k]
                    for k in ("privilege", "root_squash", "async")
                    if current.get(k) != desired[k]
                }
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

                updated_rules = [
                    desired if r.get("client") == hostname else r for r in current_rules
                ]
                self.set_rules(share_name, updated_rules)
                return {
                    "changed": True,
                    "action": "updated",
                    "before": {k: current.get(k) for k in diff},
                    "after": diff,
                }
            else:
                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_create",
                        "after": desired,
                    }
                self.set_rules(share_name, [*current_rules, desired])
                return {"changed": True, "action": "created", "after": desired}

        else:  # absent
            if hostname not in existing:
                return {"changed": False, "action": "noop"}

            if dry_run:
                return {
                    "changed": True,
                    "dry_run": True,
                    "action": "would_delete",
                    "before": existing[hostname],
                }

            updated_rules = [r for r in current_rules if r.get("client") != hostname]
            self.set_rules(share_name, updated_rules)
            return {"changed": True, "action": "deleted", "before": existing[hostname]}
