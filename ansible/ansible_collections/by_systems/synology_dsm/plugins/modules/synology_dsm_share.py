#!/usr/bin/python
# Copyright (c) 2026 BY-SYSTEMS SRL. MIT License.
# SPDX-License-Identifier: MIT
# Repo: https://github.com/by-openclaw/lib-synology-dsm

"""Ansible module: a Synology DSM shared folder, through lib-synology-dsm CoreShareManager.ensure()."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: synology_dsm_share
short_description: Manage a Synology DSM shared folder
version_added: "0.1.0"
description:
  - Create, update or delete a shared folder on a Synology NAS (DSM 7).
  - Thin wrapper around lib-synology-dsm C(CoreShareManager.ensure()); check mode is the lib's dry run.
requirements:
  - synology-dsm (lib-synology-dsm) >= 0.11.0
options:
  host:
    description: NAS address.
    type: str
    required: true
  port:
    description: DSM HTTPS port.
    type: int
    default: 5001
  username:
    description: DSM account with the right to manage shared folders.
    type: str
    required: true
  password:
    description: Its password.
    type: str
    required: true
  verify_ssl:
    description: Verify the DSM certificate.
    type: bool
    default: false
  timeout:
    description: API timeout in seconds.
    type: int
    default: 30
  name:
    description: Shared folder name.
    type: str
    required: true
  state:
    description: Whether the folder exists. C(absent) deletes the folder and its content.
    type: str
    choices: [present, absent]
    default: present
  vol_path:
    description: Volume the folder is created on (creation only).
    type: str
    default: /volume1
  description:
    description: Folder description.
    type: str
author:
  - BY-SYSTEMS
"""

EXAMPLES = r"""
- name: The backup share of a Proxmox node
  by_systems.synology_dsm.synology_dsm_share:
    host: "{{ nas_host }}"
    username: "{{ nas_user }}"
    password: "{{ nas_password }}"
    name: br-pmox-03-backup
    description: "br-pmox-03 VM/LXC backups"
  delegate_to: localhost
"""

RETURN = r"""
action:
  description: What ensure() did or, in check mode, would do (created, updated, deleted, noop, would_*).
  returned: always
  type: str
before:
  description: The folder before the change.
  returned: when it existed
  type: dict
after:
  description: The folder after the change.
  returned: when it was created or updated
  type: dict
"""

from typing import Any

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.by_systems.synology_dsm.plugins.module_utils.synology_dsm_common import (
    CONNECTION_ARGS,
    open_session,
    to_result,
)

try:
    from synology_dsm_v2 import CoreShareManager, DSMClient, DSMError, State

    HAS_LIB = True
except ImportError:  # pragma: no cover - reported to the user below
    HAS_LIB = False


def run(
    params: dict[str, Any], check_mode: bool, client: Any, manager_cls: Any, state_cls: Any
) -> dict[str, Any]:
    """The share's desired state through ensure(); returns the Ansible result."""
    kwargs: dict[str, Any] = {}
    if params["state"] == "present":
        kwargs["vol_path"] = params["vol_path"]
        if params.get("description") is not None:
            kwargs["description"] = params["description"]
    result = manager_cls(client).ensure(
        params["name"], state=state_cls(params["state"]), dry_run=check_mode, **kwargs
    )
    out: dict[str, Any] = to_result(result)
    return out


def main() -> None:
    spec = dict(CONNECTION_ARGS)
    spec.update(
        name={"type": "str", "required": True},
        state={"type": "str", "choices": ["present", "absent"], "default": "present"},
        vol_path={"type": "str", "default": "/volume1"},
        description={"type": "str"},
    )
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    if not HAS_LIB:
        module.fail_json(msg=missing_required_lib("synology-dsm (lib-synology-dsm)"))
    client = None
    try:
        client = open_session(module.params, DSMClient)
        module.exit_json(**run(module.params, module.check_mode, client, CoreShareManager, State))
    except DSMError as err:
        module.fail_json(msg=f"DSM: {err}")
    finally:
        if client is not None and getattr(client, "is_authenticated", False):
            client.logout()


if __name__ == "__main__":
    main()
