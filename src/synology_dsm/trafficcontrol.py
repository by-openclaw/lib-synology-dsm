"""Synology DSM — network traffic control rules.

API: SYNO.Core.Network.TrafficControl.Rules (version 1, entry.cgi)

Verified payload observed via curl on DSM 7.1.1-42962 Update 9:
    api=SYNO.Core.Network.TrafficControl.Rules
    method=load
    version=1
    adapter=<adapter_name>

Write:
    api=SYNO.Core.Network.TrafficControl.Rules
    method=save
    version=1
    adapter=<adapter_name>
    rules=<JSON-stringified array of rule objects>

Transport is form-encoded POST — NOT JSON body.

Rule object fields:
    id          — rule index (0-based)
    enabled     — bool
    port_type   — "ALL" | "SYS" | "CUSTOM"
    port_num    — "" (for ALL), comma-separated service names, or port numbers
    port_direction — "src" | "dst"
    protocol    — "all" | "tcp" | "udp"
    minrate     — minimum guaranteed rate in KB/s (0 = no guarantee)
    maxrate     — maximum allowed rate in KB/s (0 = unlimited)
    source      — "all" or specific IP/CIDR
    ip_direction — "dest" | "src"

port_type values:
    "ALL"    → all ports, port_num must be ""
    "SYS"    → named system services (comma-separated)
    "CUSTOM" → raw port number(s)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import DSMClient

#: Fields used to match rules for idempotent ensure operations.
_MATCH_KEYS = ("port_type", "port_num", "protocol")

#: Fields compared to detect changes in ensure operations.
_COMPARE_KEYS = (
    "enabled",
    "port_type",
    "port_num",
    "port_direction",
    "protocol",
    "minrate",
    "maxrate",
    "source",
    "ip_direction",
)


class TrafficControlManager:
    """Network traffic control rule management for DSM.

    Wraps SYNO.Core.Network.TrafficControl.Rules — load, save, and manage
    per-adapter traffic shaping rules in DSM Control Panel → Network →
    Traffic Control.
    """

    def __init__(self, client: DSMClient) -> None:
        """Initialise the manager with an authenticated DSMClient.

        Args:
            client: An authenticated :class:`DSMClient` instance.
        """
        self._c = client

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load(self, adapter: str) -> list[dict]:
        """Load current traffic control rules for an adapter.

        Args:
            adapter: Network adapter name (e.g. ``"eth0"``, ``"ovs_eth0"``).

        Returns:
            List of rule dicts.

        Example::

            tc = TrafficControlManager(client)
            rules = tc.load("eth0")
            for rule in rules:
                print(f"Port: {rule['port_num']}  Max: {rule['maxrate']} KB/s")
        """
        data = self._c.request(
            "SYNO.Core.Network.TrafficControl.Rules",
            "load",
            version=1,
            adapter=adapter,
        )
        rules: list[dict] = data.get("rules", [])
        # DSM strips the ``id`` field on save/load — add synthetic IDs
        # so callers can reference rules by position.
        for i, r in enumerate(rules):
            if "id" not in r:
                r["id"] = i
        return rules

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(
        self,
        adapter: str,
        rules: list[dict],
        dry_run: bool = False,
    ) -> dict:
        """Save the full rule list for an adapter (replaces all existing rules).

        Args:
            adapter: Network adapter name.
            rules: Complete list of rule dicts to persist.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.
        """
        result: dict = {"changed": True, "action": "save"}
        if dry_run:
            result["dry_run"] = True
            return result
        self._c.request(
            "SYNO.Core.Network.TrafficControl.Rules",
            "save",
            version=1,
            adapter=adapter,
            rules=json.dumps(rules),
        )
        return result

    def add_rule(
        self,
        adapter: str,
        rule: dict,
        dry_run: bool = False,
    ) -> dict:
        """Add a rule to the existing rule list for an adapter.

        Loads the current rules, appends the new rule with the next
        available ``id``, and saves.

        Args:
            adapter: Network adapter name.
            rule: Rule dict to append (``id`` will be set automatically).
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.
        """
        current = self.load(adapter)
        next_id = max((r.get("id", -1) for r in current), default=-1) + 1
        new_rule = {**rule, "id": next_id}
        current.append(new_rule)
        result: dict = {"changed": True, "action": "added"}
        if dry_run:
            result["dry_run"] = True
            return result
        self._save_raw(adapter, current)
        return result

    def remove_rule(
        self,
        adapter: str,
        rule_id: int,
        dry_run: bool = False,
    ) -> dict:
        """Remove a rule by its ``id`` from the adapter's rule list.

        Args:
            adapter: Network adapter name.
            rule_id: The ``id`` of the rule to remove.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.
        """
        current = self.load(adapter)
        filtered = [r for r in current if r.get("id") != rule_id]
        if len(filtered) == len(current):
            result: dict = {"changed": False, "action": "none"}
        else:
            result = {"changed": True, "action": "removed"}
            if not dry_run:
                self._save_raw(adapter, filtered)
        if dry_run:
            result["dry_run"] = True
        return result

    def clear_rules(
        self,
        adapter: str,
        dry_run: bool = False,
    ) -> dict:
        """Remove all traffic control rules for an adapter.

        Args:
            adapter: Network adapter name.
            dry_run: If ``True``, skip the API write.

        Returns:
            Result dict with ``changed``, ``action``, and optionally ``dry_run``.
        """
        result: dict = {"changed": True, "action": "cleared"}
        if dry_run:
            result["dry_run"] = True
            return result
        self._save_raw(adapter, [])
        return result

    # ------------------------------------------------------------------
    # Ensure (idempotent)
    # ------------------------------------------------------------------

    def ensure_rule(
        self,
        adapter: str,
        rule: dict,
        dry_run: bool = False,
    ) -> dict:
        """Idempotent rule management — add or update only if different.

        Matches existing rules by ``port_type`` + ``port_num`` + ``protocol``.
        If a matching rule exists with identical settings, no change is made.
        If a matching rule exists with different settings, it is updated.
        If no matching rule exists, a new one is added.

        Args:
            adapter: Network adapter name.
            rule: Desired rule dict.
            dry_run: If ``True``, compute diff but skip the API write.

        Returns:
            Result dict::

                {"changed": bool, "action": "none" | "added" | "updated"}
                # + "dry_run": True when dry_run=True
        """
        current_rules = self.load(adapter)

        # Find existing rule by match keys
        existing: dict | None = None
        existing_idx: int | None = None
        for i, r in enumerate(current_rules):
            if all(r.get(k) == rule.get(k) for k in _MATCH_KEYS):
                existing = r
                existing_idx = i
                break

        if existing is not None:
            # Check if all fields match
            matches = all(existing.get(k) == rule.get(k) for k in _COMPARE_KEYS)
            if matches:
                result: dict = {"changed": False, "action": "none"}
            else:
                result = {"changed": True, "action": "updated"}
                if not dry_run:
                    assert existing_idx is not None
                    current_rules[existing_idx] = {**rule, "id": existing.get("id", existing_idx)}
                    self._save_raw(adapter, current_rules)
        else:
            result = {"changed": True, "action": "added"}
            if not dry_run:
                next_id = max((r.get("id", -1) for r in current_rules), default=-1) + 1
                current_rules.append({**rule, "id": next_id})
                self._save_raw(adapter, current_rules)

        if dry_run:
            result["dry_run"] = True
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save_raw(self, adapter: str, rules: list[dict]) -> None:
        """Save rules without returning a result dict."""
        self._c.request(
            "SYNO.Core.Network.TrafficControl.Rules",
            "save",
            version=1,
            adapter=adapter,
            rules=json.dumps(rules),
        )
