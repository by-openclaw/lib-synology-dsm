# SPDX-License-Identifier: MIT
"""Typed exception hierarchy for DSM API errors.

Every DSM error code maps to a specific exception. Unknown codes fall back to
DSMAPIError. Network failures are wrapped as DSMConnectionError. No raw
urllib.error or socket.error ever reaches the caller.
"""

from __future__ import annotations


class DSMError(Exception):
    """Base exception for all DSM API errors.

    Attributes:
        code: DSM API error code (None for non-API errors like network failures).
        message: Human-readable description.
    """

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self.args[0]!r})"

    def __str__(self) -> str:
        if self.code is not None:
            return f"[{self.code}] {self.args[0]}"
        return self.args[0]


class DSMAuthError(DSMError):
    """Authentication failure — wrong credentials, account disabled, or OTP required.

    DSM error codes: 400, 401, 402.
    """


class DSMPermissionError(DSMError):
    """Insufficient permissions for the requested operation.

    DSM error codes: 103, 403.
    """


class DSMNotFoundError(DSMError):
    """Requested API endpoint or resource ID not found.

    DSM error codes: 104, 408.
    """


class DSMSessionError(DSMError):
    """Session expired, invalid, or timed out.

    DSM error codes: 105, 106, 119.
    """


class DSMInvalidParameterError(DSMError):
    """Invalid or missing parameter in the API request.

    DSM error codes: 100, 101, 102, 120, 1001, 1009, 1010.
    """


class DSMInvalidOperationError(DSMError):
    """Operation not supported or not allowed in current state.

    DSM error codes: 117.
    """


class DSMAPIError(DSMError):
    """Generic API error — fallback for unmapped error codes.

    If you see this exception, consider adding the error code to _ERROR_MAP
    in client.py so it gets a more specific exception type.
    """


class DSMResourceNotFoundError(DSMError):
    """Logical resource not found — e.g., user, group, or share does not exist.

    This is raised by manager ensure() methods, not directly by the API.
    Always has code=None.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code=None)


class DSMConnectionError(DSMError):
    """Network-level failure — NAS unreachable, DNS failure, timeout, TLS error.

    Wraps urllib.error.URLError and socket.OSError. Always has code=None.
    The original exception is chained via ``raise ... from``.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, code=None)


# Error code → exception type mapping.
# Used by DSMClient._resolve_error() to raise the correct exception.
# Source: https://github.com/N4S4/synology-api/blob/master/synology_api/error_codes.py
# + Synology DSM developer docs + field testing on DS1513+ DSM 7.1.1
ERROR_MAP: dict[int, type[DSMError]] = {
    # --- Common errors ---
    100: DSMInvalidParameterError,  # Unknown error
    101: DSMInvalidParameterError,  # No parameter of API, method or version
    102: DSMNotFoundError,  # The requested API does not exist
    103: DSMInvalidParameterError,  # The requested method does not exist
    104: DSMNotFoundError,  # The requested version does not support the functionality
    105: DSMPermissionError,  # The logged in session does not have permission
    106: DSMSessionError,  # Session timeout
    107: DSMSessionError,  # Session interrupted by duplicated login
    108: DSMAPIError,  # Failed to upload the file
    114: DSMInvalidParameterError,  # Lost parameters for this API
    115: DSMPermissionError,  # Not allowed to upload a file
    116: DSMInvalidOperationError,  # Not allowed to perform for a demo site
    117: DSMInvalidOperationError,  # Operation not supported
    119: DSMSessionError,  # Invalid session / SID not found
    150: DSMAuthError,  # Request source IP does not match login IP
    160: DSMPermissionError,  # Insufficient application privilege
    # --- Authentication errors (SYNO.API.Auth) ---
    400: DSMAuthError,  # No such account or incorrect password
    401: DSMAuthError,  # Disabled account
    402: DSMPermissionError,  # Denied permission
    403: DSMAuthError,  # 2-factor authentication code required
    404: DSMAuthError,  # Failed to authenticate 2-factor code
    406: DSMAuthError,  # Enforce 2-factor authentication code
    407: DSMAuthError,  # Blocked IP source
    408: DSMAuthError,  # Expired password cannot change
    409: DSMAuthError,  # Expired password
    410: DSMAuthError,  # Password must be changed
    411: DSMAuthError,  # Account locked (max try exceeded)
    # --- Core user/group/share errors ---
    1001: DSMInvalidParameterError,  # Invalid parameter
    1009: DSMInvalidParameterError,  # Invalid parameter
    1010: DSMInvalidParameterError,  # Invalid parameter
    2300: DSMInvalidParameterError,  # Shared folder error — invalid parameter
    2301: DSMInvalidParameterError,  # Shared folder — bad share name parameter
    # --- Catchall ---
    9999: DSMAPIError,  # Unknown error
}

# Human-readable descriptions for error codes.
# Used in error messages to give callers context without consulting docs.
ERROR_DESCRIPTIONS: dict[int, str] = {
    0: "Success",
    100: "Unknown error",
    101: "No parameter of API, method or version",
    102: "The requested API does not exist",
    103: "The requested method does not exist",
    104: "The requested version does not support the functionality",
    105: "The logged in session does not have permission",
    106: "Session timeout",
    107: "Session interrupted by duplicated login",
    108: "Failed to upload the file",
    114: "Lost parameters for this API",
    115: "Not allowed to upload a file",
    116: "Not allowed to perform for a demo site",
    117: "Operation not supported or not allowed",
    119: "Invalid session / SID not found",
    150: "Request source IP does not match login IP",
    160: "Insufficient application privilege",
    400: "No such account or incorrect password",
    401: "Disabled account",
    402: "Denied permission",
    403: "2-factor authentication code required",
    404: "Failed to authenticate 2-factor code",
    406: "Enforce 2-factor authentication code",
    407: "Blocked IP source",
    408: "Expired password cannot change",
    409: "Expired password",
    410: "Password must be changed",
    411: "Account locked (max try exceeded)",
    1001: "Invalid parameter",
    1009: "Invalid parameter",
    1010: "Invalid parameter",
    2300: "Shared folder error — invalid parameter",
    2301: "Shared folder — bad share name (use share_name, not sharename)",
    9999: "Unknown error",
}
