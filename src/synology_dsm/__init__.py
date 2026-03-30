"""Synology DSM API library."""

from .bandwidth import BandwidthManager
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
    DSMResourceNotFoundError,
    DSMSessionError,
)
from .filestation import FileStationManager
from .groups import GroupManager
from .nfs import NFSManager
from .quota import QuotaManager
from .shares import ShareManager
from .storage import StorageManager
from .trafficcontrol import TrafficControlManager
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
    "DSMResourceNotFoundError",
    "DSMSessionError",
    "EnvCredentialProvider",
    "BandwidthManager",
    "FileStationManager",
    "GroupManager",
    "NFSManager",
    "QuotaManager",
    "ShareManager",
    "StorageManager",
    "TrafficControlManager",
    "UserManager",
    "VaultCredentialProvider",
    "get_credentials",
]
__version__ = "0.10.0"
