# lib-synology-dsm

Python library for Synology DSM API — idempotent CRUD for shared folders, NFS permissions, users, and groups.

**Hardware:** DS1513+ · **DSM:** 7.1.1-42962 Update 9 · **Auth:** SYNO.API.Auth v7

---

## Quick start

```bash
pip install git+https://github.com/by-openclaw/lib-synology-dsm.git

# Smoke test (requires curl + jq)
bash tests/integration/dsm-crud-test.sh

# Full Python integration test
python3 tests/integration/test_live_nas.py
```

---

## DSM account requirements

The API user must be configured in DSM before any write operation will work.

### Groups

| Group | Required | Why |
|---|---|---|
| `administrators` | **Yes** | Share create/delete, NFS rules — fail with 403 without this |
| `users` | Yes | Default group — required for basic auth |

### Application permissions (Control Panel → User & Group → Edit → Applications)

| Application | Permission |
|---|---|
| DSM | **Allow** |
| File Station | **Allow** |
| All others | Deny (default) |

### One-time setup in DSM UI

1. Control Panel → User & Group → select user → Edit
2. **User Groups tab** → check `administrators` + `users`
3. **Applications tab** → DSM = Allow, File Station = Allow
4. Save

### Verify setup

```bash
curl -sk "https://10.6.224.6:5001/webapi/entry.cgi" \
  --data "api=SYNO.API.Auth&version=7&method=login&account=rune-api&passwd=YOUR_PASS&session=DSM&format=sid&enable_syno_token=yes"
# success=true AND synotoken must be a real token (not "--------")
```

---

## Known API quirks (DS1513+ DSM 7.x)

These are documented from live testing — not from official docs.

| API | Issue | Fix |
|---|---|---|
| All write ops | Return 403 without `X-SYNO-TOKEN` header | Login with `enable_syno_token=yes`, send token on every write |
| `SYNO.Core.Share.create` | Flat params (`vol_path`, `desc`) return 403 | Must use `shareinfo` JSON object: `{"name":..,"vol_path":..,"desc":..,"name_org":""}` |
| `SYNO.Core.Group.member_set` | Error 103 (invalid parameter) | Use `SYNO.Core.Group.set` with `members=["user1","user2"]` instead |
| `SYNO.Core.Share.NFS.set` | Error 102 (no such API) | Use `SYNO.Core.FileServ.NFS.SharePrivilege.save` with `share_name=` + `rule=` |
| `SYNO.Core.User.delete` | Requires JSON array | `name=["username"]` not `name=username` |
| `SYNO.Core.Group.delete` | Requires JSON array | Same as user delete |

---

## Usage

### Shares

```python
from synology_dsm import DSMClient
from synology_dsm.shares import ShareManager

with DSMClient("10.6.224.6") as client:
    client.login("rune-api", "password")
    mgr = ShareManager(client)

    # Create
    mgr.create("my-share", volume_path="/volume1", description="My share")

    # Create with permissions + NFS in one call
    mgr.create_with_permissions(
        "my-share",
        owner_user="by-systems",
        owner_group="svc-automation",
        nfs_client="10.6.224.0/20",
        nfs_rw=True,
    )

    # List
    for s in mgr.list():
        print(s["name"])

    # NFS rules
    mgr.set_nfs_permission("my-share", "10.6.224.0/20", rw=True)
    rules = mgr.get_nfs_rules("my-share")

    # Idempotent ensure
    mgr.ensure("my-share", state="present", description="desc")
    mgr.ensure("my-share", state="absent")
```

### Users

```python
from synology_dsm.users import UserManager

with DSMClient("10.6.224.6") as client:
    client.login("rune-api", "password")
    mgr = UserManager(client)

    mgr.create("alice", password="Secret123!", description="Alice")
    mgr.update("alice", description="Alice — updated")
    users = mgr.list()
    mgr.ensure("alice", state="absent")
```

### Groups

```python
from synology_dsm.groups import GroupManager

with DSMClient("10.6.224.6") as client:
    client.login("rune-api", "password")
    mgr = GroupManager(client)

    mgr.create("svc-automation", description="Automation accounts")
    mgr.add_member("svc-automation", "rune-api")   # uses Group.set internally
    mgr.remove_member("svc-automation", "rune-api")
    mgr.ensure("svc-automation", state="absent")
```

---

## Credentials

Never hardcode credentials. Supported patterns:

### `.env` (development)

```bash
cp .env.example .env
```

```python
from synology_dsm.credentials import EnvCredentialProvider
creds = EnvCredentialProvider().get()
```

### HashiCorp Vault (production — Layer 2+)

```python
from synology_dsm.credentials import get_credentials
creds = get_credentials()  # auto-detects Vault when VAULT_ADDR is set
```

### Explicit (tests only)

```python
client.login("rune-api", "password")
```

---

## Testing

```bash
# Bash smoke test — full CRUD cycle, no Python deps needed
bash tests/integration/dsm-crud-test.sh

# Python integration test
python3 tests/integration/test_live_nas.py

# Override NAS target
NAS_HOST=10.6.x.x API_PASS=mypass bash tests/integration/dsm-crud-test.sh
```

**Current test results (2026-03-28):**

| Test | Status |
|---|---|
| Auth (rune-api) | ✅ |
| User create / update / delete | ✅ |
| Group create / members / delete | ✅ |
| Share create / permissions / NFS / delete | ✅ |
| rune-audit login | ⚠️ disabled in DSM — re-enable to test read-only path |

---

## Install

```bash
# From GitHub (current)
pip install git+https://github.com/by-openclaw/lib-synology-dsm.git

# From GitLab Package Registry (when GitLab CE is live — Phase 5)
pip install synology-dsm
```

---

## Modules

| Module | Purpose |
|---|---|
| `client.py` | Session management, auth, `X-SYNO-TOKEN` handling |
| `shares.py` | Shared folder CRUD + NFS + permissions |
| `groups.py` | Group CRUD + membership |
| `users.py` | User CRUD |
| `credentials.py` | Env + Vault credential providers |

---

## References

- DSM API on your NAS: `https://NAS_IP:5001/webapi/entry.cgi?api=SYNO.API.Info&version=1&method=query&query=all`
- Community reference: <https://github.com/pmilano1/synology-dsm-api>
- Platform charter: [ADR-0006](https://github.com/by-openclaw/doc-platform-core/blob/main/docs/adr/0006-platform-charter.md)

---

**Agent:** Rune | **Owner:** @yboujraf | **Org:** [by-openclaw](https://github.com/by-openclaw)
