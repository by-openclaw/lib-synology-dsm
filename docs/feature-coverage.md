# Feature Coverage

Tracks implemented vs planned DSM API coverage for lib-synology-dsm.
Updated as features are added.

**Legend:** ✅ Implemented | 🚧 Planned | ❌ Not supported | ➖ N/A

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

| Feature | Method | Status | Notes |
|---|---|---|---|
| List shares | via FileStation session | ✅ | Tested in integration test |
| List directory | | 🚧 | SYNO.FileStation.List |
| Upload file | | 🚧 | SYNO.FileStation.Upload |
| Download file | | 🚧 | SYNO.FileStation.Download |
| Create folder | | 🚧 | SYNO.FileStation.CreateFolder |
| Delete file/folder | | 🚧 | SYNO.FileStation.Delete |
| Move/copy | | 🚧 | SYNO.FileStation.CopyMove |

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
2. `SYNO.FileStation.List` — list directory (needed for backup verification)
3. `SYNO.Core.Package` — list installed packages (security audit automation)

Blocked on admin access:
- Share CRUD (need rune-api in administrators group)
- NFS set (same)
