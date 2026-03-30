# Contributing to lib-synology-dsm

## Development setup

**Choose one path. Do not mix them.**

| Path | When to use |
|---|---|
| [A — Native Python + venv](#path-a--native-python--venv) | Any OS — Python installed locally, prefer terminal |
| [B — VS Code Dev Container](#path-b--vs-code-dev-container) | Any OS — Docker Desktop installed, prefer VS Code IDE |

Both paths use the **same `.env` file at the repo root** for credentials.

---

## Credentials — always first

Regardless of the path you choose, you need a `.env` file at the repo root.

```bash
cp .env.example .env
```

Open `.env` and fill in the two required values:

```ini
API_PASS=your-dsm-admin-password
TEST_USER_PASS=TmpPass123!        # password set on the temporary test user
```

The other fields (`NAS_HOST`, `NFS_CLIENT`, etc.) are pre-filled with BY-SYSTEMS defaults.
`.env` is gitignored — it will never be committed.

---

## Path A — Native Python + venv

No Docker required. Python 3.10+ must be installed.

### Windows (Git Bash)

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm

# Create and activate venv
python -m venv .venv
source .venv/Scripts/activate

# Install with dev extras
pip install -e ".[dev]"

# Copy and fill credentials
cp .env.example .env
# edit .env — fill in API_PASS and TEST_USER_PASS
```

### Linux / macOS

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm

# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install with dev extras
pip install -e ".[dev]"

# Copy and fill credentials
cp .env.example .env
# edit .env — fill in API_PASS and TEST_USER_PASS
```

### Run tests

```bash
# Unit tests (no NAS required)
pytest tests/unit/ -v

# Integration tests (live NAS required — .env must be filled)
pytest tests/integration/ -m integration -v
```

---

## Path B — VS Code Dev Container

Docker Desktop must be installed and running.
No local Python install required — everything runs inside the container.

### Prerequisites

| Tool | Download |
|---|---|
| Docker Desktop | <https://www.docker.com/products/docker-desktop> |
| VS Code | <https://code.visualstudio.com> |
| Dev Containers extension | VS Code → Extensions → `ms-vscode-remote.remote-containers` |

### Setup

**Step 1 — Clone the repo**

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
```

**Step 2 — Create `.env`**

```bash
cd lib-synology-dsm
cp .env.example .env
# edit .env — fill in API_PASS and TEST_USER_PASS
```

**Step 3 — Open in VS Code**

```
File → Open Folder → lib-synology-dsm
```

**Step 4 — Reopen in container**

VS Code will show a notification: _"Folder contains a Dev Container configuration"_ → click **Reopen in Container**.

Or: `Ctrl+Shift+P` → `Dev Containers: Rebuild and Reopen in Container`

The container will:
1. Pull `mcr.microsoft.com/devcontainers/python:3.13`
2. Create a venv at `/home/vscode/.venv`
3. Install the project with `pip install -e '.[container]'`
4. Strip Windows `\r` line endings from `.env` if present

**Step 5 — Run tests in the container terminal**

```bash
# Unit tests (no NAS required)
pytest tests/unit/ -v

# Integration tests (live NAS required — .env must be filled)
pytest tests/integration/ -m integration -v
```

### VS Code extensions (auto-installed)

The dev container installs these automatically:

| Extension | Purpose |
|---|---|
| Python | Language support, IntelliSense |
| Pylance | Type checking |
| Ruff | Linter + formatter (format on save) |
| Mypy | Static type checker |
| GitLens | Git annotations |
| Python Test Adapter | Test explorer sidebar |
| Code Spell Checker | Typo detection |

### Unit tests in VS Code test explorer

The test explorer sidebar runs **unit tests only** by default (no NAS needed).
Integration tests must be run manually from the container terminal.

---

## Pre-commit hooks

Pre-commit hooks run on the **host** (not inside the container) because `.git/hooks/` is owned by the host user.

Install once on the host:

```bash
# Native path — in your venv
pip install pre-commit
pre-commit install

# Dev container path — run this in Git Bash on the host (outside VS Code)
cd lib-synology-dsm
pip install pre-commit  # or use system Python
pre-commit install
```

Hooks configured: `detect-secrets` (credential scanner) + `ruff` (lint + format).

---

## LAN access from the container

| Platform | Status | Notes |
|---|---|---|
| Windows 11 + Docker Desktop | ✅ Validated | LAN routes via `192.168.65.1` by default — NAS reachable as-is |
| macOS + Docker Desktop | ⏳ Pending | Expected same behaviour |
| Ubuntu Desktop + Docker Desktop | ⏳ Pending | Expected same behaviour |

If the NAS is unreachable from inside the container: check Docker Desktop → Settings → Resources → Network — enable host networking or ensure the LAN route is present.

---

## Release process

Never edit version numbers manually. See [`docs/release-process.md`](docs/release-process.md).

```
push commits with conventional messages → release-please opens PR → merge it → done
```
