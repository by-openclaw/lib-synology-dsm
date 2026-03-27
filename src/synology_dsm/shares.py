"""Synology DSM — shared folder management."""
from __future__ import annotations
from .client import DSMClient


class ShareManager:
    """CRUD operations for Synology shared folders."""

    def __init__(self, client: DSMClient):
        self._c = client

    def list(self) -> list[dict]:
        """List all shared folders."""
        data = self._c.request("SYNO.Core.Share", "list", version=1, additional="[]")
        return data.get("shares", [])

    def create(self, name: str, volume_path: str = "/volume1", description: str = "") -> dict:
        """Create a shared folder."""
        return self._c.request(
            "SYNO.Core.Share", "create", version=1,
            name=name,
            vol_path=volume_path,
            desc=description,
            enable_recycle_bin="false",
            encryption=0,
        )

    def delete(self, name: str) -> None:
        """Delete a shared folder."""
        self._c.request("SYNO.Core.Share", "delete", version=1, name=name)

    def set_nfs_permission(self, share: str, hostname: str, rw: bool = True) -> dict:
        """Set NFS permission for a host on a share."""
        privilege = "rw" if rw else "ro"
        nfs_rule = (
            f'{{"hostname":"{hostname}","privilege":"{privilege}",'
            f'"squash":"no_squash","async":true,"anonuid":-2,"anongid":-2}}'
        )
        return self._c.request(
            "SYNO.Core.Share.NFS", "set", version=1,
            name=share,
            nfs_rules=f"[{nfs_rule}]",
        )
