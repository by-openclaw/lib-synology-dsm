# Contributing to lib-synology-dsm

## Development setup

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Running unit tests

Unit tests are fully offline — no NAS required. All HTTP calls are mocked.

```bash
# Run unit tests with coverage report
pytest tests/unit/ -v

# Terminal output: per-test PASS/FAIL + coverage table
# HTML report: open htmlcov/index.html in browser after run
# Gate: fails if total coverage < 80%
```

Coverage summary:

| Module | Target | Notes |
|---|---|---|
| `client.py` | ≥80% | urllib only — no external HTTP deps |
| `credentials.py` | ≥80% | env vars + Vault providers |
| `filestation.py` | ≥80% | upload/download/list/mkdir/delete |
| `groups.py` | 100% | full ensure/CRUD/members |
| `nfs.py` | 100% | get_rules |
| `shares.py` | ≥80% | full ensure/CRUD/permissions |
| `users.py` | ≥80% | full ensure/CRUD |

---

## Running integration tests (live NAS required)

Integration tests talk to a real Synology NAS. They create and delete test artifacts
in controlled locations. **They never touch existing shares or user data.**

### What the integration test creates and cleans up

| Object | Name | Cleaned up |
|---|---|---|
| DSM user | `rune-test-tmp` | ✅ deleted at end |
| DSM group | `rune-test-group` | ✅ deleted at end |
| Shared folder | `rune-test-share` | ✅ deleted at end |
| FileStation folder | `/{TEST_SHARE}/rune-test-fs-tmp/` | ✅ deleted at end |
| FileStation file | `rune-test-upload.txt` inside above | ✅ deleted with folder |

### Prerequisites on the NAS

1. Create a DSM admin user (e.g. `your-dsm-user`) in DSM → Control Panel → User & Group
2. Add it to the `administrators` group
3. Enable: Control Panel → User & Group → `your-dsm-user` → Applications → DSM = **Allow**
4. Create a read-only audit user (e.g. `your-audit-user`) — normal user, no admin rights
5. NFS service must be enabled if testing NFS rules: Control Panel → File Services → NFS

### Setup env vars

```bash
cp .env.example .env
# Edit .env with your values:
#   NAS_HOST, API_USER, API_PASS, AUDIT_USER, AUDIT_PASS, NFS_CLIENT
```

### Run

```bash
# Option 1 — via env file (if python-dotenv installed)
pip install python-dotenv
source .env && python3 tests/integration/test_live_nas.py

# Option 2 — inline env vars
NAS_HOST=192.168.1.100 \
API_USER=your-dsm-user \
API_PASS=your-password \
AUDIT_USER=your-audit-user \
AUDIT_PASS=your-audit-password \
NFS_CLIENT=192.168.1.0/24 \
TEST_USER_PASS=TmpPass123! \
python3 tests/integration/test_live_nas.py
```

### Output format

```
============================================================
  lib-synology-dsm — Live NAS Integration Test
  Target: https://192.168.1.100:5001/webapi/entry.cgi
============================================================

── Section 1: Auth v7 ─────────────────────────────
  ✅  your-dsm-user login  sid=abc123…
  ✅  your-dsm-user logout
  ✅  your-dsm-user re-login (for subsequent tests)

  ...

── Summary ───────────────────────────────────────
  Total: 42  |  ✅ 40  |  ⚠️ 2  |  ❌ 0
```

- `✅` = PASS
- `⚠️` = WARN (non-blocking — e.g. optional feature not configured on NAS)
- `❌` = FAIL (blocking)

Exit code: `0` if no failures, `1` if any `❌`.

---

## Code standards

- **No external HTTP dependencies** — use `urllib.request` only (no `httpx`, no `requests`)
- **Conventional commits**: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`
- **Formatting**: `ruff format src/ tests/` before committing
- **Linting**: `ruff check src/ tests/` must be clean
- **Types**: `mypy src/synology_dsm/ --ignore-missing-imports` must pass
- **Docstrings**: all public classes and methods — no exceptions
- **ensure() pattern**: all managers must implement idempotent `ensure(name, state="present"|"absent", dry_run=False)`
- **dry_run**: all destructive methods must support `dry_run=True` (no-op + describe what would happen)

## Adding a new module

1. Create `src/synology_dsm/{module}.py`
2. Add unit tests in `tests/unit/test_{module}.py`
3. Add integration tests in `tests/integration/test_live_nas.py` — use isolated test objects, clean up after
4. Export from `src/synology_dsm/__init__.py` if appropriate
5. Update `docs/feature-coverage.md` and `README.md`

## Session management

Always use `DSMClient` as a context manager — it handles login/logout and session cleanup:

```python
with DSMClient(host, port=5001, verify_ssl=False) as client:
    client.login(user, password)
    mgr = ShareManager(client)
    mgr.ensure("my-share", state="present")
# logout called automatically on __exit__
```

Never store session IDs in state — they are short-lived (30 min default on DSM 7.x).
