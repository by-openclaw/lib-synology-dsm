"""Synology DSM — storage volume information.

API: SYNO.Core.Storage.Volume (version 1, entry.cgi)

Verified payload observed via Chrome DevTools F12 on DSM 7.1.1-42962 Update 9:
    api=SYNO.Core.Storage.Volume
    method=list
    version=1
    offset=0
    limit=-1
    option=include_cold_storage
    location=internal

Read-only. No write/create/delete — volumes are managed via DSM Storage Manager UI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import DSMClient


class StorageManager:
    """Read-only access to DSM storage volume information.

    Wraps SYNO.Core.Storage.Volume — returns capacity, status, and
    filesystem details for each volume on the NAS.
    """

    def __init__(self, client: DSMClient) -> None:
        """Initialise the manager with an authenticated DSMClient.

        Args:
            client: An authenticated :class:`DSMClient` instance.
        """
        self._c = client

    def list_volumes(
        self,
        include_cold_storage: bool = True,
        location: str = "internal",
        offset: int = 0,
        limit: int = -1,
    ) -> list[dict]:
        """List all storage volumes on the NAS.

        Args:
            include_cold_storage: Include cold storage tiers in results.
                Matches the ``option=include_cold_storage`` param observed
                in DSM DevTools.
            location: Volume location filter. ``"internal"`` returns
                internal drives only. Pass ``""`` for all locations.
            offset: Pagination offset (default 0).
            limit: Max results. ``-1`` returns all (default).

        Returns:
            List of volume dicts. Each dict contains at minimum:

            - ``id`` (str): Volume identifier, e.g. ``"/volume1"``.
            - ``status`` (str): ``"normal"``, ``"degraded"``, ``"crashed"``.
            - ``device_type`` (str): e.g. ``"raid_6"``, ``"shr"``.
            - ``size_total_byte`` (int): Total capacity in bytes.
            - ``size_used_byte`` (int): Used capacity in bytes.
            - ``fs_type`` (str): Filesystem, e.g. ``"btrfs"``, ``"ext4"``.

        Example::

            storage = StorageManager(client)
            for vol in storage.list_volumes():
                total_gb = vol["size_total_byte"] / 1024**3
                used_gb  = vol["size_used_byte"]  / 1024**3
                print(f"{vol['id']}: {used_gb:.1f} / {total_gb:.1f} GB  [{vol['status']}]")
        """
        params: dict[str, object] = {
            "offset": offset,
            "limit": limit,
            "location": location,
        }
        if include_cold_storage:
            params["option"] = "include_cold_storage"

        data = self._c.request(
            "SYNO.Core.Storage.Volume",
            "list",
            version=1,
            **params,
        )
        return data.get("volumes", [])

    def get_volume(self, volume_path: str) -> dict | None:
        """Get details for a single volume by path.

        DSM 7.x returns volume path under the ``volume_path`` key (e.g. ``"/volume1"``).
        Older DSM versions may use ``id`` — both are checked.

        Args:
            volume_path: Volume path identifier, e.g. ``"/volume1"``.

        Returns:
            Volume dict, or ``None`` if not found.
        """
        volumes = self.list_volumes()
        for vol in volumes:
            if vol.get("volume_path") == volume_path or vol.get("id") == volume_path:
                return vol
        return None
