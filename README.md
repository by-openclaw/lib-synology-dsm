# lib-synology-dsm

Python library for [Synology DSM](https://www.synology.com/en-global/dsm) API automation — shares, users, groups, NFS, and FileStation operations.

[![CI](https://github.com/by-openclaw/lib-synology-dsm/actions/workflows/ci.yml/badge.svg)](https://github.com/by-openclaw/lib-synology-dsm/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/by-openclaw/lib-synology-dsm/branch/main/graph/badge.svg)](https://codecov.io/gh/by-openclaw/lib-synology-dsm)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://github.com/by-openclaw/lib-synology-dsm/actions/workflows/ci.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Dev Container](https://img.shields.io/badge/dev%20container-ready-blue?logo=docker)](https://containers.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Internal use — BY-SYSTEMS DevOps platform.**
> See [LICENSE](LICENSE) for terms and disclaimer of liability.

---

## Documentation

| Document | Purpose |
|---|---|
| [docs/api-reference.md](docs/api-reference.md) | Full API reference — all managers, methods, parameters |
| [docs/credentials.md](docs/credentials.md) | Credential providers — env vars, `.env`, HashiCorp Vault |
| [docs/feature-coverage.md](docs/feature-coverage.md) | DSM API coverage matrix |
| [docs/hardening.md](docs/hardening.md) | DSM account hardening — IP restrictions, app permissions |
| [docs/licenses.md](docs/licenses.md) | Dependency license table |
| [docs/ansible-roadmap.md](docs/ansible-roadmap.md) | Planned Ansible collection |
| [docs/adr/README.md](docs/adr/README.md) | Architecture Decision Records |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, unit tests, integration tests |

---

## Quick start

```bash
pip install git+https://github.com/by-openclaw/lib-synology-dsm.git
```

```python
from synology_dsm import DSMClient, ShareManager, UserManager, GroupManager, get_credentials

creds = get_credentials()  # reads from .env file or Vault automatically
with DSMClient(creds.host, port=creds.port, verify_ssl=False) as client:
    client.login(creds.user, creds.password)

    # Idempotent share creation
    shares = ShareManager(client)
    result = shares.ensure("by-data", state="present", description="Data share")
    print(result)  # {"changed": True, "action": "created"}

    # Idempotent user creation
    users = UserManager(client)
    result = users.ensure("alice", state="present", password="secret", email="a@b.com")
    print(result)  # {"changed": False, "action": "noop"}  — if already exists with same values
```

See [docs/api-reference.md](docs/api-reference.md) for full usage examples.

---

## DSM account requirements

### Admin account (`API_USER`)
- DSM group: `administrators`
- Applications: **DSM = Allow**, **File Station = Allow**

### Audit account (`AUDIT_USER`, optional — for read-only integration tests)
- DSM group: `users` (no admin)
- Applications: **DSM = Allow**, **File Station = Allow**

See [docs/hardening.md](docs/hardening.md) for IP restriction and log center setup.

---

## Testing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full instructions.

```bash
# Unit tests (offline, no NAS)
pytest tests/unit/ -v
# 170 passing | 100% coverage | htmlcov/index.html generated

# Integration tests (live NAS)
NAS_HOST=your-nas-host API_USER=your-user API_PASS=your-pass \
AUDIT_USER=your-audit AUDIT_PASS=your-audit-pass \
NFS_CLIENT=your-nfs-subnet TEST_USER_PASS=TmpPass123! \
python3 tests/integration/test_live_nas.py --report /tmp/nas-report
# Writes: /tmp/nas-report.json + /tmp/nas-report.txt
```

---

## Dev container (recommended — works on Windows, macOS, Linux)

The dev container gives every developer an identical, pre-configured environment.
No Python install on your machine. No WSL. No "works on my machine."

### What you need (one-time install)

| # | Tool | Download | How to install |
|---|---|---|---|
| 1 | **Docker Desktop** | https://www.docker.com/products/docker-desktop/ | Download installer → run → reboot if prompted. Free for personal/small team. On Windows: uses a background VM (WSL2 kernel) — you never open or manage it. |
| 2 | **VS Code** | https://code.visualstudio.com/ | Download installer → run. Free. |
| 3 | **Dev Containers extension** | https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers | In VS Code: press `Ctrl+Shift+X` (Extensions panel) → search **"Dev Containers"** → click **Install**. Publisher must be **Microsoft**. Or click the marketplace link → "Install". |

### How to open the project

1. Clone the repo:
   ```bash
   git clone https://github.com/by-openclaw/lib-synology-dsm.git
   ```
2. Open the folder in VS Code: `File → Open Folder` → select `lib-synology-dsm`
3. VS Code shows a popup: **"Reopen in Container"** — click it
   - If you miss it: press `Ctrl+Shift+P` → type `Dev Containers: Reopen in Container`
4. Wait ~2 minutes for the first build (downloads Python 3.12 image, installs all deps)
5. You now have a terminal inside the container with everything ready:
   - Python 3.12, pip, venv
   - ruff, mypy, pytest, pytest-cov
   - pre-commit hooks already installed (automatic — no manual step)

### Run unit tests inside the container

```bash
pytest tests/unit/ -v
# Expected: 170 passed, 0 failed, 100% coverage
```

### Run integration tests (requires NAS reachable on your network)

```bash
# Set your NAS credentials in .env (copy from .env.example)
cp .env.example .env
# Edit .env with your values, then:
source .env
python tests/integration/test_live_nas.py --report /tmp/nas-report
# Output: /tmp/nas-report.json + /tmp/nas-report.txt
```

---

## Pre-commit hooks

Pre-commit hooks run **automatically on every `git commit`** — no manual step needed.

Inside the dev container they are installed automatically when the container starts
(`postCreateCommand` in `.devcontainer/devcontainer.json`).

If working **outside the container** (native Python setup), install once:
```bash
pip install -e ".[dev]"
pre-commit install   # one-time — hooks run automatically on every commit from now on
```

### What the hooks check

| Hook | What it does | Blocks commit? |
|---|---|---|
| `detect-secrets` | Scans **text files** for passwords, API tokens, private keys | ✅ Yes — skips binary files and Git LFS pointer files automatically |
| `check-added-large-files` | Blocks files whose **committed size** exceeds 500 KB | ✅ Yes — see LFS note below |
| `end-of-file-fixer` | Ensures text files end with a newline | ✅ Yes (auto-fixes) — skips binary files |
| `trailing-whitespace` | Removes trailing spaces from text files | ✅ Yes (auto-fixes) — skips binary files |
| `check-yaml` / `check-toml` / `check-json` | Syntax validation for config files | ✅ Yes |
| `ruff` | Python linting (auto-fixes what it can) | ✅ Yes — Python files only |
| `ruff-format` | Python formatting | ✅ Yes (auto-formats) — Python files only |

#### Git LFS and large files

This repo uses **Git LFS** for binary files: `.pdf`, `.png`, `.svg`, `.drawio`, `.mp4`, `.zip`
(configured in `.gitattributes`).

When you commit a file tracked by LFS, Git does **not** store the binary in the repo.
Instead it commits a small **pointer file** (~134 bytes) like this:

```
version https://git-lfs.github.com/spec/v1
oid sha256:4d7a8f...
size 5242880
```

**What the hooks see:**

| Scenario | What gets committed | `check-added-large-files` | `detect-secrets` | `ruff` |
|---|---|---|---|---|
| `assets/diagram.png` (10 MB, LFS tracked) | 134-byte LFS pointer | ✅ Passes (134 B < 500 KB) | ✅ Passes (not text content) | ✅ Passes (not Python) |
| `docs/report.pdf` (50 MB, LFS tracked) | 134-byte LFS pointer | ✅ Passes | ✅ Passes | ✅ Passes |
| `big-file.bin` (2 MB, **not** LFS tracked) | Full 2 MB binary | ❌ **Blocked** (2 MB > 500 KB) | ✅ Passes (binary) | ✅ Passes (not Python) |
| `secret.py` with `password = "abc123"` | Text file | ✅ Passes | ❌ **Blocked** | ✅ Passes (or fix linting) |

**Rule:** Binary files must be tracked by LFS — otherwise `check-added-large-files` blocks the commit.
To add a new file type to LFS:
```bash
git lfs track "*.ext"     # adds to .gitattributes
git add .gitattributes
git add your-file.ext
git commit -m "chore: add *.ext to LFS tracking"
```

### If detect-secrets blocks your commit (false positive)

**What is a false positive?**
detect-secrets blocked your commit because a line *looks* like a secret but isn't — for example
a test placeholder (`"secret"`, `"YOUR_PASSWORD"`), a Vault path, or a high-entropy string in a comment.

**Step 1 — Run the interactive audit tool**

```bash
detect-secrets audit .secrets.baseline
```

This opens an interactive session in your terminal. For each flagged item it shows:

```
Secret:      1 of 3
Filename:    tests/unit/test_credentials.py
Secret Type: Secret Keyword
----------
20:    assert creds.password == "secret"
----------
Is this a valid secret? [y/n/s/q]:
```

- Press **`n`** — not a real secret (false positive) → moves to next
- Press **`y`** — it IS a real secret → **stop, remove it from your code first**
- Press **`s`** — skip for now (stays unresolved)
- Press **`q`** — quit

Work through all findings pressing `n` for each false positive.

**Step 2 — Commit the updated baseline**

```bash
git add .secrets.baseline
git commit -m "chore: update secrets baseline — mark false positives"
git push
```

Your original commit will now go through on your next `git commit`.

**Does this affect CI?**
No. CI does not run detect-secrets. CI only runs `ruff`, `mypy`, and `pytest`.
The baseline commit is a normal commit — CI runs green as long as tests pass.

**Does this trigger a version bump?**
No. A `chore:` commit type is ignored by release-please.
It does not create a new version tag or release. It may appear in the CHANGELOG but will not
change `v0.8.0` → `v0.8.1` or anything else. Completely safe.

---

## Modules

| Module | Class | Description |
|---|---|---|
| `synology_dsm.client` | `DSMClient` | Session management, auth, raw API calls |
| `synology_dsm.shares` | `ShareManager` | Shared folder CRUD, NFS rules, permissions |
| `synology_dsm.users` | `UserManager` | User CRUD, group membership |
| `synology_dsm.groups` | `GroupManager` | Group CRUD, member management |
| `synology_dsm.filestation` | `FileStationManager` | Upload, download, list, mkdir, delete |
| `synology_dsm.nfs` | `NFSManager` | NFS rule management (per share) |
| `synology_dsm.credentials` | `EnvCredentialProvider`, `VaultCredentialProvider`, `get_credentials` | Credential resolution |
| `synology_dsm.exceptions` | `DSMError` hierarchy | Typed exceptions — auth, permission, connection, API |

---

## Error handling

All errors raise typed exceptions that inherit from `DSMError`. Catch what you need:

```python
from synology_dsm import (
    DSMClient,
    ShareManager,
    DSMAuthError,
    DSMConnectionError,
    DSMPermissionError,
    DSMNotFoundError,
    DSMAPIError,
    DSMError,
)
import os

try:
    with DSMClient(creds.host, port=creds.port, verify_ssl=False) as client:
        client.login(os.environ["DSM_USER"], os.environ["DSM_PASS"])
        shares = ShareManager(client)
        result = shares.ensure("my-share", state="present")

except DSMConnectionError as e:
    # NAS unreachable: connection refused, timeout, DNS failure
    print(f"Cannot reach NAS: {e}")

except DSMAuthError as e:
    # Wrong credentials (400) or account disabled (402)
    print(f"Auth failed (code {e.code}): {e}")

except DSMPermissionError as e:
    # Account lacks permission for this operation (403)
    print(f"Permission denied (code {e.code}): {e}")

except DSMNotFoundError as e:
    # Resource does not exist (408)
    print(f"Not found (code {e.code}): {e}")

except DSMAPIError as e:
    # Any other DSM error code
    print(f"DSM API error (code {e.code}): {e}")

except DSMError as e:
    # Catch-all for any library error
    print(f"DSM error: {e}")
```

All exceptions expose `.code: int | None` (the raw DSM error code, or `None` for network errors).

### Exception hierarchy

```
DSMError
├── DSMAuthError          — codes 400, 402 (bad credentials, account disabled)
├── DSMPermissionError    — code 403 (insufficient privileges)
├── DSMSessionError       — code 119 (session expired)
├── DSMNotFoundError      — code 408 (resource not found)
├── DSMConnectionError    — network failure (connection refused, timeout, DNS)
└── DSMAPIError           — any other DSM error code
```

---

## Install from source

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```
