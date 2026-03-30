# Dev Container — LAN Access Setup

## How credentials work

Credentials are loaded from a **gitignored local file** — `.devcontainer/.env.local`.

- Never stored in Windows env vars
- Never committed to git
- Delete the file when done with integration testing on this machine

---

## Setup — one time per machine

### Step 1 — Enable WSL2 mirrored networking

Create or edit `%USERPROFILE%\.wslconfig` on the **Windows host**:

```ini
[wsl2]
networkingMode=mirrored
```

**Requirements:** Windows 11 22H2+ (build 22621+), WSL 2.0.0+

Check WSL version:
```powershell
wsl --version
```

If WSL is older:
```powershell
wsl --update
```

Restart WSL after editing `.wslconfig`:
```powershell
wsl --shutdown
```
Then reopen Docker Desktop — it restarts WSL2 automatically.

---

### Step 2 — Create the credentials file

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

---

### Step 3 — Build the container

In VS Code:
```
Ctrl+Shift+P → Dev Containers: Rebuild Container (Without Cache)
```

The `--env-file` in `runArgs` loads `.env.local` into the container automatically.
No Windows env vars needed. Nothing persists on the host after the container is stopped.

---

## Verify it works

From the container terminal:

```bash
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

## Windows 10 or older Windows 11 (no mirrored networking)

WSL2 mirrored networking requires Windows 11 22H2+. On older systems the container
cannot reach LAN directly — run integration tests from Git Bash on the host instead:

```bash
# Git Bash on Windows host — no container needed
cd lib-synology-dsm
pip install -e ".[dev]"
source .devcontainer/.env.local  # load credentials
pytest tests/integration/ -v
```

Or use **macvlan** (Docker network that bridges to your LAN adapter):

```powershell
# Run once in PowerShell as Administrator
docker network create `
  --driver macvlan `
  --subnet=10.6.224.0/20 `
  --gateway=10.6.224.1 `
  --opt parent=Ethernet `
  by-systems-lan
```

Then replace `"runArgs"` in `devcontainer.json`:
```jsonc
"runArgs": ["--network=by-systems-lan", "--env-file", "${localWorkspaceFolder}/.devcontainer/.env.local"]
```

---

## Approach comparison

| Approach | Win 11 22H2+ | Older Windows | Complexity | Credentials on host |
|---|---|---|---|---|
| WSL2 mirrored + `--network=host` + `.env.local` | ✅ | ❌ | Low | ❌ None |
| Run tests from host (Git Bash) | ✅ | ✅ | Zero | ❌ None |
| macvlan bridge | ✅ | ✅ | Medium | ❌ None |
| Windows User env vars | ✅ | ✅ | Low | ⚠️ Persistent — avoid |
