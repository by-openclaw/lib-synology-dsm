"""Synology DSM API library."""

from .client import DSMClient
from .credentials import (
    DSMCredentials,
    EnvCredentialProvider,
    VaultCredentialProvider,
    get_credentials,
)
from .exceptions import (
    DSMAPIError,
    DSMAuthError,
    DSMConnectionError,
    DSMError,
    DSMNotFoundError,
    DSMPermissionError,
    DSMSessionError,
)
from .filestation import FileStationManager
from .groups import GroupManager
from .nfs import NFSManager
from .shares import ShareManager
from .users import UserManager

__all__ = [
    "DSMAPIError",
    "DSMAuthError",
    "DSMClient",
    "DSMConnectionError",
    "DSMCredentials",
    "DSMError",
    "DSMNotFoundError",
    "DSMPermissionError",
    "DSMSessionError",
    "EnvCredentialProvider",
    "FileStationManager",
    "GroupManager",
    "NFSManager",
    "ShareManager",
    "UserManager",
    "VaultCredentialProvider",
    "get_credentials",
]
__version__: str = "0.8.2"
