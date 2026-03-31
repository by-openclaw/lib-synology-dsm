"""Synology DSM — system information.

APIs (tried in order):
  1. SYNO.DSM.Info, method="getinfo", version=2
  2. SYNO.Core.System, method="info", version=1 (fallback)

Read-only. Returns NAS model, serial, hostname, DSM version, uptime.
Used by NetBox automation to auto-populate device records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .exceptions import DSMAPIError

if TYPE_CHECKING:
    from .client import DSMClient


class SystemManager:
    """Read-only system information for a Synology NAS.

    Wraps SYNO.DSM.Info (primary) and SYNO.Core.System (fallback) to
    return hardware and firmware details needed for inventory automation.
    """

    def __init__(self, client: DSMClient) -> None:
        self._c = client

    def get_info(self) -> dict:
        """Get NAS system information.

        Tries SYNO.DSM.Info first (available on most DSM 7.x), then
        falls back to SYNO.Core.System if the first call fails.

        Returns:
            Dict with keys: ``model``, ``serial``, ``hostname``,
            ``dsm_version``, ``dsm_build``, ``uptime_seconds``, ``ram_mb``.
            Missing fields are returned as ``None``.
        """
        try:
            data = self._c.request("SYNO.DSM.Info", "getinfo", version=2)
        except DSMAPIError:
            data = self._c.request("SYNO.Core.System", "info", version=1)

        return {
            "model": data.get("model"),
            "serial": data.get("serial"),
            "hostname": data.get("hostname") or data.get("server_name"),
            "dsm_version": data.get("version_string") or data.get("firmware_ver"),
            "dsm_build": data.get("version") or data.get("firmware_build"),
            "uptime_seconds": data.get("up_time") or data.get("uptime"),
            "ram_mb": data.get("ram") or data.get("physical_mem"),
        }

    def ensure(
        self,
        state: str = "present",
        dry_run: bool = False,
    ) -> dict:
        """Read-only ensure — fetches current state.

        This is a fact-gathering operation only. ``changed`` is always
        ``False`` because system info cannot be modified via this API.
        The ``dry_run`` parameter is accepted for API consistency but
        has no effect.

        Args:
            state: Accepted for API consistency. Only ``"present"`` is
                   meaningful (reads current info).
            dry_run: Accepted for API consistency; has no effect.

        Returns:
            Dict with keys: ``changed`` (always False), ``action``
            (always ``"noop"``), ``info`` (system info dict).
        """
        info = self.get_info()
        return {"changed": False, "action": "noop", "info": info}
