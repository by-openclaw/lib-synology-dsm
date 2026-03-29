"""Synology DSM API library."""

from .client import DSMClient
from .credentials import (
    DSMCredentials,
    EnvCredentialProvider,
    VaultCredentialProvider,
    get_credentials,
)
from .filestation import FileStationManager
from .groups import GroupManager
from .shares import ShareManager
from .users import UserManager

__all__ = [
    "DSMClient",
    "DSMCredentials",
    "EnvCredentialProvider",
    "FileStationManager",
    "GroupManager",
    "ShareManager",
    "UserManager",
    "VaultCredentialProvider",
    "get_credentials",
]
__version__ = "0.6.1"
