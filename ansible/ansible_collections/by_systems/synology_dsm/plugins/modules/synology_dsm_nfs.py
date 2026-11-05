#!/usr/bin/python
# Copyright (c) 2026 BY-SYSTEMS SRL. MIT License.
# SPDX-License-Identifier: MIT
# Repo: https://github.com/by-openclaw/lib-synology-dsm

"""Ansible module: one client's NFS rule on a Synology shared folder, through CoreFileServNFSManager.ensure()."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: synology_dsm_nfs
short_description: Manage one client's NFS rule on a Synology DSM shared folder
version_added: "0.1.0"
description:
  - Add, update or remove the NFS permission rule of one client on a shared folder (DSM 7).
  - The other clients' rules on the folder are kept as they are.
  - Thin wrapper around lib-synology-dsm C(CoreFileServNFSManager.ensure()); check mode is the lib's dry run.
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
    description: DSM account with the right to manage NFS permissions.
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
  share:
    description: Shared folder the rule belongs to (it must exist).
    type: str
    required: true
  client:
    description: The client the rule admits (address, network or host name, as DSM shows it).
    type: str
    required: true
  state:
    description: Whether the rule exists.
    type: str
    choices: [present, absent]
    default: present
  privilege:
    description: Read-write or read-only.
    type: str
    choices: [rw, ro]
    default: rw
  root_squash:
    description: DSM squash mapping (C(root) no mapping, C(admin) map root to admin, C(guest) map root to guest, C(all_admin), C(all_guest)).
    type: str
    default: root
  async_io:
    description: Asynchronous writes.
    type: bool
    default: true
author:
  - BY-SYSTEMS
"""

EXAMPLES = r"""
- name: The node may mount its backup share
  by_systems.synology_dsm.synology_dsm_nfs:
    host: "{{ nas_host }}"
    username: "{{ nas_user }}"
    password: "{{ nas_password }}"
    share: pve-node1-backup
    client: 192.0.2.10
    privilege: rw
    root_squash: admin
  delegate_to: localhost
"""

RETURN = r"""
action:
  description: What ensure() did or, in check mode, would do (created, updated, deleted, noop, would_*).
  returned: always
  type: str
before:
  description: The rule before the change.
  returned: when it existed
  type: dict
after:
  description: The rule after the change.
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
    from synology_dsm_v2 import CoreFileServNFSManager, DSMClient, DSMError, State

    HAS_LIB = True
except ImportError:  # pragma: no cover - reported to the user below
    HAS_LIB = False


def run(
    params: dict[str, Any], check_mode: bool, client: Any, manager_cls: Any, state_cls: Any
) -> dict[str, Any]:
    """The client's rule on the share through ensure(); returns the Ansible result."""
    kwargs: dict[str, Any] = {"hostname": params["client"]}
    if params["state"] == "present":
        kwargs.update(
            rw=params["privilege"] == "rw",
            root_squash=params["root_squash"],
            async_io=params["async_io"],
        )
    result = manager_cls(client).ensure(
        params["share"], state=state_cls(params["state"]), dry_run=check_mode, **kwargs
    )
    out: dict[str, Any] = to_result(result)
    return out


def main() -> None:
    spec = dict(CONNECTION_ARGS)
    spec.update(
        share={"type": "str", "required": True},
        client={"type": "str", "required": True},
        state={"type": "str", "choices": ["present", "absent"], "default": "present"},
        privilege={"type": "str", "choices": ["rw", "ro"], "default": "rw"},
        root_squash={"type": "str", "default": "root"},
        async_io={"type": "bool", "default": True},
    )
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    if not HAS_LIB:
        module.fail_json(msg=missing_required_lib("synology-dsm (lib-synology-dsm)"))
    client = None
    try:
        client = open_session(module.params, DSMClient)
        module.exit_json(
            **run(module.params, module.check_mode, client, CoreFileServNFSManager, State)
        )
    except DSMError as err:
        module.fail_json(msg=f"DSM: {err}")
    finally:
        if client is not None and getattr(client, "is_authenticated", False):
            client.logout()


if __name__ == "__main__":
    main()
