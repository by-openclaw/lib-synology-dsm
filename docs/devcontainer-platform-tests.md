# Dev Container — Platform Test Status

Tracks validation of the dev container across all required platforms.

| Platform | Docker Desktop | Container build | Integration tests | Status |
|---|---|---|---|---|
| Windows 11 (Docker Desktop) | ✅ | ✅ | ✅ | **Validated 2026-03-30** |
| macOS | — | — | — | ⏳ Pending |
| Ubuntu Desktop | — | — | — | ⏳ Pending |

## Notes

- Windows 11: validated in session 2026-03-30 — container builds clean, `pytest tests/integration/ -v` passes against live NAS
- macOS + Ubuntu: to be verified with Docker Desktop installed
- LAN routing to NAS (10.6.224.0/20): on Windows routes via 192.168.65.1 by default — confirm same on macOS/Ubuntu

## How to test

1. Install Docker Desktop
2. Clone `lib-synology-dsm`
3. Copy `.devcontainer/.env.local.example` → `.devcontainer/.env.local`, fill credentials
4. Open in VS Code → `Dev Containers: Rebuild and Reopen in Container`
5. Open terminal inside container → `pytest tests/integration/ -v`
6. Update table above with result + date
