# Dev Container — LAN Access Setup

## The problem

Docker Desktop on Windows uses WSL2 as its backend. By default WSL2 uses
a **NAT network** — containers reach the internet but not your local network
(your Synology NAS at `10.6.x.x` is unreachable).

## The fix — two steps, done once per machine

### Step 1 — Enable WSL2 mirrored networking

Create or edit `%USERPROFILE%\.wslconfig` on the **Windows host**:

```ini
# %USERPROFILE%\.wslconfig
# Full path example: C:\Users\YourName\.wslconfig

[wsl2]
networkingMode=mirrored
```

**Requirements:**
- Windows 11 22H2 or later (build 22621+)
- WSL version 2.0.0 or later

Check your WSL version:
```powershell
wsl --version
```

If WSL is older:
```powershell
wsl --update
```

After editing `.wslconfig`, **restart WSL**:
```powershell
wsl --shutdown
# Then reopen Docker Desktop — it restarts WSL2 automatically
```

Mirrored mode copies all Windows network interfaces into WSL2 — including
your LAN adapter, its routes, and DNS. The container now sees your entire
local network exactly as Windows does.

### Step 2 — Rebuild the dev container

In VS Code: `Ctrl+Shift+P` → `Dev Containers: Rebuild Container`

The `devcontainer.json` already has `--network=host` which tells Docker
to share the WSL2 network stack. With mirrored networking active, this
gives the container full LAN access.

---

## Verify it works

From inside the container terminal:

```bash
# Ping the NAS
ping -c 2 $NAS_HOST

# Auth check
bash tests/integration/curl/00-auth.sh

# Full integration test suite
pytest tests/integration/ -m integration -v
```

---

## Why this approach

| Approach | Windows support | Complexity | LAN access |
|---|---|---|---|
| `--network=host` alone | ❌ silently ignored on Windows | Low | ❌ |
| WSL2 mirrored + `--network=host` | ✅ Windows 11 22H2+ | Low | ✅ |
| macvlan bridge network | ✅ all Windows | High — per-machine setup | ✅ |
| Run integration tests from host | ✅ all Windows | Zero | ✅ |

WSL2 mirrored networking is the **official Microsoft solution** for this exact
problem. It requires no per-project Docker network config and works for every
container automatically.

---

## Windows 10 or older Windows 11

Mirrored networking requires Windows 11 22H2+. On older systems use
**macvlan** (more complex) or run integration tests from Git Bash on the host.

macvlan setup:
```powershell
# Run once in PowerShell as Administrator
# Replace subnet, gateway, and adapter name with your network values
docker network create `
  --driver macvlan `
  --subnet=10.6.0.0/20 `
  --gateway=10.6.0.1 `
  --opt parent=Ethernet `
  by-systems-lan
```

Then in `devcontainer.json`, replace:
```jsonc
"runArgs": ["--network=host"]
```
with:
```jsonc
"runArgs": ["--network=by-systems-lan"]
```

---

## Environment variables

NAS credentials are forwarded from host environment variables into the
container via `remoteEnv` in `devcontainer.json`. Set them once on Windows:

**Option A — System environment variables (permanent, all shells)**

```
Windows → Settings → System → About → Advanced system settings
→ Environment Variables → User variables → New
```

Add each variable: `NAS_HOST`, `NAS_PORT`, `API_USER`, `API_PASS`,
`NFS_CLIENT`, `FS_BASE_SHARE`, `TEST_USER_PASS`

**Option B — Git Bash profile (Git Bash only)**

Add to `~/.bash_profile` (create if missing):

```bash
export NAS_HOST=10.6.224.6
export NAS_PORT=5001
export API_USER=rune-api
export API_PASS=your-password
export NFS_CLIENT=10.6.0.0/20
export FS_BASE_SHARE=by-terraform-state
export TEST_USER_PASS=TmpPass123!
```

Restart Git Bash, then reopen VS Code from Git Bash:
```bash
code /path/to/lib-synology-dsm
```

VS Code inherits the environment and forwards the variables into the container.

---

## Pre-commit hooks

Pre-commit hooks **cannot be installed inside the container** — `.git/hooks`
is owned by the Windows host and is not writable from the container.

**Always commit from Git Bash on the Windows host**, not from the container terminal.

One-time setup on the host:
```bash
# Git Bash on Windows host
cd lib-synology-dsm
pip install pre-commit
pre-commit install
```

Hooks then run automatically on every `git commit` from Git Bash.
