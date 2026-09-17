# SPDX-License-Identifier: MIT
"""DSM API client — authentication, session management, and HTTP transport.

Implements ClientProtocol so all managers can depend on the abstract
interface, not the concrete class. Uses only stdlib urllib (ADR-0001).
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from synology_dsm_v2.exceptions import (
    ERROR_DESCRIPTIONS,
    ERROR_MAP,
    DSMAPIError,
    DSMAuthError,
    DSMConnectionError,
    DSMError,
    DSMSessionError,
)


class DSMClient:
    """Authenticated HTTP client for the Synology DSM WebAPI.

    Handles login/logout, session tokens, and all HTTP transport.
    Managers receive a DSMClient instance via dependency injection.

    Usage::

        with DSMClient("10.6.224.6") as client:
            client.login("rune-api", password)
            users = UserManager(client)
            result = users.ensure("bob", state=State.PRESENT, password="secret")

    Attributes (read-only via @property):
        base_url: Constructed from host/port/https.
        sid: Session ID — set by login(), cleared by logout().
        synotoken: X-SYNO-TOKEN header value — required for write operations.
        timeout: HTTP timeout in seconds — configurable with validation.
    """

    def __init__(
        self,
        host: str,
        port: int = 5001,
        https: bool = True,
        verify_ssl: bool = False,
        timeout: int = 30,
    ) -> None:
        if not host:
            raise ValueError("host must not be empty")
        if port < 1 or port > 65535:
            raise ValueError(f"port must be 1-65535, got {port}")
        if timeout < 1:
            raise ValueError(f"timeout must be >= 1 second, got {timeout}")

        self._host = host
        self._port = port
        self._https = https
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._sid: str | None = None
        self._synotoken: str = ""
        self._session_name: str = ""

        # SSL context for self-signed NAS certs (verify_ssl=False).
        self._ssl_ctx: ssl.SSLContext | None = None
        if https and not verify_ssl:
            self._ssl_ctx = ssl.create_default_context()
            self._ssl_ctx.check_hostname = False
            self._ssl_ctx.verify_mode = ssl.CERT_NONE

    # -- Properties (read-only where appropriate) --

    @property
    def base_url(self) -> str:
        """Base URL for all API calls."""
        scheme = "https" if self._https else "http"
        return f"{scheme}://{self._host}:{self._port}/webapi"

    @property
    def sid(self) -> str | None:
        """Session ID — read-only. Set by login(), cleared by logout()."""
        return self._sid

    @property
    def synotoken(self) -> str:
        """X-SYNO-TOKEN value — read-only. Required for write operations."""
        return self._synotoken

    @property
    def timeout(self) -> int:
        """HTTP timeout in seconds."""
        return self._timeout

    @timeout.setter
    def timeout(self, value: int) -> None:
        if value < 1:
            raise ValueError(f"timeout must be >= 1 second, got {value}")
        self._timeout = value

    @property
    def is_authenticated(self) -> bool:
        """True if a session is active (login() succeeded, logout() not called)."""
        return self._sid is not None

    # -- Auth --

    def login(
        self,
        account: str,
        password: str,
        session: str = "DSM",
    ) -> str:
        """Authenticate and obtain a session ID + SynoToken.

        Args:
            account: DSM username.
            password: DSM password.
            session: Session name (default "DSM" — required for most APIs).

        Returns:
            Session ID string.

        Raises:
            DSMAuthError: Wrong credentials, account disabled, or OTP required.
            DSMConnectionError: NAS unreachable.
        """
        data = self._post(
            f"{self.base_url}/entry.cgi",
            {
                "api": "SYNO.API.Auth",
                "version": "6",
                "method": "login",
                "account": account,
                "passwd": password,
                "session": session,
                "enable_syno_token": "yes",
                "format": "sid",
            },
        )

        if not data.get("success"):
            error = data.get("error", {})
            code = error.get("code", 0)
            self._resolve_error(code, DSMAuthError, "Login failed")

        result = data.get("data", {})
        self._sid = result.get("sid", "")
        self._synotoken = result.get("synotoken", "")
        self._session_name = session
        return self._sid  # type: ignore[return-value]

    def logout(self) -> None:
        """Invalidate the current session (best-effort, no error on failure)."""
        if not self._sid:
            return
        try:
            self._post(
                f"{self.base_url}/entry.cgi",
                {
                    "api": "SYNO.API.Auth",
                    "version": "6",
                    "method": "logout",
                    "session": self._session_name,
                    "_sid": self._sid,
                },
            )
        except DSMError:
            pass  # Best-effort — session may already be expired.
        finally:
            self._sid = None
            self._synotoken = ""

    # -- API request --

    def request(
        self,
        api: str,
        method: str,
        version: int = 1,
        **params: Any,
    ) -> dict[str, Any]:
        """Execute an authenticated API call.

        Args:
            api: API name (e.g., "SYNO.Core.User").
            method: API method (e.g., "list", "set", "delete").
            version: API version (default 1).
            **params: Additional API parameters.

        Returns:
            The ``data`` dict from the API response.

        Raises:
            DSMSessionError: Not authenticated — call login() first.
            DSMAuthError, DSMPermissionError, DSMNotFoundError, etc.: API-specific errors.
            DSMConnectionError: Network failure.
        """
        if not self._sid:
            raise DSMSessionError("Not authenticated — call login() first")

        form: dict[str, str] = {
            "api": api,
            "version": str(version),
            "method": method,
            "_sid": self._sid,
        }
        for k, v in params.items():
            form[k] = str(v) if not isinstance(v, str) else v

        headers = {"X-SYNO-TOKEN": self._synotoken} if self._synotoken else None

        data = self._post(f"{self.base_url}/entry.cgi", form, headers=headers)

        if not data.get("success"):
            error = data.get("error", {})
            code = error.get("code", 0)
            self._resolve_error(code, context=f"{api}.{method}")

        return data.get("data", {})

    # -- Context manager --

    def __enter__(self) -> DSMClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.logout()

    def __repr__(self) -> str:
        auth = "authenticated" if self._sid else "not authenticated"
        return f"DSMClient(host={self._host!r}, port={self._port}, https={self._https}, {auth})"

    # -- Private --

    def _post(
        self,
        url: str,
        data: dict[str, str],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """POST form data and return parsed JSON response.

        Raises:
            DSMConnectionError: On any network/transport failure.
        """
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=encoded, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        try:
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=self._timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.URLError as exc:
            raise DSMConnectionError(
                f"Connection failed: {self._host}:{self._port} — {exc.reason}"
            ) from exc
        except OSError as exc:
            raise DSMConnectionError(f"Network error: {self._host}:{self._port} — {exc}") from exc

    def _resolve_error(
        self,
        code: int,
        fallback: type[DSMError] = DSMAPIError,
        context: str = "API error",
    ) -> None:
        """Raise a typed exception based on DSM error code.

        Looks up the code in ERROR_MAP. Falls back to DSMAPIError for
        unknown codes — never swallows errors.
        """
        exc_type = ERROR_MAP.get(code, fallback)
        desc = ERROR_DESCRIPTIONS.get(code, "Unknown error")
        raise exc_type(f"{context}: {desc} (code {code})", code=code)
