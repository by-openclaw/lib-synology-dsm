"""Synology DSM — shared folder management.

API: SYNO.Core.Share (version 1, entry.cgi)
NFS: SYNO.Core.Share.NFS (version 1, entry.cgi)
Permissions: SYNO.Core.Share.Permission (version 1, entry.cgi)
Compound: SYNO.Entry.Request (version 1, entry.cgi)

Verified against DSM 7.1.1-42962 Update 9 (nas01).

SHARE CREATE — REQUIRED FORMAT:
    DSM 7.x requires create params wrapped in a 'shareinfo' JSON object,
    NOT as flat POST params. Flat params return 403 regardless of permissions.

    Correct shape (discovered via F12 DevTools on DSM WebUI):
        shareinfo={"name":"SHARENAME","vol_path":"/volume1","desc":"","name_org":""}

    After create, permissions must be set separately via SYNO.Entry.Request
    compound call (batching Share.Permission.set + Share.set).

NFS Permission Notes:
    SYNO.Core.Share.NFS.set replaces the entire NFS rule list for a share.
    SYNO.Core.FileServ.NFS returns the global NFS service config (not per-share rules).
    To get per-share NFS rules: use SYNO.Core.Share.NFS.get (requires admin).
"""

from __future__ import annotations

import json

from .client import DSMClient


class ShareManager:
    """CRUD operations for Synology shared folders."""

    def __init__(self, client: DSMClient):
        self._c = client

    def list(self, additional: list[str] | None = None) -> list[dict]:
        """List all shared folders.

        Args:
            additional: Optional list of extra fields to include.
                Common values: 'share_quota', 'valid_users', 'hidden',
                'is_aclmode', 'encryption'.

        Returns:
            List of share dicts with at minimum: name, vol_path, desc.
        """
        extra = json.dumps(additional or [])
        data = self._c.request("SYNO.Core.Share", "list", version=1, additional=extra)
        return data.get("shares", [])

    def create(self, name: str, volume_path: str = "/volume1", description: str = "") -> dict:
        """Create a shared folder.

        Uses the 'shareinfo' JSON object format required by DSM 7.x.
        Flat POST params return 403 — this is the correct shape discovered via
        browser DevTools (F12) on the DSM WebUI.

        Requires: administrators group membership + DSM + FileStation app enabled.

        Args:
            name: Share name (alphanumeric, hyphens, underscores).
            volume_path: Volume mount point (e.g. '/volume1').
            description: Human-readable description. Always set.

        Returns:
            Dict with share info from the API.
        """
        shareinfo = json.dumps({
            "name": name,
            "vol_path": volume_path,
            "desc": description,
            "name_org": "",
        })
        return self._c.request(
            "SYNO.Core.Share",
            "create",
            version=1,
            name=name,
            shareinfo=shareinfo,
        )

    def create_with_permissions(
        self,
        name: str,
        volume_path: str = "/volume1",
        description: str = "",
        owner: str = "rune-api",
    ) -> dict:
        """Create a shared folder and set owner permissions in one compound call.

        Uses SYNO.Entry.Request to batch Permission.set + Share.set after create.
        This mirrors the exact sequence the DSM WebUI performs.

        Args:
            name: Share name.
            volume_path: Volume mount point.
            description: Human-readable description.
            owner: Username to grant RW access.

        Returns:
            Dict with keys: create (share create result), permissions (compound result).
        """
        # Step 1: Create
        create_result = self.create(name, volume_path=volume_path, description=description)

        # Step 2: Set permissions via compound request
        compound = json.dumps([
            {
                "api": "SYNO.Core.Share.Permission",
                "method": "set",
                "version": 1,
                "name": name,
                "user_group_type": "local_user",
                "permissions": [
                    {
                        "name": owner,
                        "is_readonly": False,
                        "is_writable": True,
                        "is_deny": False,
                        "is_custom": False,
                    }
                ],
            },
            {
                "api": "SYNO.Core.Share",
                "method": "set",
                "version": 1,
                "name": name,
                "shareinfo": json.dumps({
                    "name": name,
                    "vol_path": volume_path,
                    "desc": description,
                    "encryption": False,
                    "enc_passwd": "",
                }),
            },
        ])
        perm_result = self._c.request(
            "SYNO.Entry.Request",
            "request",
            version=1,
            stop_when_error="true",
            mode="sequential",
            compound=compound,
        )
        return {"create": create_result, "permissions": perm_result}

    def update(self, name: str, **kwargs: object) -> None:
        """Update shared folder attributes.

        Requires administrators group membership.

        Updatable fields (verified against DSM 7.1.1):
            desc (str) — description
            hidden (bool as string)
            enable_recycle_bin (bool as string)

        Args:
            name: Share name to update.
            **kwargs: Fields to update.

        Example:
            mgr.update("by-gitlab", desc="GitLab storage — production data")
        """
        self._c.request("SYNO.Core.Share", "set", version=1, name=name, **kwargs)

    def delete(self, name: str) -> None:
        """Delete a shared folder.

        Requires administrators group membership.

        Args:
            name: Share name to delete.
        """
        self._c.request("SYNO.Core.Share", "delete", version=1, name=name)

    def set_permission(
        self,
        share: str,
        username: str,
        writable: bool = True,
        readonly: bool = False,
        deny: bool = False,
    ) -> dict:
        """Set user permission on a shared folder.

        Args:
            share: Share name.
            username: Local DSM username.
            writable: Grant read-write access.
            readonly: Grant read-only access.
            deny: Explicitly deny access.

        Returns:
            API response dict.
        """
        return self._c.request(
            "SYNO.Core.Share.Permission",
            "set",
            version=1,
            name=share,
            user_group_type="local_user",
            permissions=json.dumps([{
                "name": username,
                "is_readonly": readonly,
                "is_writable": writable,
                "is_deny": deny,
                "is_custom": False,
            }]),
        )

    def get_nfs_rules(self, share: str) -> list[dict]:
        """Get NFS rules for a share.

        Uses SYNO.Core.FileServ.NFS.SharePrivilege.load (correct API on DS1513+ DSM 7.x).
        SYNO.Core.Share.NFS does not exist on this hardware.

        Args:
            share: Share name.

        Returns:
            List of NFS rule dicts.
        """
        data = self._c.request(
            "SYNO.Core.FileServ.NFS.SharePrivilege",
            "load",
            version=1,
            sharename=share,
        )
        return data.get("rule", [])

    def set_nfs_permission(
        self,
        share: str,
        hostname: str,
        rw: bool = True,
        async_io: bool = True,
        root_squash: str = "root",
    ) -> dict:
        """Set NFS permission for a host on a share.

        Uses SYNO.Core.FileServ.NFS.SharePrivilege.save (correct API on DS1513+ DSM 7.x).
        WARNING: This REPLACES the entire NFS rule list for the share.
        Use get_nfs_rules() first if you need to preserve existing rules.

        Args:
            share: Share name.
            hostname: Client hostname or CIDR (e.g. '10.6.224.105' or '10.6.0.0/20').
            rw: True for read-write, False for read-only.
            async_io: Enable async I/O (better performance).
            root_squash: Squash mode — 'root' (root_squash), 'all', 'no_root_squash'.

        Returns:
            API response dict.
        """
        rule = [{
            "async": async_io,
            "client": hostname,
            "crossmnt": False,
            "insecure": False,
            "privilege": "rw" if rw else "ro",
            "root_squash": root_squash,
            "security_flavor": {
                "kerberos": False,
                "kerberos_integrity": False,
                "kerberos_privacy": False,
                "sys": True,
            },
        }]
        return self._c.request(
            "SYNO.Core.FileServ.NFS.SharePrivilege",
            "save",
            version=1,
            sharename=share,
            rule=json.dumps(rule),
        )

    def ensure(
        self,
        name: str,
        state: str = "present",
        volume_path: str = "/volume1",
        description: str = "",
    ) -> dict:
        """Ensure a shared folder exists or is absent — idempotent.

        state="present" → create if not exists, update description if exists
        state="absent"  → delete if exists, no-op if already gone

        Args:
            name: Share name.
            state: "present" or "absent".
            volume_path: Volume mount point (used only on create).
            description: Human-readable description.

        Returns:
            Dict with keys: changed (bool), action (str).
        """
        existing = {s["name"] for s in self.list()}

        if state == "present":
            if name not in existing:
                self.create(name, volume_path=volume_path, description=description)
                return {"changed": True, "action": "created"}
            else:
                self.update(name, desc=description)
                return {"changed": True, "action": "updated"}

        elif state == "absent":
            if name in existing:
                self.delete(name)
                return {"changed": True, "action": "deleted"}
            return {"changed": False, "action": "noop"}

        else:
            raise ValueError(f"Invalid state '{state}'. Use 'present' or 'absent'.")
