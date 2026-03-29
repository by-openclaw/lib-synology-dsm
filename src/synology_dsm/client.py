"""DSM API client — session management."""

from __future__ import annotations
import httpx
from typing import Any

from .exceptions import (
    DSMAPIError,
    DSMAuthError,
    DSMPermissionError,
    DSMSessionError,
)

# Map DSM error codes to exception classes
_ERROR_MAP = {
    400: DSMAuthError,
    402: DSMAuthError,
    403: DSMPermissionError,
    119: DSMSessionError,
}


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
            error = data.get("error", {})
            code = error.get("code") if isinstance(error, dict) else None
            exc_class = _ERROR_MAP.get(code, DSMAuthError)
            raise exc_class(f"Login failed: {error}", code=code)
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

        Raises:
            DSMAuthError: On error codes 400 or 402.
            DSMPermissionError: On error code 403.
            DSMSessionError: On error code 119.
            DSMAPIError: On any other API error.
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
            error = data.get("error", {})
            code = error.get("code") if isinstance(error, dict) else None
            exc_class = _ERROR_MAP.get(code, DSMAPIError)
            raise exc_class(f"API error [{api}.{method}]: {error}", code=code)
        return data.get("data", {})

    def __enter__(self) -> "DSMClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.logout()
        self._client.close()
