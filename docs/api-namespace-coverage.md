# API Namespace Coverage — v1 vs v2 vs NAS Available

> **Source:** `synology-api-list-query.json` (DS1513+ DSM 7.1.1 — 757 APIs)
> **Date:** 2026-03-31
> **Purpose:** Map every API namespace to implementation status and priority

---

## How to read this table

- **APIs:** Number of SYNO.* endpoints in this namespace
- **v1:** Current lib (synology_dsm) — what's implemented
- **v2 PoC:** New pattern (synology_dsm_v2) — what's proven
- **Methods:** How many methods the manager needs (5 base + ensure + sub-entity methods)
- **Complexity:** LOW = simple CRUD, MEDIUM = sub-entities or special auth, HIGH = compound requests or streaming
- **Priority:** Who needs it (Ansible, NetBox, Authentik, etc.)

---

## Implemented namespaces

| Namespace | APIs | v1 manager | v2 PoC | Methods (v1) | Complexity | ensure() pattern |
|---|---|---|---|---|---|---|
| `SYNO.API.Auth` | 8 | ✅ DSMClient | ✅ DSMClient | login, logout, request | LOW | N/A (auth) |
| `SYNO.Core.User` | 8 | ✅ UserManager | ✅ UserManager | 6 + list_groups, add_to_group, remove_from_group, disable | MEDIUM | ✅ Proven both |
| `SYNO.Core.Group` | 4 | ✅ GroupManager | ✅ CoreGroupManager | 3 public + membership private | MEDIUM | ✅ Proven both |
| `SYNO.Core.Share` | 10 | ✅ ShareManager | ✅ CoreShareManager | 3 public (shareinfo JSON create) | HIGH (compound) | ✅ Proven both |
| `SYNO.Core.Share.Permission` | 1 | ✅ SharePermissionManager | ❌ | 4 (list, set, set_bulk, ensure) | MEDIUM | Same as User |
| `SYNO.Core.FileServ.NFS` | 5 | ✅ NFSManager | ✅ CoreFileServNFSManager | 3 public (per-hostname ensure) | MEDIUM | ✅ Proven both |
| `SYNO.FileStation.*` | 30+ | ✅ FileStationManager | ✅ FileStationManager | 3 public + upload/download private | HIGH (multipart upload) | ✅ Proven both |
| `SYNO.Core.Quota` | 1 | ✅ QuotaManager | ❌ | 6 (get/set user/group, ensure) | LOW | Same as User |
| `SYNO.Core.BandwidthControl` | 3 | ✅ BandwidthManager | ❌ | 14 (get/set user/group, ensure_user/group, disable) | MEDIUM | Same — per user/group variant |
| `SYNO.Core.Storage.Volume` | 1 | ✅ StorageManager | ❌ | 3 (list_volumes, get_volume, ensure) | LOW | Read-assert only |
| `SYNO.Core.Network.TrafficControl` | 2 | ✅ TrafficControlManager | ❌ | 6 (load, save, add_rule, remove_rule, clear_rules, ensure_rule) | MEDIUM | Same — match by port/protocol |
| `SYNO.Core.System` | 6 | ✅ SystemManager | ❌ | 2 (get_info, ensure) | LOW | Read-only |
| `SYNO.DSM.Info` | 1 | ✅ SystemManager | ❌ | (included above) | LOW | — |

---

## Not implemented — candidates for v2

| Namespace | APIs | Candidate manager | Methods needed | Complexity | Consumer |
|---|---|---|---|---|---|
| `SYNO.Core.Security.Firewall` | 7 | FirewallManager | 6 (list profiles, list rules, set rules, ensure) | MEDIUM | Ansible hardening, NIS2 compliance |
| `SYNO.Core.Security.AutoBlock` | 2 | AutoBlockManager | 3 (list, get_rules, set) | LOW | Monitoring, security |
| `SYNO.Core.Certificate` | 7 | CertificateManager | 5 (list, get, create/upload, delete, ensure) | MEDIUM | step-ca integration, TLS strategy |
| `SYNO.Core.Package` | 16 | PackageManager | 5 (list, get, install, uninstall, ensure) | MEDIUM | Automation — ensure packages installed |
| `SYNO.Core.Terminal` | 1 | TerminalManager | 2 (get, set) | LOW | SSH config — port, enable/disable |
| `SYNO.Core.Network` | 25+ | NetworkManager | 6+ (get interfaces, set, VPN config) | HIGH | Network automation |
| `SYNO.Core.DDNS` | 6 | DDNSManager | 4 (list providers, get record, set, ensure) | LOW | DNS management |
| `SYNO.Core.Notification` | 16 | NotificationManager | 5 (get mail/push/sms config, set, test) | MEDIUM | Alerting setup |
| `SYNO.Core.Directory.LDAP` | 5 | LDAPManager | 4 (get config, set, test, ensure) | MEDIUM | Authentik LDAP integration |
| `SYNO.Core.Directory.SSO` | 4 | SSOManager | 3 (get config, set, ensure) | MEDIUM | Authentik SSO integration |
| `SYNO.Core.Upgrade` | 12 | UpgradeManager | 3 (check, get status, apply) | MEDIUM | DSM version management |
| `SYNO.Core.Hardware` | 14 | HardwareManager | 5 (fan, hibernation, power schedule, UPS) | LOW | Monitoring |
| `SYNO.LogCenter` | 5 | LogManager | 3 (list, get, configure) | LOW | Audit trail, SIEM |
| `SYNO.Core.ISCSI` | 7 | ISCSIManager | 6 (LUN, Target, Host CRUD) | HIGH | Storage provisioning |
| `SYNO.Core.Sharing` | 4 | SharingManager | 4 (list, create link, delete, ensure) | LOW | File sharing links |
| `SYNO.FileStation.CopyMove` | 1 | (FileStationManager) | +2 (copy, move) | MEDIUM | File automation |
| `SYNO.FileStation.Search` | 2 | (FileStationManager) | +1 (search) | LOW | File discovery |
| `SYNO.FileStation.Compress` | 1 | (FileStationManager) | +1 (compress) | LOW | Archive creation |
| `SYNO.FileStation.Rename` | 1 | (FileStationManager) | +1 (rename) | LOW | File management |

---

## Out of scope (separate lib or not needed)

| Namespace | APIs | Why out of scope |
|---|---|---|
| `SYNO.SurveillanceStation.*` | 80+ | Separate product — `lib-synology-surveillance` if needed |
| `SYNO.Backup.*` | 20+ | Hyper Backup — separate concern |
| `SYNO.C2FS.*` | 8 | Synology C2 cloud — not self-hosted |
| `SYNO.DR.*` | 3 | Disaster Recovery — separate concern |
| `SYNO.AntiVirus.*` | 9 | Antivirus package — not infra |
| `SYNO.ActiveInsight.*` | 4 | Synology cloud analytics — not self-hosted |
| `SYNO.AudioPlayer.*` | 2 | Media — not infra |
| `SYNO.VideoPlayer.*` | 2 | Media — not infra |
| `SYNO.Finder.*` | 12 | Search indexing — not infra |
| `SYNO.PersonMailAccount.*` | 4 | Email — not infra |
| `SYNO.Core.Desktop.*` | 8 | DSM UI — not automatable |
| `SYNO.Core.Theme.*` | 5 | DSM UI theming — not infra |
| `SYNO.Core.PhotoViewer` | 1 | Media — not infra |
| `SYNO.Core.MediaIndexing.*` | 5 | Media indexing — not infra |
| `SYNO.AME.*` | 4 | Advanced Media Extensions — not infra |
| `SYNO.Entry.Request` | 2 | Compound request — used internally by ShareManager, not a manager |

---

## Complexity breakdown for v2 migration

**The ensure() pattern is identical across all managers.** The complexity is NOT in ensure() — it's in:

| Complexity | What makes it complex | Managers |
|---|---|---|
| **LOW** | Simple CRUD — `request(API, "list/set/create/delete")` | Quota, Storage, System, Terminal, AutoBlock, DDNS, Hardware, Log |
| **MEDIUM** | Sub-entities (members, rules, permissions) or variant methods (per-user, per-group) | User, Group, SharePermission, NFS, Bandwidth, TrafficControl, Firewall, Certificate, Package, LDAP, SSO |
| **HIGH** | Compound requests (batch API calls) or streaming (multipart upload/download) | Share (compound), FileStation (multipart), ISCSI, Network |

**Effort estimate per manager:**

| Complexity | Methods | ensure() | Tests | Total effort |
|---|---|---|---|---|
| LOW | 5-6 (trivial wrappers) | Copy from UserManager, change diff fields | 15-20 tests | ~1 hour |
| MEDIUM | 6-10 (sub-entity methods) | Same pattern + sub-entity ensure variants | 25-35 tests | ~2 hours |
| HIGH | 10+ (compound/streaming) | Same pattern but compound/multipart logic | 35-50 tests | ~4 hours |

---

## Summary

| Category | Namespaces | APIs | Managers | v1 done | v2 done |
|---|---|---|---|---|---|
| **Implemented** | 13 | ~90 | 12 | 12 | 5 (User + Group + Share + NFS + FileStation) |
| **Candidates** | 18 | ~150 | 15 | 0 | 0 |
| **Out of scope** | ~30 | ~500+ | — | — | — |
| **Total on NAS** | ~60 | 757 | — | — | — |

---

*Sort the "candidates" table by your priority. That becomes the v2 implementation roadmap.*
