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
        self._client = httpx.Client(verify=verify_ssl, timeout=30)

    def login(self, account: str, password: str, session: str = "DSM") -> str:
        """Login and return session ID."""
        resp = self._client.post(
            f"{self.base_url}/entry.cgi",
            data={
                "api": "SYNO.API.Auth",
                "version": "7",  # v7: returns synotoken + device_id; falls back gracefully on older DSM
                "method": "login",
                "account": account,
                "passwd": password,
                "session": session,  # use "DSM" for admin ops, "FileStation" for file ops
                "format": "sid",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Login failed: {data.get('error')}")
        self._sid = data["data"]["sid"]
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
        """Make an authenticated API request."""
        if not self._sid:
            raise RuntimeError("Not logged in. Call login() first.")
        payload = {
            "api": api,
            "version": str(version),
            "method": method,
            "_sid": self._sid,
            **params,
        }
        resp = self._client.post(f"{self.base_url}/entry.cgi", data=payload)
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
