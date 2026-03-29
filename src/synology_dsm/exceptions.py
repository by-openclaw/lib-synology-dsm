"""Synology DSM — typed exception hierarchy.

All exceptions carry an optional ``code`` attribute that maps to the DSM
API error code returned in the ``error.code`` field of the response JSON.
"""

from __future__ import annotations


class DSMError(Exception):
    """Base exception for all Synology DSM errors."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class DSMAuthError(DSMError):
    """Authentication failure — DSM error codes 400 (bad credentials) or 402 (account disabled)."""

    pass


class DSMPermissionError(DSMError):
    """Insufficient permissions — DSM error code 403."""

    pass


class DSMNotFoundError(DSMError):
    """Resource not found — DSM error code 408."""

    pass


class DSMSessionError(DSMError):
    """Session invalid or expired — DSM error code 119."""

    pass


class DSMAPIError(DSMError):
    """Generic API error — any other DSM error code."""

    pass


class DSMConnectionError(DSMError):
    """Network-level failure — cannot reach the NAS (connection refused, timeout, DNS failure).

    Wraps urllib.error.URLError and socket-level errors so callers never
    need to import urllib internals to handle connection failures.

    Attributes:
        code: Always None (no DSM error code for network failures).
    """

    pass
