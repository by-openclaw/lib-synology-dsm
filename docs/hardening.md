# API Account Hardening Guide

## Context

`rune-api` (future: `svc-rune-dsm`) requires the `administrators` group.
This is a DSM constraint — no workaround exists. Without it, all write operations
return error 119. Harden the account instead.

## Confirmed requirements (tested 2026-03-28)

| Requirement | Value | Why |
|---|---|---|
| Group: administrators | ✅ Required | Write ops (share/user/group CRUD, NFS) |
| Group: users | ✅ Required | Basic authentication |
| Group: svc-automation | ✅ Recommended | Audit identity — filter logs by service accounts |
| App: DSM | Allow | Authentication + admin API |
| App: File Station | Allow | File operations |
| App: all others | Deny | Least privilege |

## Password policy

| Setting | Value |
|---|---|
| Password length | 30+ characters, random |
| Storage | HashiCorp Vault — `secret/data/synology/nas01` |
| Rotation | Automated via Vault lease/rotation (future) |
| Password expiry in DSM | **Disabled** — rotate via Vault instead |
| User cannot change password | **Enabled** — prevent accidental change |
| 2FA | **Disabled** — breaks API authentication |

## Network-level restrictions

### App privilege by IP (DSM Control Panel → Application Privileges)

Restrict `rune-api` to automation subnets only:

| Network | CIDR | Purpose |
|---|---|---|
| OOB | 10.6.224.0/20 | Management network — Rune VM, Proxmox nodes |
| MGMT | 10.6.240.0/20 | Application management network |

**How to configure:**
1. Control Panel → Application Privileges
2. Find DSM → Edit → add IP restriction for rune-api
3. Allow: 10.6.224.0/20, 10.6.240.0/20
4. Deny: all others

### Auto-block (global — applies to all accounts)

Control Panel → Security → Account → Enable auto-block:
- After X failed logins → block IP
- Recommended: 5 attempts, 10 minute block
- Note: this affects all users, not only rune-api

### Log Center — audit rune-api activity

Control Panel → Log Center → enable:
- File access logs
- User/group change logs
- Filter/export by user: rune-api

## Summary

```
rune-api (future: svc-rune-dsm)
 ├── Groups
 │   ├── administrators  ← required (write ops)
 │   ├── users           ← required (auth)
 │   └── svc-automation  ← identity label (audit)
 ├── Applications
 │   ├── DSM        = Allow
 │   ├── FileStation = Allow
 │   └── others     = Deny
 ├── Password: 30+ chars, Vault-managed
 ├── 2FA: Disabled
 ├── Expiry: Disabled (Vault rotation)
 ├── IP restriction: 10.6.224.0/20 + 10.6.240.0/20
 └── No interactive shell needed
```

## Rename roadmap

Current: `rune-api` → Target: `svc-rune-dsm`

DSM does not support renaming users — requires delete + recreate.
Track: platform-setup#56 — do before any production use.
