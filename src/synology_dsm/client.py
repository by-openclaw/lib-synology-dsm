"""DSM API client — session management.

Uses stdlib urllib only — no external HTTP dependencies.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .exceptions import (
    DSMAPIError,
    DSMAuthError,
    DSMConnectionError,
    DSMError,
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

    def __init__(
        self, host: str, port: int = 5001, https: bool = True, verify_ssl: bool = False
    ) -> None:
        """Initialise a DSM API client.

        Args:
            host:       NAS hostname or IP address.
            port:       HTTPS or HTTP port (default 5001).
            https:      Use HTTPS if True (default).
            verify_ssl: Verify SSL certificate. Set False for self-signed NAS certs.
        """
        scheme = "https" if https else "http"
        self.base_url = f"{scheme}://{host}:{port}/webapi"
        self._verify = verify_ssl
        self._sid: str | None = None
        self._synotoken: str = ""
        # SSL context — skip verification when verify_ssl=False (self-signed NAS certs)
        if https and not verify_ssl:
            self._ssl_ctx: ssl.SSLContext | None = ssl._create_unverified_context()
        elif https:
            self._ssl_ctx = ssl.create_default_context()
        else:
            self._ssl_ctx = None

    def _post(self, url: str, data: dict[str, str], headers: dict[str, str] | None = None) -> dict:
        """POST form-encoded data, return parsed JSON dict."""
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise DSMConnectionError(f"Cannot reach DSM at {url}: {exc.reason}", code=None) from exc
        except OSError as exc:
            raise DSMConnectionError(
                f"Network error reaching DSM at {url}: {exc}", code=None
            ) from exc

    def _resolve_error(
        self,
        error: object,
        fallback: type[DSMError] = DSMAPIError,
        context: str = "API error",
    ) -> None:
        """Parse a DSM error dict and raise the appropriate typed exception.

        Args:
            error:    The ``error`` value from the DSM response.
            fallback: Exception class when code not in error map.
            context:  Human-readable prefix for the error message.

        Raises:
            DSMError subclass: Always raises.
        """
        raw_code = error.get("code") if isinstance(error, dict) else None  # type: ignore[union-attr]
        code: int | None = int(raw_code) if isinstance(raw_code, int) else None
        exc_class = _ERROR_MAP.get(code, fallback)
        raise exc_class(f"{context}: {error}", code=code)

    def login(self, account: str, password: str, session: str = "DSM") -> str:
        """Login and return session ID."""
        data = self._post(
            f"{self.base_url}/entry.cgi",
            {
                "api": "SYNO.API.Auth",
                "version": "6",
                "method": "login",
                "account": account,
                "passwd": password,
                "session": session,
                "format": "sid",
                "enable_syno_token": "yes",
            },
        )
        if not data.get("success"):
            self._resolve_error(
                data.get("error", {}), fallback=DSMAuthError, context="Login failed"
            )
        self._sid = data["data"]["sid"]
        self._synotoken = data["data"].get("synotoken", "")
        return self._sid

    def logout(self) -> None:
        """Logout and invalidate session."""
        if not self._sid:
            return
        try:
            self._post(
                f"{self.base_url}/auth.cgi",
                {"api": "SYNO.API.Auth", "version": "1", "method": "logout", "_sid": self._sid},
            )
        except Exception:
            pass  # Best-effort logout — don't raise on cleanup
        self._sid = None

    def request(self, api: str, method: str, version: int = 1, **params: Any) -> dict:
        """Make an authenticated API request.

        Automatically includes _sid and X-SYNO-TOKEN header (required for
        ALL write operations on DSM 7.x).

        Raises:
            DSMAuthError: On error codes 400 or 402.
            DSMPermissionError: On error code 403.
            DSMSessionError: On error code 119.
            DSMAPIError: On any other API error.
        """
        if not self._sid:
            raise RuntimeError("Not logged in. Call login() first.")
        payload: dict[str, str] = {
            "api": api,
            "version": str(version),
            "method": method,
            "_sid": self._sid,
            **{k: str(v) for k, v in params.items()},
        }
        headers = {"X-SYNO-TOKEN": self._synotoken} if self._synotoken else None
        data = self._post(f"{self.base_url}/entry.cgi", payload, headers=headers)
        if not data.get("success"):
            self._resolve_error(
                data.get("error", {}), fallback=DSMAPIError, context=f"API error [{api}.{method}]"
            )
        return data.get("data", {})

    def __enter__(self) -> DSMClient:
        return self

    def __exit__(self, *_: Any) -> None:
        """Exit the context manager — call :meth:`logout` unconditionally."""
        self.logout()
