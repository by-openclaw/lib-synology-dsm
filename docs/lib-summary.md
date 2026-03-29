# lib-synology-dsm — Capability Summary

## What this library does

Python library for Synology DSM API automation. Provides idempotent CRUD operations
for users, groups, and shared folders — Ansible-compatible, credential-safe.

## CRUD Coverage

### Users (`UserManager`)

| Operation | Method | Notes |
|---|---|---|
| List | `list()` | Returns all local users |
| Create | `create(name, password, email, description)` | |
| Update | `update(name, **fields)` | description, email, password |
| Delete | `delete(name)` | JSON array format (DSM requirement) |
| Disable | `disable(name)` | Preferred over delete — preserves audit trail |
| Add to group | `add_to_group(username, group)` | |
| Remove from group | `remove_from_group(username, group)` | |
| **Ensure** | `ensure(name, state, password, email, description)` | state="present"/"absent" |

### Groups (`GroupManager`)

| Operation | Method | Notes |
|---|---|---|
| List | `list()` | Returns all local groups |
| Create | `create(name, description)` | |
| Update | `update(name, **fields)` | description |
| Delete | `delete(name)` | JSON array format |
| Get details | `get(name)` | |
| Add member | `add_member(group, username)` | Fetches current list first — safe |
| Remove member | `remove_member(group, username)` | |
| List members | `list_members(group)` | |
| **Ensure** | `ensure(name, state, description)` | state="present"/"absent" |

### Shared Folders (`ShareManager`)

| Operation | Method | Notes |
|---|---|---|
| List | `list(additional)` | Optional extra fields |
| Create | `create(name, volume_path, description)` | Uses shareinfo JSON (DSM 7.x requirement) |
| Update | `update(name, **fields)` | desc, hidden, recycle_bin |
| Delete | `delete(name)` | |
| Set user permission | `set_permission(share, username, writable, readonly, deny)` | |
| Get NFS rules | `get_nfs_rules(share)` | SYNO.Core.FileServ.NFS.SharePrivilege.load |
| Set NFS permission | `set_nfs_permission(share, hostname, rw, async_io, root_squash)` | |
| **Create with all permissions** | `create_with_permissions(name, volume_path, description, owner_user, owner_group, nfs_client, nfs_rw)` | Full lifecycle: create + user perms + group perms + NFS in one call |
| **Ensure** | `ensure(name, state, volume_path, description)` | state="present"/"absent" |

### Not yet implemented

| Feature | API | Priority |
|---|---|---|
| Share quota | SYNO.Core.Share (quota param) | Medium |
| App permissions per user | SYNO.Core.AppPriv | Medium |
| System info (model/DSM version) | SYNO.Core.System | High — useful for audit automation |
| Package list | SYNO.Core.Package | Medium |
| 2FA reset | SYNO.Core.OTP | Low |
| FileStation file ops | SYNO.FileStation.* | Low |

## Ansible Compatibility

All managers implement `ensure(state="present"/"absent")` which maps directly to Ansible module semantics:

```python
# Idempotent — safe to run multiple times
result = users.ensure("svc-monitoring", state="present",
                      password="...", description="Monitoring service account")
# Returns: {"changed": True, "action": "created"} or {"changed": False, "action": "noop"}

result = shares.ensure("old-share", state="absent")
# Returns: {"changed": True, "action": "deleted"} or {"changed": False, "action": "noop"}
```

The `changed` + `action` return values map directly to Ansible's `changed` status.

## Credential Providers

### Priority order (auto-detect)
1. **Vault** — if `VAULT_ADDR` + `VAULT_TOKEN` set → reads from `secret/data/synology/nas01`
2. **Environment / .env** — reads `SYNOLOGY_HOST`, `SYNOLOGY_PORT`, `SYNOLOGY_USER`, `SYNOLOGY_PASS`

### Usage

```python
from synology_dsm.credentials import get_credentials
from synology_dsm import DSMClient

creds = get_credentials()  # auto-detects Vault or .env
with DSMClient(creds.host, port=creds.port) as client:
    client.login(creds.user, creds.password)
```

### .env (development)

```bash
cp .env.example .env
# Fill in: SYNOLOGY_HOST, SYNOLOGY_PORT, SYNOLOGY_USER, SYNOLOGY_PASS
```

### Vault (production)

```bash
export VAULT_ADDR=https://vault.by-systems.arpa
export VAULT_TOKEN=...
# Secret at: secret/data/synology/nas01
# Keys: host, port, user, password
```

## Full example — create share with all permissions

```python
from synology_dsm import DSMClient
from synology_dsm.credentials import get_credentials
from synology_dsm.shares import ShareManager

creds = get_credentials()
with DSMClient(creds.host) as client:
    client.login(creds.user, creds.password)
    shares = ShareManager(client)

    result = shares.create_with_permissions(
        name="srv-proxmox-prod-01-backup",
        volume_path="/volume1",
        description="srv-proxmox-prod-01 — VM/LXC backups — Production",
        owner_user="svc-rune-dsm",
        owner_group="svc-automation",
        nfs_client="your-nfs-client",
        nfs_rw=True,
    )
```

## Account requirements

See [hardening.md](./hardening.md) for full setup guide.

**TL;DR:** API account needs `administrators` + `users` groups. Apps: DSM + FileStation = Allow.
