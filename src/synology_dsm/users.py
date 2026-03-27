"""Synology DSM — user and group management."""
from __future__ import annotations
from .client import DSMClient


class UserManager:
    """User and group CRUD operations."""

    def __init__(self, client: DSMClient):
        self._c = client

    def list(self) -> list[dict]:
        """List all users."""
        data = self._c.request("SYNO.Core.User", "list", version=1)
        return data.get("users", [])

    def create(self, name: str, password: str, email: str = "", description: str = "") -> dict:
        """Create a user."""
        return self._c.request(
            "SYNO.Core.User", "create", version=1,
            name=name, password=password, email=email, description=description,
        )

    def delete(self, name: str) -> None:
        """Delete a user by name.

        Note: DSM API requires name as a JSON array string e.g. '["username"]'.
        Prefer disable() to preserve audit trail unless hard cleanup is needed.
        """
        import json
        self._c.request("SYNO.Core.User", "delete", version=1, name=json.dumps([name]))

    def disable(self, name: str) -> None:
        """Disable a user (preferred over delete — audit trail preserved)."""
        self._c.request("SYNO.Core.User", "set", version=1, name=name, expired="true")

    def list_groups(self) -> list[dict]:
        """List all groups."""
        data = self._c.request("SYNO.Core.Group", "list", version=1)
        return data.get("groups", [])
