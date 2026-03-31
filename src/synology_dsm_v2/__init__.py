# SPDX-License-Identifier: MIT
"""synology_dsm_v2 — Design pattern PoC for lib-synology-dsm v2."""

from synology_dsm_v2.base import Action, BaseManager, ClientProtocol, EnsureResult, State
from synology_dsm_v2.client import DSMClient
from synology_dsm_v2.core_fileserv_nfs import CoreFileServNFSManager
from synology_dsm_v2.core_group import CoreGroupManager
from synology_dsm_v2.core_share import CoreShareManager
from synology_dsm_v2.core_user import CoreUserManager
from synology_dsm_v2.filestation import FileStationManager
from synology_dsm_v2.exceptions import (
    DSMAPIError,
    DSMAuthError,
    DSMConnectionError,
    DSMError,
    DSMInvalidOperationError,
    DSMInvalidParameterError,
    DSMNotFoundError,
    DSMPermissionError,
    DSMResourceNotFoundError,
    DSMSessionError,
)

__all__ = [
    # Base
    "Action",
    "BaseManager",
    "ClientProtocol",
    "EnsureResult",
    "State",
    # Client
    "DSMClient",
    # Exceptions
    "DSMAPIError",
    "DSMAuthError",
    "DSMConnectionError",
    "DSMError",
    "DSMInvalidOperationError",
    "DSMInvalidParameterError",
    "DSMNotFoundError",
    "DSMPermissionError",
    "DSMResourceNotFoundError",
    "DSMSessionError",
    # Managers (named by API namespace)
    "CoreFileServNFSManager",
    "CoreGroupManager",
    "CoreShareManager",
    "CoreUserManager",
    "FileStationManager",
]

__version__ = "2.0.0a1"
