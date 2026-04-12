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
| Set group share permissions | | 🚧 | SYNO.Core.Share.Permission — ACL |

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

## System & Security (`SYNO.Core.*`)

| Feature | API | Status | Notes |
|---|---|---|---|
| Get system info (model, DSM version, serial) | `SYNO.DSM.Info` | 🚧 | **Priority — needed for NetBox automation** (#33) |
| System utilization (CPU, RAM) | `SYNO.Core.System.Utilization` | 🚧 | Hardware stats |
| System health status | `SYNO.Core.System.Status` | 🚧 | Hardware health check |
| SSH / terminal config | `SYNO.Core.Terminal` | 🚧 | Enable/disable SSH, port, password auth (#34) |
| List/install/remove packages | `SYNO.Core.Package` | 🚧 | Package management (#35) |
| Certificate management | `SYNO.Core.Certificate.CRT` | 🚧 | TLS cert import/delete |
| Firewall status / rules | `SYNO.Core.Security.Firewall.Profile` | 🚧 | Firewall policy |
| Security advisor checklist | `SYNO.SecurityAdvisor.Conf.Checklist` | 🚧 | Security posture audit |
| Login activity audit | `SYNO.SecurityAdvisor.LoginActivity` | 🚧 | Auth event log |
| DSM update status | `SYNO.Core.Upgrade.Server` | 🚧 | Update check + apply |
| Auto-update config | `SYNO.Core.Upgrade.AutoUpgrade` | 🚧 | Enable/disable auto-update |
| Scheduled tasks | `SYNO.Core.TaskScheduler` | 🚧 | Create/manage scheduled tasks |
| SNMP config | `SYNO.Core.SNMP` | 🚧 | SNMP enable/community |
| SMB/NFS/FTP service control | `SYNO.Core.FileServ.*` | 🚧 | Enable/disable file services |
| Email notification config | `SYNO.Core.Notification.Mail.Conf` | 🚧 | Alert routing |

## User Policy (`SYNO.Core.User.*`)

| Feature | API | Status | Notes |
|---|---|---|---|
| Password policy | `SYNO.Core.User.PasswordPolicy` | 🚧 | Enforce complexity, min length |
| Password expiry | `SYNO.Core.User.PasswordExpiry` | 🚧 | Max age enforcement |
| Username policy | `SYNO.Core.User.UsernamePolicy` | 🚧 | Character constraints |

## Share ACL (`SYNO.Core.Share.Permission`)

| Feature | API | Status | Notes |
|---|---|---|---|
| Get share ACL | `SYNO.Core.Share.Permission` | 🚧 | Per-user/group RW/deny |
| Set share ACL | `SYNO.Core.Share.Permission` | 🚧 | Full ACL replacement |
| Ensure share ACL | — | 🚧 | Idempotent ensure pattern |

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

| Priority | Feature | API | Issue | Rationale |
|---|---|---|---|---|
| HIGH | System info (model, version, serial) | `SYNO.DSM.Info` | #33 | NetBox automation — populate device record |
| HIGH | SSH / terminal config | `SYNO.Core.Terminal` | #34 | Security hardening — disable password auth, set port |
| HIGH | Share ACL (per user/group) | `SYNO.Core.Share.Permission` | — | Complete share management surface |
| MEDIUM | Move / copy files | `SYNO.FileStation.CopyMove` | — | Cross-share file ops |
| MEDIUM | Package management | `SYNO.Core.Package` | #35 | Idempotent package install/remove |
| MEDIUM | Password policy enforcement | `SYNO.Core.User.PasswordPolicy` | — | Security hardening |
| MEDIUM | Certificate management | `SYNO.Core.Certificate.CRT` | — | TLS lifecycle automation |
| MEDIUM | Retry logic (transient errors) | client | #32 | Resilience — session expiry + network blips |
| LOW | Firewall policy | `SYNO.Core.Security.Firewall.Profile` | — | Verify firewall enabled |
| LOW | DSM update status | `SYNO.Core.Upgrade.Server` | — | Alert when DSM behind |
| LOW | Security advisor checklist | `SYNO.SecurityAdvisor.Conf.Checklist` | — | Compliance audit |
| LOW | Scheduled tasks | `SYNO.Core.TaskScheduler` | — | NAS automation tasks |
| FUTURE | Ansible collection | — | — | Phase 2 — see docs/ansible-roadmap.md |
| FUTURE | Vault AppRole auth | — | — | Phase 2 — blocked until Vault deployed |

---

## API References

| Source | URL | Use for |
|---|---|---|
| Official Synology KB | <https://kb.synology.com/en-us/DG/DSM_Login_Web_API_Guide/2> | Auth spec, ground truth |
| pmilano1/synology-dsm-api | <https://github.com/pmilano1/synology-dsm-api/tree/master/docs/api-reference> | Full API reference |
| n4s4/synology-api | <https://n4s4.github.io/synology-api/docs/apis> | Request/response shape reference |
