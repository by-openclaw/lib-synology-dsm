# Integration Tests — Agent Context

## Credentials

Loaded from `infra-synology-nas.json` (KV `fields` block) via `conftest.py`.
Default path: `~/.openclaw/workspace/infra/secrets/infra-synology-nas.json`
Override: `export NAS_CREDS_JSON=/path/to/infra-synology-nas.json`

## Fixtures

| Fixture | Account | Group | Role |
|---|---|---|---|
| `dsm_client` | `svc-rune` | administrators | Executor — full CRUD |
| `audit_client` | `svc-opus` | users | Auditor — read-only |

## svc-opus audit coverage (NEXT STEP)

`audit_client` fixture is wired and ready. The following tests need to be written:

### What to test with `audit_client`

1. **Read ops succeed** — list users, list groups, list shares, list FileStation
2. **Write ops are blocked** — create/update/delete user, create share, upload file
   - Expected: `DSMPermissionError` (code 403) or HTTP 105 (write blocked)
3. **ensure() with svc-opus** — ensure(state="present") on existing resource → `{"changed": False}` (noop, read path only)

### File to create

`tests/integration/test_audit_client.py`

### Pattern to follow

```python
import pytest
from synology_dsm.exceptions import DSMPermissionError

@pytest.mark.integration
def test_audit_can_list_users(audit_client):
    from synology_dsm.users import UserManager
    u = UserManager(audit_client)
    users = u.list()
    assert isinstance(users, list)

@pytest.mark.integration
def test_audit_cannot_create_user(audit_client):
    from synology_dsm.users import UserManager
    u = UserManager(audit_client)
    with pytest.raises(DSMPermissionError):
        u.ensure("test-audit-block", state="present", password="Tmp123!")
```

Run audit tests only:
```bash
NAS_CREDS_JSON=~/.openclaw/workspace/infra/secrets/infra-synology-nas.json \
pytest tests/integration/test_audit_client.py -v
```
