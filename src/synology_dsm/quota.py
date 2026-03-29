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

Write operations (set quota) require additional F12 capture — not yet verified.
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
