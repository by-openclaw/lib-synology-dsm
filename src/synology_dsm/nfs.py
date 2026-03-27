"""Synology DSM — NFS management."""

from __future__ import annotations
from .client import DSMClient


class NFSManager:
    """NFS export management."""

    def __init__(self, client: DSMClient):
        self._c = client

    def get_rules(self, share: str) -> list[dict]:
        """Get NFS rules for a share."""
        data = self._c.request("SYNO.Core.Share.NFS", "get", version=1, name=share)
        return data.get("nfs_rules", [])
