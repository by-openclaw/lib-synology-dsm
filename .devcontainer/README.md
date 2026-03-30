# Dev Container — LAN Access Setup

## How credentials work

Credentials are loaded from a **gitignored local file** — `.devcontainer/.env.local`.

- Never stored in Windows env vars
- Never committed to git
- Delete the file when done with integration testing on this machine

---

## Setup — one time per machine

### Step 1 — Create the credentials file

In Git Bash, from the repo root:

```bash
cp .devcontainer/.env.local.example .devcontainer/.env.local
```

Edit `.devcontainer/.env.local` and fill in the credentials:

```ini
NAS_HOST=10.6.224.6
NAS_PORT=5001
API_USER=rune-api
API_PASS=<password>
NFS_CLIENT=10.6.224.0/20
FS_BASE_SHARE=by-terraform-state
TEST_USER_PASS=<test-user-password>
```

This file is gitignored — it will never be committed.

> **Windows line endings** — if you edit `.env.local` with Notepad or VS Code on Windows,
> it may save `\r\n` line endings. The `postCreateCommand` runs `sed -i 's/\r//'` automatically
> on every container build — you don't need to do anything.

---

### Step 2 — Build the container

In VS Code:
```
Ctrl+Shift+P → Dev Containers: Rebuild Container (Without Cache)
```

The `--env-file` in `runArgs` loads `.env.local` into the container at build time.
No Windows env vars needed. Nothing persists on the host after the container is stopped.

> **Note:** `--network=host` is silently ignored by Docker Desktop on Windows.
> Docker Desktop routes LAN traffic (10.x.x.x) via `192.168.65.1` by default —
> no extra network config needed. WSL2 mirrored networking is **not required**.

---

## Verify it works

From the container terminal:

```bash
# Check credentials loaded correctly
echo "NAS_HOST=$NAS_HOST API_USER=$API_USER"

# Check LAN connectivity — should return {"success": true}
curl -sk https://$NAS_HOST:$NAS_PORT/webapi/entry.cgi \
  -d "api=SYNO.API.Auth&version=7&method=login&account=$API_USER&passwd=$API_PASS&session=DSM&format=cookie" \
  | python3 -m json.tool

# Full integration test suite
pytest tests/integration/ -v
```

---

## When done with integration testing

Delete the credentials file:
```bash
rm .devcontainer/.env.local
```

Nothing remains on the Windows host.

---

## Pre-commit hooks

Pre-commit hooks **cannot be installed inside the container** — `.git/hooks` is owned
by the Windows host and is not writable from inside the container.

**Always commit from Git Bash on the Windows host**, not from the container terminal.

One-time setup on the host:
```bash
# Git Bash on Windows host
cd lib-synology-dsm
pip install pre-commit
pre-commit install
```

---

## Running on Linux or macOS

No special setup needed — `.env.local` loads normally, LAN is reachable directly.

```bash
cp .devcontainer/.env.local.example .devcontainer/.env.local
# fill in credentials
# Ctrl+Shift+P → Dev Containers: Rebuild Container
```
