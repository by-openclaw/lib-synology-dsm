# Copyright (c) 2026 BY-SYSTEMS SRL. MIT License.
# SPDX-License-Identifier: MIT
# Repo: https://github.com/by-openclaw/lib-synology-dsm

"""Shared plumbing for the by_systems.synology_dsm modules: connection options, the session, the result.

The modules hold no DSM API logic: every change goes through a lib-synology-dsm v2 manager's ensure()
(fetch, diff, no-op when equal). This file only opens the session and turns an EnsureResult into an
Ansible result.
"""

from __future__ import annotations

from typing import Any

# Connection options every module takes.
CONNECTION_ARGS: dict[str, dict[str, Any]] = {
    "host": {"type": "str", "required": True},
    "port": {"type": "int", "default": 5001},
    "username": {"type": "str", "required": True},
    "password": {"type": "str", "required": True, "no_log": True},
    "verify_ssl": {"type": "bool", "default": False},
    "timeout": {"type": "int", "default": 30},
}

# Actions an ensure() in dry_run reports for a change it would make.
WOULD_CHANGE = {"would_create", "would_update", "would_delete"}


def to_result(ensure_result: Any) -> dict[str, Any]:
    """An EnsureResult as an Ansible result: a dry run that would change something is `changed`."""
    data: dict[str, Any] = ensure_result.to_dict()
    action = str(data.get("action", ""))
    data["changed"] = bool(data.get("changed")) or action in WOULD_CHANGE
    return data


def open_session(params: dict[str, Any], client_cls: Any) -> Any:
    """A logged-in DSMClient for the module's connection options."""
    client = client_cls(
        params["host"],
        port=params["port"],
        https=True,
        verify_ssl=params["verify_ssl"],
        timeout=params["timeout"],
    )
    client.login(params["username"], params["password"])
    return client
