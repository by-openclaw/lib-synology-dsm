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
  feature-coverage.md  ← implemented vs planned features table
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
- User: rune-api / YOUR_PASSWORD (session=DSM)
- Credentials file: /home/by-systems/.openclaw/workspace/infra/secrets/.synology.env
- rune-audit: DELETED (redundant)

## Blocked items
- Share CRUD (create/delete/update): needs rune-api in administrators group in DSM
- NFS set: same
- Rename rune-api → svc-rune-dsm: tracked in platform-setup#56

## Current version: 0.3.0 (+ unreleased update/ensure methods → will be 0.4.0)

## References
- Community API reference: https://github.com/pmilano1/synology-dsm-api
- On-NAS API explorer: https://10.6.224.6:5001/webapi/entry.cgi?api=SYNO.API.Info&version=1&method=query&query=all
