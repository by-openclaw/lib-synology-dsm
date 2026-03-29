# Feature Coverage

Tracks implemented vs planned DSM API coverage for lib-synology-dsm.
Updated as features are added.

**Legend:** ✅ Implemented | 🚧 Planned | ❌ Not supported | ➖ N/A

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

## User Management (`SYNO.Core.User`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List users | `UserManager.list()` | ✅ | |
| Create user | `UserManager.create()` | ✅ | |
| Update user | `UserManager.update()` | ✅ | description, email, password |
| Delete user | `UserManager.delete()` | ✅ | JSON array format required |
| Disable user | `UserManager.disable()` | ✅ | Preferred over delete |
| Ensure present/absent | `UserManager.ensure()` | ✅ | Idempotent, Ansible-style |
| Add to group | `UserManager.add_to_group()` | ✅ | Delegates to GroupManager |
| Remove from group | `UserManager.remove_from_group()` | ✅ | Delegates to GroupManager |
| Change password | `UserManager.update(password=)` | ✅ | Via update() |
| List user details | | 🚧 | email, 2fa_status, expired fields |
| Reset 2FA | | 🚧 | SYNO.Core.User.OTP |
| Set home folder | | 🚧 | homes share integration |

## Group Management (`SYNO.Core.Group`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List groups | `GroupManager.list()` | ✅ | |
| Create group | `GroupManager.create()` | ✅ | |
| Update group | `GroupManager.update()` | ✅ | description |
| Delete group | `GroupManager.delete()` | ✅ | JSON array format required |
| Get group details | `GroupManager.get()` | ✅ | |
| Add member | `GroupManager.add_member()` | ✅ | Fetches current list first |
| Remove member | `GroupManager.remove_member()` | ✅ | Fetches current list first |
| List members | `GroupManager.list_members()` | ✅ | |
| Ensure present/absent | `GroupManager.ensure()` | ✅ | Idempotent, Ansible-style |
| Set group permissions | | 🚧 | Share-level ACL |

## Shared Folder Management (`SYNO.Core.Share`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| List shares | `ShareManager.list()` | ✅ | |
| Create share | `ShareManager.create()` | ✅ | Requires admin |
| Update share | `ShareManager.update()` | ✅ | desc, hidden, recycle_bin — requires admin |
| Delete share | `ShareManager.delete()` | ✅ | Requires admin |
| Ensure present/absent | `ShareManager.ensure()` | ✅ | Idempotent — requires admin |
| Set NFS permission | `ShareManager.set_nfs_permission()` | ✅ | Requires admin |
| Get NFS rules | `ShareManager.get_nfs_rules()` | ✅ | |
| Set SMB/Windows ACL | | 🚧 | SYNO.Core.Share.Permission |
| Set quota | | 🚧 | SYNO.Core.Share — quota param |
| Enable encryption | | 🚧 | Encryption at rest |
| Clone/snapshot | | ❌ | Not supported via Core API |

## File Operations (`SYNO.FileStation`)

> **Auth quirk (DS1513+ DSM 7.x):** `SynoToken` must be in URL query string; session as cookie `id=`; field `path` not `dest_folder_path`. Login must use `session=DSM`. All handled transparently by `FileStationManager`.

| Feature | Method | Status | Notes |
|---|---|---|---|
| List shares | `FileStationManager.list_shares()` | ✅ | |
| List directory | `FileStationManager.list()` | ✅ | Supports `additional`: size, time, owner, perm, real_path, type |
| Upload file | `FileStationManager.upload()` | ✅ | `overwrite=True/False`; returns `skipped` flag when file exists and overwrite=False |
| Download file | `FileStationManager.download()` | ✅ | Binary-safe streaming |
| Create folder | `FileStationManager.mkdir()` | ✅ | `force_parent=True` creates intermediate dirs |
| Delete file/folder | `FileStationManager.delete()` | ✅ | Returns DSM task id |
| Move/copy | | 🚧 | SYNO.FileStation.CopyMove |
| Rename | | 🚧 | SYNO.FileStation.Rename |
| Get file info | | 🚧 | SYNO.FileStation.List — single path |
| Search | | 🚧 | SYNO.FileStation.Search |

## System & Security (`SYNO.Core.*`)

| Feature | Method | Status | Notes |
|---|---|---|---|
| Get system info | | 🚧 | SYNO.Core.System — model, DSM version |
| Package list | | 🚧 | SYNO.Core.Package |
| Firewall status | | 🚧 | SYNO.Core.Security.Firewall |
| SSH config | | 🚧 | SYNO.Core.Terminal |
| Update status | | 🚧 | SYNO.Core.SynoUpdate |
| Security scan | | 🚧 | SYNO.SecurityScan |
| Scheduled tasks | | 🚧 | SYNO.Core.TaskScheduler |
| Email notification | | 🚧 | SYNO.Core.Notification.Mail |

## Credential Management

| Feature | Class | Status | Notes |
|---|---|---|---|
| Env / .env file | `EnvCredentialProvider` | ✅ | python-dotenv optional |
| HashiCorp Vault | `VaultCredentialProvider` | ✅ | Requires hvac |
| Auto-detect | `get_credentials()` | ✅ | Vault > env priority |
| Azure Key Vault | | 🚧 | Future provider |
| AWS Secrets Manager | | 🚧 | Future provider |

## Missing features — priorities

High value, low effort (implement next):
1. `SYNO.Core.System` — get model/DSM version/serial (useful for audit automation)
2. `SYNO.Core.Package` — list installed packages (security audit automation)
3. `SYNO.FileStation.CopyMove` — move/copy files (rename + cross-share ops)

Done (v0.6.x):
- ✅ `FileStationManager` — full CRUD: list, upload, download, mkdir, delete (v0.6.0–0.6.1)
