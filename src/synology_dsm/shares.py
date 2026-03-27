"""Synology DSM — shared folder management.

API: SYNO.Core.Share (version 1, entry.cgi)
NFS: SYNO.Core.Share.NFS (version 1, entry.cgi)

Verified against DSM 7.1.1-42962 Update 9 (nas01).

PERMISSION REQUIREMENT:
    create() and delete() require the API user to be in the 'administrators' group
    on the NAS. If the account is not an administrator, create/delete return HTTP 403.
    The list() method works with any authenticated user.

    To add rune-api to administrators:
        DSM Control Panel → User & Group → Group → administrators → Edit → Members → Add rune-api

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
                Defaults to empty (basic info only).

        Returns:
            List of share dicts with at minimum: name, vol_path, desc, encryption, hidden.
        """
        extra = json.dumps(additional or [])
        data = self._c.request("SYNO.Core.Share", "list", version=1, additional=extra)
        return data.get("shares", [])

    def create(self, name: str, volume_path: str = "/volume1", description: str = "") -> dict:
        """Create a shared folder.

        Requires the API user to be in the 'administrators' group.
        Returns HTTP 403 / DSM error if the account lacks that privilege.

        Args:
            name: Share name (alphanumeric, hyphens, underscores).
            volume_path: Volume mount point (e.g. '/volume1').
            description: Human-readable description. Always set — missing descriptions
                are flagged as a security gap during audits.

        Returns:
            Dict with share info from the API.
        """
        return self._c.request(
            "SYNO.Core.Share",
            "create",
            version=1,
            name=name,
            vol_path=volume_path,
            desc=description,
            enable_recycle_bin="false",
            encryption=0,
        )

    def update(self, name: str, **kwargs: object) -> None:
        """Update shared folder attributes.

        Requires the API user to be in the 'administrators' group.

        Updatable fields (verified against DSM 7.1.1):
            desc (str) — description
            hidden (bool as string "true"/"false")
            enable_recycle_bin (bool as string)

        Args:
            name: Share name to update.
            **kwargs: Fields to update (use 'desc' not 'description' for shares).

        Example:
            mgr.update("by-gitlab", desc="GitLab storage — production data")
        """
        self._c.request("SYNO.Core.Share", "set", version=1, name=name, **kwargs)

    def delete(self, name: str) -> None:
        """Delete a shared folder.

        Requires the API user to be in the 'administrators' group.

        Args:
            name: Share name to delete.
        """
        self._c.request("SYNO.Core.Share", "delete", version=1, name=name)

    def set_nfs_permission(
        self,
        share: str,
        hostname: str,
        rw: bool = True,
        squash: str = "no_squash",
        async_io: bool = True,
    ) -> dict:
        """Set NFS permission for a host on a share.

        WARNING: This REPLACES the entire NFS rule list for the share.
        Use get_nfs_rules() first if you need to preserve existing rules.

        Requires admin privileges.

        Args:
            share: Share name.
            hostname: Hostname or CIDR (e.g. '10.6.0.0/20' or 'trustedhost').
            rw: True for read-write, False for read-only.
            squash: NFS squash mode. Options: 'no_squash', 'root_squash',
                'all_squash'. Default: 'no_squash'.
            async_io: Enable async I/O (better performance, slight durability trade-off).

        Returns:
            API response dict.
        """
        privilege = "rw" if rw else "ro"
        nfs_rule = {
            "hostname": hostname,
            "privilege": privilege,
            "squash": squash,
            "async": async_io,
            "anonuid": -2,
            "anongid": -2,
        }
        return self._c.request(
            "SYNO.Core.Share.NFS",
            "set",
            version=1,
            name=share,
            nfs_rules=json.dumps([nfs_rule]),
        )

    def get_nfs_rules(self, share: str) -> list[dict]:
        """Get NFS rules for a share.

        Args:
            share: Share name.

        Returns:
            List of NFS rule dicts.
        """
        data = self._c.request("SYNO.Core.Share.NFS", "get", version=1, name=share)
        return data.get("nfs_rules", data.get("rules", []))
