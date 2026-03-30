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

Write (set bandwidth) — verified via curl on DSM 7.1.1:
    api=SYNO.Core.BandwidthControl
    method=set
    version=1       (version=2 returns error 103 on DSM 7.1.1)
    bandwidths=<JSON-stringified array of bandwidth objects>

Transport is form-encoded POST — NOT JSON body.
Auth: _sid as form field.

policy values:
    "disabled"  → no limit (unlimited — row exists but inactive)
    "enabled"   → flat rate active (upload_result/download_result = effective KB/s)
    "scheduled" → time-based using schedule_plan + limit_1/limit_2
    "group"     → inherit group settings

schedule_plan: 168-char string (7 days × 24 hours).
    "1" = Speed limit 1 active, "2" = Speed limit 2 active, "0" = no limit.
    Order: Sun[0-23], Mon[0-23], …, Sat[0-23].

Known protocols: FileStation, FTP, NetworkBackup, SFTP, NFS, WebDAV, iSCSI, Rsync
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import DSMClient

#: Valid owner types for bandwidth queries.
_OWNER_TYPES = frozenset({"local_user", "local_group"})

#: Valid bandwidth policy values.
_POLICIES = frozenset({"disabled", "enabled", "scheduled", "group", "notexist"})

#: Default schedule plan — all hours use Speed limit 1.
_DEFAULT_SCHEDULE = "1" * 168


class BandwidthManager:
    """Bandwidth control (traffic throttling) for DSM users and groups.

    Wraps SYNO.Core.BandwidthControl — read and write upload/download speed
    limits configured per user or group in DSM Control Panel → Network →
    Traffic Control.

    Note:
        DSM must have Traffic Control enabled for limits to be active.
    """

    def __init__(self, client: DSMClient) -> None:
        """Initialise the manager with an authenticated DSMClient.

        Args:
            client: An authenticated :class:`DSMClient` instance.
        """
        self._c = client

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

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

    def get(self, name: str, owner_type: str) -> list[dict]:
        """Get per-protocol bandwidth objects for a user or group.

        Args:
            name: DSM username or group name.
            owner_type: ``"local_user"`` or ``"local_group"``.

        Returns:
            List of per-protocol bandwidth dicts from the API
            (``bandwidths`` key in the response).

        Raises:
            ValueError: If ``owner_type`` is not a recognised value.
        """
        if owner_type not in _OWNER_TYPES:
            raise ValueError(
                f"Invalid owner_type '{owner_type}'. Use 'local_user' or 'local_group'."
            )
        data = self._c.request(
            "SYNO.Core.BandwidthControl",
            "get",
            version=2,
            name=name,
            owner_type=owner_type,
        )
        return data.get("bandwidths", [])  # type: ignore[no-any-return]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def set(
        self,
        name: str,
        owner_type: str,
        bandwidths: list[dict],
        dry_run: bool = False,
    ) -> dict:
        """Set bandwidth limits (multiple protocols at once).

        Args:
            name: DSM username or group name.
            owner_type: ``"local_user"`` or ``"local_group"``.
            bandwidths: List of bandwidth objects to set.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.

        Raises:
            ValueError: If ``owner_type`` is not a recognised value.
        """
        if owner_type not in _OWNER_TYPES:
            raise ValueError(
                f"Invalid owner_type '{owner_type}'. Use 'local_user' or 'local_group'."
            )
        result: dict = {"changed": True, "action": "set"}
        if dry_run:
            result["dry_run"] = True
            return result
        self._c.request(
            "SYNO.Core.BandwidthControl",
            "set",
            version=1,
            bandwidths=json.dumps(bandwidths),
        )
        return result

    def set_user(
        self,
        username: str,
        protocol: str,
        policy: str = "enabled",
        upload_limit_1: int = 0,
        download_limit_1: int = 0,
        upload_limit_2: int = 0,
        download_limit_2: int = 0,
        schedule_plan: str = _DEFAULT_SCHEDULE,
        dry_run: bool = False,
    ) -> dict:
        """Set bandwidth limit for a single user+protocol combination.

        Args:
            username: DSM username.
            protocol: Protocol name (e.g. ``"FileStation"``, ``"FTP"``).
            policy: ``"disabled"``, ``"enabled"``, ``"scheduled"``, or ``"group"``.
            upload_limit_1: Upload speed limit 1 in KB/s.
            download_limit_1: Download speed limit 1 in KB/s.
            upload_limit_2: Upload speed limit 2 in KB/s (for scheduled mode).
            download_limit_2: Download speed limit 2 in KB/s (for scheduled mode).
            schedule_plan: 168-char schedule string.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.

        Raises:
            ValueError: If ``policy`` is not a recognised value.
        """
        return self._set_single(
            name=username,
            owner_type="local_user",
            protocol=protocol,
            policy=policy,
            upload_limit_1=upload_limit_1,
            download_limit_1=download_limit_1,
            upload_limit_2=upload_limit_2,
            download_limit_2=download_limit_2,
            schedule_plan=schedule_plan,
            dry_run=dry_run,
        )

    def set_group(
        self,
        group_name: str,
        protocol: str,
        policy: str = "enabled",
        upload_limit_1: int = 0,
        download_limit_1: int = 0,
        upload_limit_2: int = 0,
        download_limit_2: int = 0,
        schedule_plan: str = _DEFAULT_SCHEDULE,
        dry_run: bool = False,
    ) -> dict:
        """Set bandwidth limit for a single group+protocol combination.

        Args:
            group_name: DSM group name.
            protocol: Protocol name (e.g. ``"FileStation"``, ``"FTP"``).
            policy: ``"disabled"``, ``"enabled"``, ``"scheduled"``, or ``"group"``.
            upload_limit_1: Upload speed limit 1 in KB/s.
            download_limit_1: Download speed limit 1 in KB/s.
            upload_limit_2: Upload speed limit 2 in KB/s (for scheduled mode).
            download_limit_2: Download speed limit 2 in KB/s (for scheduled mode).
            schedule_plan: 168-char schedule string.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.

        Raises:
            ValueError: If ``policy`` is not a recognised value.
        """
        return self._set_single(
            name=group_name,
            owner_type="local_group",
            protocol=protocol,
            policy=policy,
            upload_limit_1=upload_limit_1,
            download_limit_1=download_limit_1,
            upload_limit_2=upload_limit_2,
            download_limit_2=download_limit_2,
            schedule_plan=schedule_plan,
            dry_run=dry_run,
        )

    # ------------------------------------------------------------------
    # Ensure (idempotent)
    # ------------------------------------------------------------------

    def ensure_user(
        self,
        username: str,
        protocol: str,
        policy: str = "enabled",
        upload_limit_1: int = 0,
        download_limit_1: int = 0,
        upload_limit_2: int = 0,
        download_limit_2: int = 0,
        schedule_plan: str = _DEFAULT_SCHEDULE,
        dry_run: bool = False,
    ) -> dict:
        """Idempotent bandwidth limit for a user — set only if changed.

        Reads the current bandwidth config, compares to the desired state,
        and writes only if different.

        Args:
            username: DSM username.
            protocol: Protocol name (e.g. ``"FileStation"``).
            policy: ``"disabled"``, ``"enabled"``, ``"scheduled"``, or ``"group"``.
            upload_limit_1: Upload speed limit 1 in KB/s.
            download_limit_1: Download speed limit 1 in KB/s.
            upload_limit_2: Upload speed limit 2 in KB/s (for scheduled mode).
            download_limit_2: Download speed limit 2 in KB/s (for scheduled mode).
            schedule_plan: 168-char schedule string.
            dry_run: If ``True``, compute diff but skip the API write.

        Returns:
            Result dict::

                {"changed": bool, "action": "none" | "updated"}
                # + "dry_run": True when dry_run=True
        """
        return self._ensure(
            name=username,
            owner_type="local_user",
            protocol=protocol,
            policy=policy,
            upload_limit_1=upload_limit_1,
            download_limit_1=download_limit_1,
            upload_limit_2=upload_limit_2,
            download_limit_2=download_limit_2,
            schedule_plan=schedule_plan,
            dry_run=dry_run,
        )

    def ensure_group(
        self,
        group_name: str,
        protocol: str,
        policy: str = "enabled",
        upload_limit_1: int = 0,
        download_limit_1: int = 0,
        upload_limit_2: int = 0,
        download_limit_2: int = 0,
        schedule_plan: str = _DEFAULT_SCHEDULE,
        dry_run: bool = False,
    ) -> dict:
        """Idempotent bandwidth limit for a group — set only if changed.

        Reads the current bandwidth config, compares to the desired state,
        and writes only if different.

        Args:
            group_name: DSM group name.
            protocol: Protocol name (e.g. ``"FileStation"``).
            policy: ``"disabled"``, ``"enabled"``, ``"scheduled"``, or ``"group"``.
            upload_limit_1: Upload speed limit 1 in KB/s.
            download_limit_1: Download speed limit 1 in KB/s.
            upload_limit_2: Upload speed limit 2 in KB/s (for scheduled mode).
            download_limit_2: Download speed limit 2 in KB/s (for scheduled mode).
            schedule_plan: 168-char schedule string.
            dry_run: If ``True``, compute diff but skip the API write.

        Returns:
            Result dict::

                {"changed": bool, "action": "none" | "updated"}
                # + "dry_run": True when dry_run=True
        """
        return self._ensure(
            name=group_name,
            owner_type="local_group",
            protocol=protocol,
            policy=policy,
            upload_limit_1=upload_limit_1,
            download_limit_1=download_limit_1,
            upload_limit_2=upload_limit_2,
            download_limit_2=download_limit_2,
            schedule_plan=schedule_plan,
            dry_run=dry_run,
        )

    # ------------------------------------------------------------------
    # Disable helpers
    # ------------------------------------------------------------------

    def disable_user(
        self,
        username: str,
        protocol: str,
        dry_run: bool = False,
    ) -> dict:
        """Disable bandwidth limit for a user+protocol (set policy="disabled").

        Args:
            username: DSM username.
            protocol: Protocol name.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.
        """
        return self.ensure_user(
            username=username,
            protocol=protocol,
            policy="disabled",
            dry_run=dry_run,
        )

    def disable_group(
        self,
        group_name: str,
        protocol: str,
        dry_run: bool = False,
    ) -> dict:
        """Disable bandwidth limit for a group+protocol (set policy="disabled").

        Args:
            group_name: DSM group name.
            protocol: Protocol name.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.
        """
        return self.ensure_group(
            group_name=group_name,
            protocol=protocol,
            policy="disabled",
            dry_run=dry_run,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

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

    def _build_bandwidth_obj(
        self,
        name: str,
        owner_type: str,
        protocol: str,
        policy: str,
        upload_limit_1: int,
        download_limit_1: int,
        upload_limit_2: int,
        download_limit_2: int,
        schedule_plan: str,
    ) -> dict:
        """Build a bandwidth object for the set API.

        Returns:
            Bandwidth dict ready for JSON serialisation.
        """
        return {
            "name": name,
            "owner_type": owner_type,
            "protocol": protocol,
            "protocol_ui": protocol,
            "policy": policy,
            "upload_limit_1": upload_limit_1,
            "download_limit_1": download_limit_1,
            "upload_limit_2": upload_limit_2,
            "download_limit_2": download_limit_2,
            "schedule_plan": schedule_plan,
        }

    def _set_single(
        self,
        name: str,
        owner_type: str,
        protocol: str,
        policy: str,
        upload_limit_1: int,
        download_limit_1: int,
        upload_limit_2: int,
        download_limit_2: int,
        schedule_plan: str,
        dry_run: bool,
    ) -> dict:
        """Set bandwidth for a single name+protocol combination."""
        if policy not in _POLICIES:
            raise ValueError(
                f"Invalid policy '{policy}'. Use one of: {', '.join(sorted(_POLICIES))}."
            )
        bw_obj = self._build_bandwidth_obj(
            name=name,
            owner_type=owner_type,
            protocol=protocol,
            policy=policy,
            upload_limit_1=upload_limit_1,
            download_limit_1=download_limit_1,
            upload_limit_2=upload_limit_2,
            download_limit_2=download_limit_2,
            schedule_plan=schedule_plan,
        )
        return self.set(name, owner_type, [bw_obj], dry_run=dry_run)

    def _ensure(
        self,
        name: str,
        owner_type: str,
        protocol: str,
        policy: str,
        upload_limit_1: int,
        download_limit_1: int,
        upload_limit_2: int,
        download_limit_2: int,
        schedule_plan: str,
        dry_run: bool,
    ) -> dict:
        """Idempotent bandwidth set — read, diff, write only if changed."""
        if policy not in _POLICIES:
            raise ValueError(
                f"Invalid policy '{policy}'. Use one of: {', '.join(sorted(_POLICIES))}."
            )

        # Read current state
        current_list = self.get(name, owner_type)

        # Find existing entry for this protocol
        current: dict | None = None
        for entry in current_list:
            if entry.get("protocol") == protocol:
                current = entry
                break

        # Build desired state
        desired = self._build_bandwidth_obj(
            name=name,
            owner_type=owner_type,
            protocol=protocol,
            policy=policy,
            upload_limit_1=upload_limit_1,
            download_limit_1=download_limit_1,
            upload_limit_2=upload_limit_2,
            download_limit_2=download_limit_2,
            schedule_plan=schedule_plan,
        )

        # Compare — check the fields we control
        _COMPARE_KEYS = (
            "policy",
            "upload_limit_1",
            "download_limit_1",
            "upload_limit_2",
            "download_limit_2",
            "schedule_plan",
        )
        if current is not None:
            matches = all(current.get(k) == desired[k] for k in _COMPARE_KEYS)
        else:
            matches = False

        if matches:
            result: dict = {"changed": False, "action": "none"}
        else:
            result = {"changed": True, "action": "updated"}
            if not dry_run:
                self.set(name, owner_type, [desired])

        if dry_run:
            result["dry_run"] = True
        return result
