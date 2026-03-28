# CLAUDE.md — lib-synology-dsm Agent Notes

## What this repo is
Python library for Synology DSM API automation. Part of the BY-SYSTEMS platform stack.
Used by: platform-setup runbooks, future ansible-collection-synology, NetBox webhooks.

## Repo structure
```
src/synology_dsm/
  __init__.py          ← exports all public classes + version
  client.py            ← DSMClient (session management, auth v7)
  credentials.py       ← EnvCredentialProvider, VaultCredentialProvider, get_credentials()
  users.py             ← UserManager (CRUD + ensure)
  groups.py            ← GroupManager (CRUD + membership + ensure)
  shares.py            ← ShareManager (CRUD + NFS + ensure)
docs/
  api-versions.md      ← tested API version table
  api-reference.md     ← method reference
  credentials.md       ← credential provider guide
  feature-coverage.md  ← implemented vs planned features table (primary reference)
  references.md        ← API docs + community links
tests/
  test_client.py       ← unit tests
  integration/
    test_live_nas.py   ← live NAS tests (urllib only, no httpx)
```

## Key decisions
- Auth: SYNO.API.Auth v7 via entry.cgi (NOT auth.cgi)
- Session: always "DSM" for admin ops
- Delete ops: DSM requires JSON array format: `name='["value"]'`
- ensure(state=present/absent): idempotent Ansible-style pattern on all managers
- Vault-first credentials: production uses VaultCredentialProvider
- httpx NOT available on Rune's host — integration tests use urllib only

## Test NAS
- Host: 10.6.224.6:5001 (HTTPS)
- User: rune-api / BySyst3ms_ (session=DSM)
- Credentials file: /home/by-systems/.openclaw/workspace/infra/secrets/.synology.env
- rune-audit: DELETED (redundant — 2026-03-27)

## rune-api group membership — decision (2026-03-27)
- **rune-api is in `administrators` group** — required for share CRUD + NFS management
- DSM has no finer-grained permission model for share creation without admin
- NAS is internal-only (no QuickConnect, firewall being hardened per SYN-001)
- Accepted risk for PoC phase; revisit when Vault + least-privilege audit is done
- **Future rename:** rune-api → svc-rune-dsm (tracked in platform-setup#56)
  - Keep in administrators group after rename — same rationale applies
  - DSM does not support renaming users; requires delete + recreate

## Pending items
- Share CRUD live test: pending confirmation rune-api is added to administrators in DSM UI
  - Control Panel → User & Group → Group → administrators → Edit → Members → Add rune-api
- Rename rune-api → svc-rune-dsm: platform-setup#56 (low priority, before prod use)
- SSH pubkey sync via User.Home: explore SYNO.Core.User.Home API for authorized_keys upload

## Current version: 0.4.0

## API discovery
```bash
# List all 757 APIs on DS1513+ DSM 7.1.1 with version ranges
curl -sk "https://10.6.224.6:5001/webapi/query.cgi?api=SYNO.API.Info&method=query&version=1&query=all"
```

## References
- Community API reference: https://github.com/pmilano1/synology-dsm-api
- Feature coverage table: docs/feature-coverage.md
