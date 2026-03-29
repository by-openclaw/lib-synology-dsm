# Contributing to lib-synology-dsm

## Development setup

### Linux / macOS

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install   # installs git hooks — blocks commits with secrets or lint errors
```

### Windows 11 (native, no WSL required)

> ⚠️ **Use PowerShell or Windows Terminal — not Git Bash.**
> Git Bash on Windows does not find the Python installed via `winget` or the Microsoft Store.
> All commands below must be run in **PowerShell** or **cmd.exe**.

```powershell
# 1. Install Python 3.13 (if not already installed)
#    Run in PowerShell — opens Microsoft Store if Python is missing
winget install Python.Python.3.13

# 2. Close and reopen PowerShell (so Python is on PATH), then verify:
python --version   # Expected: Python 3.13.x

# 3. Clone and set up
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install

# 4. Verify
pytest tests/unit/ -v
# Expected: 223 passed, 0 failed
```

> 💡 **Recommended alternative:** Use the VS Code Dev Container below — zero Python install required on your machine.

### VS Code Dev Container (recommended for consistency)

#### Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Install [VS Code](https://code.visualstudio.com/) + [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Docker Desktop install settings (Windows)

During Docker Desktop installation you will see a configuration screen.
Use these settings — anything else will cause issues:

| Option | Setting | Why |
|---|---|---|
| ✅ Use WSL 2 instead of Hyper-V | **Enable** | Required for Linux containers — better performance, less RAM overhead |
| ☐ Add shortcut to desktop | Optional | No impact |
| ☐ Allow Windows Containers | **Leave disabled** | We use Linux containers only (Python 3.13 image) — enabling this switches Docker to a different engine |

![Docker Desktop install settings](.devcontainer/assets/docker-desktop-install-settings.png)

After install, Docker Desktop will prompt for a logout/restart — do it before continuing.

#### Open in container

1. `File → Open Folder` → select the `lib-synology-dsm` folder
2. VS Code shows a popup: **"Reopen in Container"** → click it
   (or: `Ctrl+Shift+P` → `Dev Containers: Reopen in Container`)
3. First time: ~2 min to pull Python 3.13 image and install deps
4. Done — Python 3.13, ruff, mypy, pytest explorer all pre-configured

#### Verify it works

```bash
# Inside the container terminal:
pytest tests/unit/ -v
# Expected: 223 passed, 0 failed, 100% coverage
```

See [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) for full config.

---

## Pre-commit hooks (mandatory)

After cloning, run `pre-commit install` once. This installs git hooks that run automatically on every `git commit`:

| Hook | What it checks |
|---|---|
| `detect-secrets` | Blocks commits containing passwords, API tokens, private keys |
| `check-added-large-files` | Blocks files > 500KB |
| `end-of-file-fixer` | Ensures files end with newline |
| `ruff` | Python linting (auto-fix) |
| `ruff-format` | Python formatting |

**If detect-secrets flags a false positive** (e.g. a test placeholder like `"secret"`):
```bash
detect-secrets audit .secrets.baseline
# Follow prompts: press 'n' to mark as not a real secret
git add .secrets.baseline
git commit -m "chore: update secrets baseline"
```

**Never bypass the hooks** with `git commit --no-verify` unless you have an explicit reason and review it immediately.

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
