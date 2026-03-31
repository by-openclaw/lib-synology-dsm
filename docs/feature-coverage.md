# Feature Coverage

Tracks implemented vs planned DSM API coverage for lib-synology-dsm.
Updated as features are added.

**Legend:** ✅ Implemented | 🚧 Planned | ❌ Not supported | ➖ N/A

---

## ⚠️ Account Permission Requirements

> **Confirmed on DS1513+ DSM 7.1.1** (tested with and without admin group — 2026-03-28)

The API account **must** be in the `administrators` group. Apps alone are not sufficient:

| Config | Auth | Read | Write (shares/NFS/users) |
|---|---|---|---|
| Apps only (no group) | ❌ error 402 | ❌ | ❌ |
| `users` group only | ✅ | ✅ partial | ❌ error 119 |
| `administrators` + `users` | ✅ | ✅ | ✅ |

**Required DSM user setup:**
- Groups: `administrators` + `users`
- Applications: DSM = Allow, File Station = Allow

---

## User Management (`SYNO.Core.User`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List users | `UserManager.list()` | ✅ | |
| List users (detailed) | `UserManager.list_detailed()` | ✅ | email, description, expired fields |
| Get user | `UserManager.get()` | ✅ | Returns None if not found |
| Create user | `UserManager.create()` | ✅ | |
| Update user | `UserManager.update()` | ✅ | description, email, password |
| Delete user | `UserManager.delete()` | ✅ | JSON array format required |
| Disable user | `UserManager.disable()` | ✅ | Preferred over delete — audit trail preserved |
| Add to group | `UserManager.add_to_group()` | ✅ | Idempotent — delegates to GroupManager |
| Remove from group | `UserManager.remove_from_group()` | ✅ | Idempotent — delegates to GroupManager |
| Change password | `UserManager.update(password=)` | ✅ | Via update() |
| Ensure present/absent | `UserManager.ensure()` | ✅ | Idempotent, Ansible-style |
| Reset 2FA | | 🚧 | SYNO.Core.User.OTP |
| Set home folder | | 🚧 | homes share integration |

## Group Management (`SYNO.Core.Group`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List groups | `GroupManager.list()` | ✅ | |
| Get group | `GroupManager.get()` | ✅ | |
| Create group | `GroupManager.create()` | ✅ | |
| Update group | `GroupManager.update()` | ✅ | description |
| Delete group | `GroupManager.delete()` | ✅ | JSON array format required |
| Add member | `GroupManager.add_member()` | ✅ | Fetches current list first — idempotent |
| Remove member | `GroupManager.remove_member()` | ✅ | Fetches current list first — idempotent |
| List members | `GroupManager.list_members()` | ✅ | |
| List shares for group | `ShareManager.list_shares_for_group()` | ✅ | Returns shares accessible to a group |
| Ensure present/absent | `GroupManager.ensure()` | ✅ | Idempotent, Ansible-style |
| Set group share permissions | `SharePermissionManager.set()` | ✅ | SYNO.Core.Share.Permission — ACL |

## Shared Folder Management (`SYNO.Core.Share`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List shares | `ShareManager.list()` | ✅ | |
| Create share | `ShareManager.create()` | ✅ | Requires admin |
| Create share with permissions | `ShareManager.create_with_permissions()` | ✅ | Atomic create + ACL |
| Update share | `ShareManager.update()` | ✅ | desc, hidden, recycle_bin — requires admin |
| Delete share | `ShareManager.delete()` | ✅ | Requires admin |
| Set user/group permission | `ShareManager.set_permission()` | ✅ | Read/write/deny |
| Set NFS permission | `ShareManager.set_nfs_permission()` | ✅ | Requires admin |
| Get NFS rules | `ShareManager.get_nfs_rules()` | ✅ | |
| Ensure present/absent | `ShareManager.ensure()` | ✅ | Idempotent — requires admin |
| Enable encryption | | 🚧 | Encryption at rest |
| Clone/snapshot | | ❌ | Not supported via Core API |

## NFS Management (`SYNO.Core.Share.NFS`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| Get NFS rules | `NFSManager.get_rules()` | ✅ | Per-share |
| Set NFS rules | `NFSManager.set_rules()` | ✅ | Full rule list replace |
| Ensure rule present/absent | `NFSManager.ensure()` | ✅ | Per-client hostname, idempotent |

## File Operations (`SYNO.FileStation`)

> **Auth quirk (DS1513+ DSM 7.x):** `SynoToken` must be in URL query string; session as cookie `id=`; field name `path` not `dest_folder_path`. Login must use `session=DSM`. All handled transparently by `FileStationManager`.

| Feature | Method | Status | Notes |
|---|---|---|---|
| List shares | `FileStationManager.list_shares()` | ✅ | |
| List directory | `FileStationManager.list()` | ✅ | Supports `additional`: size, time, owner, perm, real_path, type |
| Upload file | `FileStationManager.upload()` | ✅ | `overwrite=True/False`; returns `{changed, action, skipped}` |
| Download file | `FileStationManager.download()` | ✅ | Binary-safe; returns `{changed, action, file, local_path}` |
| Create folder | `FileStationManager.mkdir()` | ✅ | `force_parent=True` creates intermediate dirs |
| Delete file/folder | `FileStationManager.delete()` | ✅ | Returns `{changed, action}` |
| Ensure folder present/absent | `FileStationManager.ensure()` | ✅ | Idempotent |
| Move / copy | | 🚧 | `SYNO.FileStation.CopyMove` — see TODO below |
| Rename | | 🚧 | `SYNO.FileStation.Rename` — see TODO below |
| Get file info | | 🚧 | `SYNO.FileStation.List` (single path) |
| Search | | 🚧 | `SYNO.FileStation.Search` |

## Storage Management (`SYNO.Storage.Volume`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List volumes | `StorageManager.list_volumes()` | ✅ | Returns volume_path, size, status, fstype |
| Get volume | `StorageManager.get_volume()` | ✅ | Returns None if not found |
| Assert volume present/absent | `StorageManager.ensure()` | ✅ | Read-assert only — volumes cannot be created/deleted via API |

> **Note:** `StorageManager.ensure()` is a read-assert, not a write operation. `changed` is always `False`. Volumes are managed via DSM Storage Manager UI.

## Quota Management (`SYNO.Core.Quota`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| Get user quota | `QuotaManager.get_user_quota()` | ✅ | Per volume |
| Get group quota | `QuotaManager.get_group_quota()` | ✅ | Per volume |
| Get quota (generic) | `QuotaManager.get_quota()` | ✅ | subject_type: "user" or "group" |
| Set user quota | `QuotaManager.set_user_quota()` | ✅ | MB; 0 = unlimited |
| Set group quota | `QuotaManager.set_group_quota()` | ✅ | MB; 0 = unlimited |
| Ensure quota | `QuotaManager.ensure()` | ✅ | Idempotent; state="present"/"absent" |

## Bandwidth Management (`SYNO.Core.BandwidthControl`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| Get user limit | `BandwidthManager.get_user_limit()` | ✅ | Per protocol |
| Get group limit | `BandwidthManager.get_group_limit()` | ✅ | Per protocol |
| Get limit (generic) | `BandwidthManager.get_limit()` | ✅ | owner_type: "local_user" or "local_group" |
| Get all limits | `BandwidthManager.get()` | ✅ | Returns list |
| Set (generic) | `BandwidthManager.set()` | ✅ | |
| Set user bandwidth | `BandwidthManager.set_user()` | ✅ | policy, upload/download limits, schedule |
| Set group bandwidth | `BandwidthManager.set_group()` | ✅ | policy, upload/download limits, schedule |
| Disable user bandwidth | `BandwidthManager.disable_user()` | ✅ | Sets policy="disabled" |
| Disable group bandwidth | `BandwidthManager.disable_group()` | ✅ | Sets policy="disabled" |
| Ensure user bandwidth | `BandwidthManager.ensure_user()` | ✅ | Idempotent |
| Ensure group bandwidth | `BandwidthManager.ensure_group()` | ✅ | Idempotent |

## Traffic Control (`SYNO.Core.TrafficControl`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| Load rules | `TrafficControlManager.load()` | ✅ | Per adapter |
| Save rules | `TrafficControlManager.save()` | ✅ | Full rule list replace |
| Add rule | `TrafficControlManager.add_rule()` | ✅ | Auto-increments id |
| Remove rule | `TrafficControlManager.remove_rule()` | ✅ | By rule id |
| Clear rules | `TrafficControlManager.clear_rules()` | ✅ | Removes all rules for an adapter |
| Ensure rule present/absent | `TrafficControlManager.ensure_rule()` | ✅ | Idempotent |

## Share Permissions (`SYNO.Core.Share.Permission`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List permissions | `SharePermissionManager.list()` | ✅ | Users + groups, returns perm string |
| Set single permission | `SharePermissionManager.set()` | ✅ | Per user or group |
| Set bulk permissions | `SharePermissionManager.set_bulk()` | ✅ | Atomic replace for users + groups |
| Ensure permission present/absent | `SharePermissionManager.ensure()` | ✅ | Idempotent, Ansible-style |

## System & Security (`SYNO.Core.*`)

| Feature | API | Status | Notes |
|---|---|---|---|
| Get system info (model, DSM version, serial) | `SystemManager.get_info()` | ✅ | SYNO.DSM.Info + SYNO.Core.System fallback — **NetBox automation** |
| System ensure (fact gathering) | `SystemManager.ensure()` | ✅ | Read-only noop — Ansible fact gather |
| List installed packages | `SYNO.Core.Package` | 🚧 | Useful for security audit automation |
| Firewall status / rules | `SYNO.Core.Security.Firewall` | 🚧 | |
| SSH / terminal config | `SYNO.Core.Terminal` | 🚧 | Enable/disable SSH, port, password auth toggle |
| DSM update status | `SYNO.Core.SynoUpdate` | 🚧 | |
| Security scan | `SYNO.SecurityScan` | 🚧 | |
| Scheduled tasks | `SYNO.Core.TaskScheduler` | 🚧 | |
| Email notification config | `SYNO.Core.Notification.Mail` | 🚧 | |

## Credential Management

| Feature | Class | Status | Notes |
|---|---|---|---|
| Env / .env file | `EnvCredentialProvider` | ✅ | python-dotenv optional |
| HashiCorp Vault | `VaultCredentialProvider` | ✅ | Requires hvac |
| Auto-detect | `get_credentials()` | ✅ | Vault > env priority |
| Azure Key Vault | | 🚧 | Future provider |
| AWS Secrets Manager | | 🚧 | Future provider |

---

## TODO — Next implementations

Priority order based on platform value:

| Priority | Feature | API | Rationale |
|---|---|---|---|
| ~~HIGH~~ | ~~System info (model, version, serial, uptime)~~ | ~~`SYNO.Core.System`~~ | ✅ Implemented — `SystemManager.get_info()` |
| HIGH | SSH / terminal config | `SYNO.Core.Terminal` | Security hardening automation — disable password auth, set port |
| MEDIUM | Move / copy files | `SYNO.FileStation.CopyMove` | Terraform state management — cross-share ops |
| MEDIUM | Rename file/folder | `SYNO.FileStation.Rename` | FileStation completeness |
| LOW | List installed packages | `SYNO.Core.Package` | Security audit — detect EOL packages (e.g. Python 2.7) |
| LOW | Firewall status | `SYNO.Core.Security.Firewall` | Verify firewall enabled — DSM hardening checks |
| LOW | Update status | `SYNO.Core.SynoUpdate` | Alert when DSM version is behind |
| FUTURE | Ansible collection | — | Phase 2 — see docs/ansible-roadmap.md |
| FUTURE | Vault AppRole auth | — | Phase 2 — blocked until Vault deployed |
