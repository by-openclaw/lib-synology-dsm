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

import builtins
import json
from typing import Any, cast

from .client import DSMClient


class ShareManager:
    """CRUD operations for Synology shared folders."""

    def __init__(self, client: DSMClient) -> None:
        """Initialise the manager with an authenticated DSMClient.

        Args:
            client: An authenticated :class:`DSMClient` instance.
        """
        self._c = client

    def list(self, additional: list[str] | None = None) -> builtins.list[dict]:
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
        return cast(builtins.list[dict[Any, Any]], data.get("shares", []))

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
        shareinfo = json.dumps(
            {
                "name": name,
                "vol_path": volume_path,
                "desc": description,
                "name_org": "",
            }
        )
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
        owner_user: str | None = None,
        owner_group: str | None = None,
        nfs_client: str | None = None,
        nfs_rw: bool = True,
    ) -> dict:
        """Create a shared folder with user/group permissions and optional NFS rule.

        Mirrors the exact sequence the DSM WebUI performs (confirmed via F12 DevTools):
        1. Create share (shareinfo JSON with name_org)
        2. Set user permissions via compound request
        3. Set group permissions via compound request (if owner_group provided)
        4. Set NFS rule via compound request (if nfs_client provided)

        Args:
            name: Share name.
            volume_path: Volume mount point (e.g. '/volume1').
            description: Human-readable description.
            owner_user: Local DSM username to grant RW access.
            owner_group: Local DSM group to grant RW access.
            nfs_client: NFS client hostname or IP to grant RW access.
            nfs_rw: True for read-write NFS, False for read-only.

        Returns:
            Dict with keys: create, user_permissions, group_permissions, nfs.
        """
        shareinfo_obj = {
            "name": name,
            "vol_path": volume_path,
            "desc": description,
            "encryption": False,
            "enc_passwd": "",
        }

        # Step 1: Create
        create_result = self.create(name, volume_path=volume_path, description=description)

        result = {
            "create": create_result,
            "user_permissions": None,
            "group_permissions": None,
            "nfs": None,
        }

        # Step 2: User permissions
        if owner_user:
            compound = json.dumps(
                [
                    {
                        "api": "SYNO.Core.Share.Permission",
                        "method": "set",
                        "version": 1,
                        "name": name,
                        "user_group_type": "local_user",
                        "permissions": [
                            {
                                "name": owner_user,
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
                        "shareinfo": shareinfo_obj,
                    },
                ]
            )
            result["user_permissions"] = self._c.request(
                "SYNO.Entry.Request",
                "request",
                version=1,
                stop_when_error="true",
                mode="sequential",
                compound=compound,
            )

        # Step 3: Group permissions
        if owner_group:
            compound = json.dumps(
                [
                    {
                        "api": "SYNO.Core.Share.Permission",
                        "method": "set",
                        "version": 1,
                        "name": name,
                        "user_group_type": "local_group",
                        "permissions": [
                            {
                                "name": owner_group,
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
                        "shareinfo": shareinfo_obj,
                    },
                ]
            )
            result["group_permissions"] = self._c.request(
                "SYNO.Entry.Request",
                "request",
                version=1,
                stop_when_error="true",
                mode="sequential",
                compound=compound,
            )

        # Step 4: NFS rule
        if nfs_client:
            nfs_rule = [
                {
                    "client": nfs_client,
                    "privilege": "rw" if nfs_rw else "ro",
                    "root_squash": "root",
                    "async": True,
                    "insecure": False,
                    "crossmnt": False,
                    "security_flavor": {
                        "kerberos": False,
                        "kerberos_integrity": False,
                        "kerberos_privacy": False,
                        "sys": True,
                    },
                }
            ]
            compound = json.dumps(
                [
                    {
                        "api": "SYNO.Core.FileServ.NFS.SharePrivilege",
                        "method": "save",
                        "version": 1,
                        "share_name": name,
                        "rule": nfs_rule,
                    },
                    {
                        "api": "SYNO.Core.Share",
                        "method": "set",
                        "version": 1,
                        "name": name,
                        "shareinfo": shareinfo_obj,
                    },
                ]
            )
            result["nfs"] = self._c.request(
                "SYNO.Entry.Request",
                "request",
                version=1,
                stop_when_error="true",
                mode="sequential",
                compound=compound,
            )

        return result

    def update(self, name: str, **kwargs: object) -> dict:
        """Update shared folder attributes.

        Requires administrators group membership.

        Updatable fields (verified against DSM 7.1.1):
            desc (str) — description
            hidden (bool as string)
            enable_recycle_bin (bool as string)

        Args:
            name: Share name to update.
            **kwargs: Fields to update.

        Returns:
            Dict with keys: ``changed`` (bool), ``action`` (str), ``target`` (str).

        Example:
            mgr.update("by-gitlab", desc="GitLab storage — production data")
        """
        self._c.request("SYNO.Core.Share", "set", version=1, name=name, **kwargs)
        return {"changed": True, "action": "updated", "target": name}

    def delete(self, name: str, dry_run: bool = False) -> dict | None:
        """Delete a shared folder.

        Requires administrators group membership.

        Args:
            name: Share name to delete.
            dry_run: If True, return what would happen without making changes.

        Returns:
            None (or dry_run result dict).
        """
        if dry_run:
            return {"changed": True, "dry_run": True, "action": "would_delete", "target": name}
        self._c.request("SYNO.Core.Share", "delete", version=1, name=name)
        return None

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
            permissions=json.dumps(
                [
                    {
                        "name": username,
                        "is_readonly": readonly,
                        "is_writable": writable,
                        "is_deny": deny,
                        "is_custom": False,
                    }
                ]
            ),
        )

    def get_nfs_rules(self, share: str) -> builtins.list[dict]:
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
            share_name=share,
        )
        return cast(builtins.list[dict[Any, Any]], data.get("rule", []))

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
        rule = [
            {
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
            }
        ]
        return self._c.request(
            "SYNO.Core.FileServ.NFS.SharePrivilege",
            "save",
            version=1,
            share_name=share,
            rule=json.dumps(rule),
        )

    def list_shares_for_group(
        self,
        group_name: str,
        share_type: builtins.list[str] | None = None,
        additional: builtins.list[str] | None = None,
    ) -> builtins.list[dict]:
        """List all shares accessible by a specific group.

        Uses ``SYNO.Core.Share.Permission list_by_group`` — the API observed
        in Chrome DevTools F12 when opening Group properties in DSM Control Panel.

        Args:
            group_name: DSM group name (e.g. ``"administrators"``).
            share_type: Share types to include. Defaults to all standard types:
                ``["dec", "local", "usb", "sata", "cluster", "c2", "cold_storage"]``.
                Pass a subset to filter (e.g. ``["local"]`` for internal shares only).
            additional: Extra fields to include per share.
                Common values: ``"hidden"``, ``"encryption"``, ``"is_aclmode"``.

        Returns:
            List of share permission dicts. Each dict contains at minimum:

            - ``name`` (str): Share name.
            - ``is_writable`` (bool): Group has write access.
            - ``is_readonly`` (bool): Group has read-only access.
            - ``is_deny`` (bool): Group is explicitly denied.

        Example::

            shares = ShareManager(client)
            for s in shares.list_shares_for_group("svc-automation"):
                access = "rw" if s["is_writable"] else ("ro" if s["is_readonly"] else "deny")
                print(f"  {s['name']}: {access}")
        """
        _share_type = share_type or ["dec", "local", "usb", "sata", "cluster", "c2", "cold_storage"]
        params: dict[str, object] = {
            "name": group_name,
            "user_group_type": "local_group",
            "share_type": json.dumps(_share_type),
        }
        if additional:
            params["additional"] = json.dumps(additional)

        data = self._c.request(
            "SYNO.Core.Share.Permission",
            "list_by_group",
            version=1,
            **params,
        )
        return cast(builtins.list[dict[Any, Any]], data.get("shares", []))

    def ensure(
        self,
        name: str,
        state: str = "present",
        volume_path: str = "/volume1",
        description: str = "",
        dry_run: bool = False,
    ) -> dict:
        """Ensure a shared folder exists or is absent — idempotent.

        state="present" → create if not exists, update description if changed
        state="absent"  → delete if exists, no-op if already gone

        Args:
            name: Share name.
            state: "present" or "absent".
            volume_path: Volume mount point (used only on create).
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
        existing_map = {s["name"]: s for s in existing_list}

        if state == "present":
            if name not in existing_map:
                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_create",
                        "after": {
                            "name": name,
                            "vol_path": volume_path,
                            "description": description,
                        },
                    }
                self.create(name, volume_path=volume_path, description=description)
                return {
                    "changed": True,
                    "action": "created",
                    "after": {"name": name, "vol_path": volume_path, "description": description},
                }
            else:
                current = existing_map[name]
                current_desc = current.get("desc", current.get("description", ""))
                diff = {}
                if current_desc != description:
                    diff["desc"] = description

                if not diff:
                    return {"changed": False, "action": "noop"}

                if dry_run:
                    return {
                        "changed": True,
                        "dry_run": True,
                        "action": "would_update",
                        "before": {"desc": current_desc},
                        "after": diff,
                    }
                self.update(name, **diff)
                return {
                    "changed": True,
                    "action": "updated",
                    "before": {"desc": current_desc},
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
                self.delete(name)
                return {"changed": True, "action": "deleted", "before": existing_map[name]}
            return {"changed": False, "action": "noop"}

        else:
            raise ValueError(f"Invalid state '{state}'. Use 'present' or 'absent'.")
