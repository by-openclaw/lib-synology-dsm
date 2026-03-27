"""Synology DSM API library."""
from .client import DSMClient
from .groups import GroupManager
from .shares import ShareManager
from .users import UserManager

__all__ = ["DSMClient", "GroupManager", "ShareManager", "UserManager"]
__version__ = "0.2.0"
