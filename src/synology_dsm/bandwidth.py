"""Synology DSM — bandwidth control (traffic throttling per user/group).

API: SYNO.Core.BandwidthControl (version 2, entry.cgi)

Verified payload observed via Chrome DevTools F12 on DSM 7.1.1-42962 Update 9:
    api=SYNO.Core.BandwidthControl
    method=get
    version=2
    name=administrators
    owner_type=local_group

owner_type switches between "local_group" and "local_user".
version=2 is required — version=1 returns error 102 on DSM 7.x.

Write operations (set bandwidth limits) require additional F12 capture —
not yet verified against live DSM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import DSMClient

#: Valid owner types for bandwidth queries.
_OWNER_TYPES = frozenset({"local_user", "local_group"})


class BandwidthManager:
    """Bandwidth control (traffic throttling) queries for DSM users and groups.

    Wraps SYNO.Core.BandwidthControl — returns upload/download speed limits
    configured per user or group in DSM Control Panel → Network → Traffic Control.

    Note:
        DSM must have Traffic Control enabled for limits to be active.
        This manager is read-only — write operations not yet verified.
    """

    def __init__(self, client: DSMClient) -> None:
        """Initialise the manager with an authenticated DSMClient.

        Args:
            client: An authenticated :class:`DSMClient` instance.
        """
        self._c = client

    def get_group_limit(self, group_name: str) -> dict:
        """Get bandwidth limits for a group.

        Args:
            group_name: DSM group name (e.g. ``"administrators"``).

        Returns:
            Bandwidth limit dict. Fields vary by DSM version but typically
            include:

            - ``upload_limit`` (int): Upload cap in KB/s. ``0`` = unlimited.
            - ``download_limit`` (int): Download cap in KB/s. ``0`` = unlimited.
            - ``protocol_list`` (list): Per-protocol limit entries.

        Example::

            bw = BandwidthManager(client)
            limits = bw.get_group_limit("svc-automation")
            up   = limits.get("upload_limit", 0)
            down = limits.get("download_limit", 0)
            print(f"Up: {up or 'unlimited'} KB/s  Down: {down or 'unlimited'} KB/s")
        """
        return self._get("local_group", group_name)

    def get_user_limit(self, username: str) -> dict:
        """Get bandwidth limits for a user.

        Args:
            username: DSM username (e.g. ``"alice"``).

        Returns:
            Bandwidth limit dict (same shape as :meth:`get_group_limit`).
        """
        return self._get("local_user", username)

    def get_limit(self, name: str, owner_type: str) -> dict:
        """Get bandwidth limits for a named user or group.

        Lower-level method — prefer :meth:`get_user_limit` or
        :meth:`get_group_limit` for clarity.

        Args:
            name: DSM username or group name.
            owner_type: ``"local_user"`` or ``"local_group"``.

        Returns:
            Bandwidth limit dict from the API.

        Raises:
            ValueError: If ``owner_type`` is not a recognised value.
        """
        if owner_type not in _OWNER_TYPES:
            raise ValueError(
                f"Invalid owner_type '{owner_type}'. Use 'local_user' or 'local_group'."
            )
        return self._get(owner_type, name)

    def _get(self, owner_type: str, name: str) -> dict:
        """Execute the SYNO.Core.BandwidthControl get request.

        Args:
            owner_type: ``"local_user"`` or ``"local_group"``.
            name: DSM username or group name.

        Returns:
            Raw API response dict.
        """
        return self._c.request(
            "SYNO.Core.BandwidthControl",
            "get",
            version=2,
            name=name,
            owner_type=owner_type,
        )
