# CLAUDE.md — lib-synology-dsm Agent Notes

## What this repo is
Python library for Synology DSM API automation. Part of the BY-SYSTEMS platform stack.
Used by: platform-setup runbooks, future ansible-collection-synology, NetBox webhooks.

## Repo structure
```
src/synology_dsm/
  __init__.py          ← exports all public classes + version
  client.py            ← DSMClient (session management, auth v6 + synotoken)
  credentials.py       ← EnvCredentialProvider, VaultCredentialProvider, get_credentials()
  users.py             ← UserManager (CRUD + ensure)
  groups.py            ← GroupManager (CRUD + membership + ensure)
  shares.py            ← ShareManager (CRUD + NFS + permissions + ensure)
docs/
  api-versions.md      ← tested API version table (ground truth)
  api-reference.md     ← method reference with confirmed working signatures
  credentials.md       ← credential provider guide
  feature-coverage.md  ← implemented vs planned features table (primary reference)
  references.md        ← API docs + community links
tests/
  test_client.py       ← unit tests
  integration/
    test_live_nas.py   ← live NAS tests (urllib only, no httpx)
    test_full_crud.sh  ← comprehensive bash CRUD test (auth/user/group/share/NFS)
```

## Key decisions
- Auth: SYNO.API.Auth v6 via entry.cgi (NOT auth.cgi), with `enable_syno_token=yes`
- SynoToken: all write requests require `X-SYNO-TOKEN: <synotoken>` header
- Session: always "DSM" for admin ops
- Delete ops: DSM requires JSON array format: `name='["value"]'`
- ensure(state=present/absent): idempotent Ansible-style pattern on all managers
- Vault-first credentials: production uses VaultCredentialProvider
- httpx NOT available on Rune's host — integration tests use urllib only
- Compound requests (SYNO.Entry.Request): required for share permissions + NFS (see below)

## Compound request pattern (confirmed working)
Permission and NFS writes use batched compound calls:
1. The permission/NFS operation
2. `SYNO.Core.Share.set` with full `shareinfo` to finalize

Always check `data.has_fail == false` (not top-level `success`) for compound call results.

## Share create — required format (DSM 7.x)
`shareinfo` must be a JSON object with `name_org` field:
```json
{"name": "SHARENAME", "vol_path": "/volume1", "desc": "", "name_org": ""}
```
Omitting `name_org` returns HTTP 403.

## NFS API details
- API: `SYNO.Core.FileServ.NFS.SharePrivilege`
- Set: `method=save`, param: `share_name` (NOT `sharename` — causes error 2301)
- Get: `method=load`, param: `share_name`

## Test NAS
- Host: 10.6.224.6:5001 (HTTPS)
- User: rune-api / BySyst3ms_ (session=DSM, in `administrators` group)
- Credentials file: /home/by-systems/.openclaw/workspace/infra/secrets/.synology.env

## rune-api group membership — decision (2026-03-27)
- **rune-api is in `administrators` group** — required for share CRUD + NFS management
- DSM has no finer-grained permission model for share creation without admin
- NAS is internal-only (no QuickConnect, firewall being hardened per SYN-001)
- Accepted risk for PoC phase; revisit when Vault + least-privilege audit is done
- **Future rename:** rune-api → svc-rune-dsm (tracked in platform-setup#56)

## Pending items
- Rename rune-api → svc-rune-dsm: platform-setup#56 (low priority, before prod use)
- SSH pubkey sync via User.Home: explore SYNO.Core.User.Home API for authorized_keys upload
- Group membership: `SYNO.Core.Group.member_set` returns error 103 on DSM 7.1.1 (method not implemented) — investigate alternative or version upgrade path

## Current version: 0.5.0

## API discovery
```bash
# List all 757 APIs on DS1513+ DSM 7.1.1 with version ranges
curl -sk "https://10.6.224.6:5001/webapi/query.cgi?api=SYNO.API.Info&method=query&version=1&query=all"
```

## References
- Community API reference: https://github.com/pmilano1/synology-dsm-api
- Feature coverage table: docs/feature-coverage.md

---

## Agent Onboarding (Rune / BY-SYSTEMS)

- **AGENTS.md:** [`AGENTS.md`](AGENTS.md) — generic agent onboarding file (read by Codex, Claude Code, and all agents)
- **Owner:** @yboujraf
- **Org:** [by-openclaw](https://github.com/by-openclaw)
- **Platform agent:** Rune (DevOps familiar)

AGENTS.md contains: commit standards, what NOT to do, API gotchas summary, and GitHub link.
