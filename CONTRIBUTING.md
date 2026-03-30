# Contributing to lib-synology-dsm

## Development setup

**Choose one path. Do not mix them.**

| Path | When to use |
|---|---|
| [A — Native (venv)](#path-a--native-venv) | Git Bash on Windows, or Linux/macOS terminal — Python installed locally |
| [B — VS Code Dev Container](#path-b--vs-code-dev-container) | No local Python install, or you want a pre-configured IDE — requires Docker Desktop |

---

## Path A — Native (venv)

No Docker required. Python runs directly on your machine.

### Linux / macOS

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
pytest tests/unit/ -v   # Expected: 223 passed, 0 failed
deactivate              # when done
```

### Windows 11 with Git Bash

#### Step 1 — Install Python 3.13

Run in Git Bash (or PowerShell):
```bash
winget install Python.Python.3.13
```

Restart Git Bash after install.

#### Step 2 — Disable App Execution Aliases

Windows intercepts `python` in Git Bash and redirects it to the Microsoft Store instead of the real binary.
**Disable the aliases before doing anything else:**

```
Start → Settings → Apps → Advanced app settings → App execution aliases
→ Turn OFF: python.exe
→ Turn OFF: python3.exe
```

#### Step 3 — Add Python to Git Bash PATH

The Python installer does **not** automatically add itself to Git Bash's PATH.
Add it manually — run this once in Git Bash (replace `YourUsername` with your Windows username):

```bash
echo 'export PATH="/c/Users/YourUsername/AppData/Local/Programs/Python/Python313:/c/Users/YourUsername/AppData/Local/Programs/Python/Python313/Scripts:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify:
```bash
python --version   # Expected: Python 3.13.x
pip --version      # Expected: pip 2x.x from .../Python313/...
```

#### Step 4 — Clone and set up

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm
python -m venv .venv
source .venv/Scripts/activate   # Git Bash on Windows: Scripts, not bin
pip install -e ".[dev]"
pre-commit install
```

> ⚠️ `bin/activate` is Linux/macOS. On Windows Git Bash it is always `Scripts/activate`.

#### Step 5 — Run unit tests

```bash
pytest tests/unit/ -v
# Expected: 223 passed, 3 warnings, 0 failed
# The 3 warnings are intentional — they test that deprecation/fallback warnings fire correctly
```

#### Step 6 — Run integration tests (live NAS)

```bash
cp .env.example .env
notepad .env   # fill in NAS_HOST, NAS_PORT, API_USER, API_PASS

# Load env vars into shell — no inline comments in .env or this will fail
export $(grep -v '^#' .env | grep -v '^$' | sed 's/[[:space:]]*#.*//' | xargs)

pytest tests/integration/ -v
# Expected: 51 passed, ~96s
```

#### Step 7 — Deactivate when done

```bash
deactivate
```

---

## Path B — VS Code Dev Container

Python runs inside a Docker container. Nothing to install locally except Docker and VS Code.

### Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Install [VS Code](https://code.visualstudio.com/) + [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Docker Desktop install settings (Windows)

During Docker Desktop installation you will see a configuration screen:

| Option | Setting | Why |
|---|---|---|
| ✅ Use WSL 2 instead of Hyper-V | **Enable** | Required for Linux containers |
| ☐ Allow Windows Containers | **Leave disabled** | We use Linux containers only |

After install, Docker Desktop will prompt for a logout/restart — do it before continuing.

### Step 1 — Clone the repo

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
```

### Step 2 — Open in VS Code

```
File → Open Folder → select lib-synology-dsm
```

VS Code will detect `.devcontainer/devcontainer.json` and show a popup:
**"Reopen in Container"** → click it.

Or: `Ctrl+Shift+P` → `Dev Containers: Reopen in Container`

First time: ~2 min to pull Python 3.13 image and install all deps automatically.

### Step 3 — Open a terminal inside the container

After the container starts, open a terminal:
- `Ctrl+\`` ` (backtick) — open a new terminal
- Or: **Terminal → New Terminal** from the menu bar

> ⚠️ VS Code may take a few seconds to become responsive after the build finishes.
> If the terminal panel does not appear immediately, wait for the status bar (bottom-left) to stop showing a spinner, then try again.
> If VS Code's built-in terminal is still not accessible, use **Terminal → New Terminal → bash** — this opens a raw bash session that always works.

### Step 4 — Run unit tests

In the container terminal:

```bash
pytest tests/unit/ -v
# Expected: 223 passed, 3 warnings, 0 failed
```

### Step 5 — Integration tests

> ⚠️ **Integration tests do NOT run inside the dev container.**
> Docker Desktop on Windows uses WSL2 NAT — the container has no route to your LAN (`10.6.224.x`).
> Run integration tests from a machine that is actually on the network: Rune VM, Git Bash on Windows, or any Linux host with LAN access.
> See [Path A](#path-a--native-venv) or the [Running integration tests](#running-integration-tests-live-nas-required) section below.

> The dev container is for **unit tests and development only.**

See [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) for full config.

### Troubleshooting — permission errors or stale build

If you see a `PermissionError` during container startup, or the `postCreateCommand` looks wrong
(e.g. still shows `pre-commit install` from an old cached build):

```bash
# Step 1 — pull latest devcontainer config
git reset --hard origin/main && git pull origin main

# Step 2 — full rebuild without cache
# Ctrl+Shift+P → Dev Containers: Rebuild Container Without Cache
```

The **"Without Cache"** option is critical — a normal rebuild reuses the old config.

> **Note on pre-commit in the container:**
> `pre-commit` is intentionally not installed inside the container. `.git/hooks/` is owned by the
> Windows host user and is not writable from inside the Linux container. Git hooks (pre-commit,
> detect-secrets, ruff, etc.) run on the **host** only — via Path A or Git Bash.
> To install hooks on the host: `pip install -e ".[dev]" && pre-commit install` (run once in Git Bash).

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

> **No `.env` needed. No NAS needed. No network needed.** All HTTP calls are mocked.
> Unit tests are completely self-contained — just `pytest tests/unit/ -v` on either Path A or B.

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

> **This is where `.env` is needed.** Integration tests connect to a real NAS.
> Skip this entirely if you're just developing and running unit tests.

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

### Setup

```bash
cp .env.example .env
notepad .env   # or your editor — fill in NAS_HOST, NAS_PORT, API_USER, API_PASS
```

> ⚠️ **Do not add inline comments** (`# ...`) after values in `.env`. The `xargs` loader will fail.

### Run

```bash
# Export env vars from file, then run
export $(grep -v '^#' .env | grep -v '^$' | sed 's/[[:space:]]*#.*//' | xargs)
pytest tests/integration/ -v
# Expected: 51 passed, ~96s
```

### What it does

Each test creates a uniquely named object (e.g. `rune-u-b4c9d1cc`), runs assertions, then deletes it.
Your NAS audit log will show create/delete pairs for each test — this is expected and correct.
**Nothing persists on the NAS after the run.**

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
