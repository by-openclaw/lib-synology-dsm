"""Synology DSM — NFS management.

Uses SYNO.Core.FileServ.NFS.SharePrivilege — the correct API on DSM 7.x.
SYNO.Core.Share.NFS does NOT exist on DSM 7.x and will return error 102.
"""

from __future__ import annotations
from .client import DSMClient


class NFSManager:
    """NFS export management per share."""

    def __init__(self, client: DSMClient):
        self._c = client

    def get_rules(self, share_name: str) -> list[dict]:
        """Get NFS rules for a share.

        Args:
            share_name: Share name to query.

        Returns:
            List of NFS rule dicts.
        """
        data = self._c.request(
            "SYNO.Core.FileServ.NFS.SharePrivilege",
            "load",
            version=1,
            share_name=share_name,
        )
        return data.get("rule", [])
