# SPDX-License-Identifier: MIT
"""SYNO.Core.FileServ.NFS.SharePrivilege — per-share NFS rule management.

API: SYNO.Core.FileServ.NFS.SharePrivilege v1
Public methods: list(), get(), ensure()
Internal CRUD: _create(), _update(), _delete() — called by ensure() only.

Note: SYNO.Core.Share.NFS does NOT exist on DSM 7.x — returns error 102.
      Always use SYNO.Core.FileServ.NFS.SharePrivilege instead.
      The save method REPLACES the entire rule list for a share.
"""

from __future__ import annotations

import json
from typing import Any

from synology_dsm_v2.base import Action, BaseManager, ClientProtocol, EnsureResult, State


class CoreFileServNFSManager(BaseManager):
    """SYNO.Core.FileServ.NFS.SharePrivilege — NFS rule CRUD per share via ensure().

    Unlike other managers, ensure() operates per-hostname per-share:

        nfs = CoreFileServNFSManager(client)

        # Ensure NFS rule for a host on a share
        result = nfs.ensure("my-share", hostname="10.6.224.105",
                            state=State.PRESENT, rw=True, root_squash="root")

        # Remove NFS rule for a host
        result = nfs.ensure("my-share", hostname="10.6.224.105", state=State.ABSENT)

        # List all rules for a share
        rules = nfs.list("my-share")

        # Get rule for a specific host
        rule = nfs.get("my-share", hostname="10.6.224.105")
    """

    _DIFF_FIELDS = ("privilege", "root_squash", "async")

    def __init__(self, client: ClientProtocol) -> None:
        super().__init__(client, api="SYNO.Core.FileServ.NFS.SharePrivilege", version=1)

    # -- Public: read --

    def list(self, share_name: str | None = None) -> list[dict[str, Any]]:
        """List NFS rules for a share.

        Args:
            share_name: Share name to query. Required.
        """
        if not share_name:
            raise ValueError("share_name is required for NFS rule listing")
        data = self._request("load", share_name=share_name)
        return data.get("rule", [])

    def get(self, name: str, **kwargs: Any) -> dict[str, Any] | None:
        """Get NFS rule for a specific hostname on a share.

        Args:
            name: Share name.
            **kwargs: Must include hostname=<str>.
        """
        hostname = kwargs.get("hostname", "")
        if not hostname:
            raise ValueError("hostname kwarg is required")
        rules = self.list(share_name=name)
        for rule in rules:
            if rule.get("client") == hostname:
                return rule
        return None

    # -- Public: write (only ensure) --

    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> EnsureResult:
        """Idempotent NFS rule management per hostname per share.

        Args:
            name: Share name.
            state: PRESENT to add/update, ABSENT to remove.
            dry_run: Preview without API calls.
            **kwargs: Must include hostname. Optional: rw (bool), root_squash (str),
                      async_io (bool).
        """
        hostname: str = kwargs.pop("hostname", "")
        if not hostname:
            raise ValueError("hostname kwarg is required")

        current = self.get(name, hostname=hostname)

        if state == State.PRESENT:
            return self._ensure_present(name, hostname, current, dry_run, **kwargs)
        elif state == State.ABSENT:
            return self._ensure_absent(name, hostname, current, dry_run)
        else:
            raise ValueError(f"Invalid state: {state!r} — use State.PRESENT or State.ABSENT")

    # -- Private: CRUD (called by ensure only) --

    def _build_rule(self, hostname: str, **kwargs: Any) -> dict[str, Any]:
        """Build a complete NFS rule dict."""
        rw = kwargs.get("rw", True)
        return {
            "client": hostname,
            "privilege": "rw" if rw else "ro",
            "root_squash": kwargs.get("root_squash", "root"),
            "async": kwargs.get("async_io", True),
            "insecure": False,
            "crossmnt": False,
            "security_flavor": {
                "sys": True,
                "kerberos": False,
                "kerberos_integrity": False,
                "kerberos_privacy": False,
            },
        }

    def _save_rules(self, share_name: str, rules: list[dict[str, Any]]) -> dict[str, Any]:
        """Replace all NFS rules for a share."""
        return self._request("save", share_name=share_name, rule=json.dumps(rules))

    def _create(self, share_name: str, hostname: str, **kwargs: Any) -> dict[str, Any]:
        """Add an NFS rule for a hostname (appends to existing rules)."""
        current_rules = self.list(share_name=share_name)
        new_rule = self._build_rule(hostname, **kwargs)
        return self._save_rules(share_name, [*current_rules, new_rule])

    def _update(self, share_name: str, hostname: str, **kwargs: Any) -> dict[str, Any]:
        """Update an NFS rule for a hostname (replaces matching rule)."""
        current_rules = self.list(share_name=share_name)
        new_rule = self._build_rule(hostname, **kwargs)
        updated = [new_rule if r.get("client") == hostname else r for r in current_rules]
        return self._save_rules(share_name, updated)

    def _delete(self, share_name: str, hostname: str) -> dict[str, Any]:
        """Remove an NFS rule for a hostname."""
        current_rules = self.list(share_name=share_name)
        filtered = [r for r in current_rules if r.get("client") != hostname]
        return self._save_rules(share_name, filtered)

    # -- Private: ensure logic --

    def _ensure_present(
        self,
        share_name: str,
        hostname: str,
        current: dict[str, Any] | None,
        dry_run: bool,
        **kwargs: Any,
    ) -> EnsureResult:
        """Create if missing, update if drifted, noop if matches."""
        desired = self._build_rule(hostname, **kwargs)

        if current is None:
            if dry_run:
                return EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True)
            self._create(share_name, hostname, **kwargs)
            return EnsureResult(changed=True, action=Action.CREATED, after=desired)

        # Check for drift
        diff = {k: desired[k] for k in self._DIFF_FIELDS if current.get(k) != desired[k]}
        if not diff:
            return EnsureResult(changed=False, action=Action.NOOP, before=current)

        if dry_run:
            return EnsureResult(
                changed=False, action=Action.WOULD_UPDATE, before=current, dry_run=True
            )

        self._update(share_name, hostname, **kwargs)
        return EnsureResult(changed=True, action=Action.UPDATED, before=current, after=desired)

    def _ensure_absent(
        self,
        share_name: str,
        hostname: str,
        current: dict[str, Any] | None,
        dry_run: bool,
    ) -> EnsureResult:
        """Delete if exists, noop if already gone."""
        if current is None:
            return EnsureResult(changed=False, action=Action.NOOP)

        if dry_run:
            return EnsureResult(
                changed=False, action=Action.WOULD_DELETE, before=current, dry_run=True
            )

        self._delete(share_name, hostname)
        return EnsureResult(changed=True, action=Action.DELETED, before=current)
