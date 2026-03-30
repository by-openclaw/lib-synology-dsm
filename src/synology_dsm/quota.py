"""Synology DSM — storage quota management.

API: SYNO.Core.Quota (version 1, entry.cgi)

Verified payload observed via Chrome DevTools F12 on DSM 7.1.1-42962 Update 9:
    api=SYNO.Core.Quota
    method=get
    version=1
    name=administrators
    subject_type=group
    support_share_quota=true

subject_type switches between "group" and "user" for the respective queries.
support_share_quota=true includes per-share quota breakdowns in the response.

Write (set quota) — verified via F12:
    api=SYNO.Core.Quota
    method=set
    version=1
    name=<username>
    user_quota=[{"volume": "/volume1", "quota": <int_in_MB>}]

For groups, use group_quota key instead of user_quota.
DSM API uses MB for all quota values throughout (read and write).
DSM UI displays GB for readability — callers must convert if needed (GB * 1024 = MB).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import DSMClient

#: Valid subject types for quota queries.
_SUBJECT_TYPES = frozenset({"user", "group"})


class QuotaManager:
    """Storage quota queries for DSM users and groups.

    Wraps SYNO.Core.Quota — returns quota limits and current usage
    per user or group, optionally broken down per share.
    """

    def __init__(self, client: DSMClient) -> None:
        """Initialise the manager with an authenticated DSMClient.

        Args:
            client: An authenticated :class:`DSMClient` instance.
        """
        self._c = client

    def get_group_quota(
        self,
        group_name: str,
        support_share_quota: bool = True,
    ) -> dict:
        """Get storage quota for a group.

        Args:
            group_name: DSM group name (e.g. ``"administrators"``).
            support_share_quota: Include per-share quota breakdown.
                Matches the ``support_share_quota=true`` param observed
                in DSM DevTools.

        Returns:
            Quota dict. Fields vary by DSM version but typically include:

            - ``quota`` (int): Quota limit in MB. ``0`` = unlimited.
            - ``usage`` (int): Current usage in MB.
            - ``share_quota`` (list): Per-share breakdown when
              ``support_share_quota=True``.

        Example::

            quota = QuotaManager(client)
            q = quota.get_group_quota("svc-automation")
            print(f"Used: {q.get('usage', 0)} MB / {q.get('quota', 0) or 'unlimited'} MB")
        """
        return self._c.request(
            "SYNO.Core.Quota",
            "get",
            version=1,
            name=group_name,
            subject_type="group",
            support_share_quota="true" if support_share_quota else "false",
        )

    def get_user_quota(
        self,
        username: str,
        support_share_quota: bool = True,
    ) -> dict:
        """Get storage quota for a user.

        Args:
            username: DSM username (e.g. ``"alice"``).
            support_share_quota: Include per-share quota breakdown.

        Returns:
            Quota dict (same shape as :meth:`get_group_quota`).
        """
        return self._c.request(
            "SYNO.Core.Quota",
            "get",
            version=1,
            name=username,
            subject_type="user",
            support_share_quota="true" if support_share_quota else "false",
        )

    def set_user_quota(
        self,
        username: str,
        volume_path: str,
        quota_mb: int,
        dry_run: bool = False,
    ) -> dict:
        """Set storage quota for a user on a specific volume.

        DSM API uses MB for all quota values. DSM UI displays GB for
        readability — callers must convert if needed (GB * 1024 = MB).

        Args:
            username: DSM username (e.g. ``"alice"``).
            volume_path: Volume path (e.g. ``"/volume1"``).
            quota_mb: Desired quota in MB. Use ``0`` for unlimited.
                Example: ``quota_mb=10240  # 10 GB``
            dry_run: If ``True``, skip the API call and return what
                would have changed.

        Returns:
            Result dict::

                {
                    "changed": True,
                    "action": "set",
                    "quota_mb": <quota_mb>,
                    "volume": <volume_path>,
                    # "dry_run": True   # only present when dry_run=True
                }

        Example::

            mgr = QuotaManager(client)
            result = mgr.set_user_quota("alice", "/volume1", 51200)  # 50 GB
            # {"changed": True, "action": "set", "quota_mb": 51200, "volume": "/volume1"}
        """
        result: dict = {
            "changed": True,
            "action": "set",
            "quota_mb": quota_mb,
            "volume": volume_path,
        }
        if dry_run:
            result["dry_run"] = True
            return result
        import json

        self._c.request(
            "SYNO.Core.Quota",
            "set",
            version=1,
            name=username,
            user_quota=json.dumps([{"volume": volume_path, "quota": quota_mb}]),
        )
        return result

    def set_group_quota(
        self,
        group_name: str,
        volume_path: str,
        quota_mb: int,
        dry_run: bool = False,
    ) -> dict:
        """Set storage quota for a group on a specific volume.

        DSM API uses MB for all quota values. DSM UI displays GB for
        readability — callers must convert if needed (GB * 1024 = MB).

        Args:
            group_name: DSM group name (e.g. ``"administrators"``).
            volume_path: Volume path (e.g. ``"/volume1"``).
            quota_mb: Desired quota in MB. Use ``0`` for unlimited.
                Example: ``quota_mb=10240  # 10 GB``
            dry_run: If ``True``, skip the API call and return what
                would have changed.

        Returns:
            Result dict::

                {
                    "changed": True,
                    "action": "set",
                    "quota_mb": <quota_mb>,
                    "volume": <volume_path>,
                    # "dry_run": True   # only present when dry_run=True
                }

        Example::

            mgr = QuotaManager(client)
            result = mgr.set_group_quota("devops", "/volume1", 102400)  # 100 GB
            # {"changed": True, "action": "set", "quota_mb": 102400, "volume": "/volume1"}
        """
        result: dict = {
            "changed": True,
            "action": "set",
            "quota_mb": quota_mb,
            "volume": volume_path,
        }
        if dry_run:
            result["dry_run"] = True
            return result
        import json

        self._c.request(
            "SYNO.Core.Quota",
            "set",
            version=1,
            name=group_name,
            group_quota=json.dumps([{"volume": volume_path, "quota": quota_mb}]),
        )
        return result

    def ensure(
        self,
        name: str,
        subject_type: str,
        volume_path: str,
        quota_mb: int | None = None,
        state: str = "present",
        dry_run: bool = False,
    ) -> dict:
        """Idempotent quota management — create, update, or remove a quota.

        DSM API uses MB for all quota values. DSM UI displays GB for
        readability — callers must convert if needed (GB * 1024 = MB).
        quota=0 means unlimited.

        Args:
            name: DSM username or group name.
            subject_type: ``"user"`` or ``"group"``.
            volume_path: Volume path (e.g. ``"/volume1"``).
            quota_mb: Desired quota in MB. Required when
                ``state="present"``. Ignored when ``state="absent"``.
                Example: ``quota_mb=10240  # 10 GB``
            state: ``"present"`` to ensure quota is set to ``quota_mb``;
                ``"absent"`` to remove quota (set to 0 = unlimited).
            dry_run: If ``True``, compute what would change and return
                the same dict structure without making any API writes.

        Returns:
            Result dict::

                {
                    "changed": bool,       # True if API was called (or would be)
                    "action": str,         # "none" | "created" | "updated" | "removed"
                    # "dry_run": True      # only present when dry_run=True
                }

        Raises:
            ValueError: If ``subject_type`` is not ``"user"`` or ``"group"``.
            ValueError: If ``state="present"`` and ``quota_mb`` is not provided.

        Notes:
            - DSM API uses MB for all quota values.
            - quota=0 means unlimited.

        Example::

            mgr = QuotaManager(client)

            # Ensure alice has 50 GB (51200 MB) on /volume1
            result = mgr.ensure("alice", "user", "/volume1", quota_mb=51200)
            # {"changed": True, "action": "created"} on first run
            # {"changed": False, "action": "none"}    on second run

            # Remove quota (set to unlimited)
            result = mgr.ensure("alice", "user", "/volume1", state="absent")
            # {"changed": True, "action": "removed"}

            # Dry-run preview
            result = mgr.ensure("alice", "user", "/volume1", quota_mb=51200, dry_run=True)
            # {"changed": True, "action": "created", "dry_run": True}
        """
        if subject_type not in _SUBJECT_TYPES:
            raise ValueError(f"Invalid subject_type '{subject_type}'. Use 'user' or 'group'.")

        if state == "present" and quota_mb is None:
            raise ValueError("quota_mb must be provided when state='present'.")

        # Read current quota
        if subject_type == "user":
            current_data = self.get_user_quota(name)
        else:
            current_data = self.get_group_quota(name)

        # Parse current quota for this volume (MB) — defensive: try per-volume list first
        current_mb: int = 0
        quota_list_key = "user_quota" if subject_type == "user" else "group_quota"
        quota_list = current_data.get(quota_list_key, [])
        if quota_list:
            for entry in quota_list:
                if entry.get("volume") == volume_path:
                    current_mb = int(entry.get("quota", 0))
                    break
        else:
            # Fall back to top-level quota field
            current_mb = int(current_data.get("quota", 0))

        if state == "present":
            if current_mb == quota_mb:
                result: dict = {"changed": False, "action": "none"}
            else:
                action = "created" if current_mb == 0 else "updated"
                result = {"changed": True, "action": action}
                if not dry_run:
                    if subject_type == "user":
                        self.set_user_quota(name, volume_path, quota_mb)  # type: ignore[arg-type]
                    else:
                        self.set_group_quota(name, volume_path, quota_mb)  # type: ignore[arg-type]
        else:  # state == "absent"
            if current_mb == 0:
                result = {"changed": False, "action": "none"}
            else:
                result = {"changed": True, "action": "removed"}
                if not dry_run:
                    if subject_type == "user":
                        self.set_user_quota(name, volume_path, 0)
                    else:
                        self.set_group_quota(name, volume_path, 0)

        if dry_run:
            result["dry_run"] = True
        return result

    def get_quota(
        self,
        name: str,
        subject_type: str,
        support_share_quota: bool = True,
    ) -> dict:
        """Get storage quota for a named user or group.

        Lower-level method — prefer :meth:`get_user_quota` or
        :meth:`get_group_quota` for clarity.

        Args:
            name: DSM username or group name.
            subject_type: ``"user"`` or ``"group"``.
            support_share_quota: Include per-share quota breakdown.

        Returns:
            Quota dict from the API.

        Raises:
            ValueError: If ``subject_type`` is not ``"user"`` or ``"group"``.
        """
        if subject_type not in _SUBJECT_TYPES:
            raise ValueError(f"Invalid subject_type '{subject_type}'. Use 'user' or 'group'.")
        return self._c.request(
            "SYNO.Core.Quota",
            "get",
            version=1,
            name=name,
            subject_type=subject_type,
            support_share_quota="true" if support_share_quota else "false",
        )
