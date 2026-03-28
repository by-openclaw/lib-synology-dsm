"""DSM API client — session management."""

from __future__ import annotations
import httpx
from typing import Any


class DSMClient:
    """Synology DSM API client with session lifecycle management."""

    def __init__(self, host: str, port: int = 5001, https: bool = True, verify_ssl: bool = False):
        scheme = "https" if https else "http"
        self.base_url = f"{scheme}://{host}:{port}/webapi"
        self._verify = verify_ssl
        self._sid: str | None = None
        self._synotoken: str = ""
        self._client = httpx.Client(verify=verify_ssl, timeout=30)

    def login(self, account: str, password: str, session: str = "DSM") -> str:
        """Login and return session ID."""
        resp = self._client.post(
            f"{self.base_url}/entry.cgi",
            data={
                "api": "SYNO.API.Auth",
                "version": "6",
                "method": "login",
                "account": account,
                "passwd": password,
                "session": session,  # "DSM" for admin ops, "FileStation" for file ops
                "format": "sid",
                "enable_syno_token": "yes",  # required to get real SynoToken for write ops
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Login failed: {data.get('error')}")
        self._sid = data["data"]["sid"]
        self._synotoken = data["data"].get("synotoken", "")
        return self._sid

    def logout(self) -> None:
        """Logout and invalidate session."""
        if not self._sid:
            return
        self._client.post(
            f"{self.base_url}/auth.cgi",
            data={"api": "SYNO.API.Auth", "version": "1", "method": "logout", "_sid": self._sid},
        )
        self._sid = None

    def request(self, api: str, method: str, version: int = 1, **params: Any) -> dict:
        """Make an authenticated API request.

        Automatically includes _sid and X-SYNO-TOKEN header (required for
        ALL write operations on DSM 7.x — share create/delete, group set, etc.).
        Without X-SYNO-TOKEN, write ops return 403 even with valid SID.
        Token is obtained during login() via enable_syno_token=yes.
        """
        if not self._sid:
            raise RuntimeError("Not logged in. Call login() first.")
        payload = {
            "api": api,
            "version": str(version),
            "method": method,
            "_sid": self._sid,
            **params,
        }
        # X-SYNO-TOKEN is mandatory for all write operations on DSM 7.x
        # It is returned by login() when enable_syno_token=yes is set
        headers = {"X-SYNO-TOKEN": self._synotoken} if self._synotoken else {}
        resp = self._client.post(f"{self.base_url}/entry.cgi", data=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"API error [{api}.{method}]: {data.get('error')}")
        return data.get("data", {})

    def __enter__(self) -> "DSMClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.logout()
        self._client.close()
