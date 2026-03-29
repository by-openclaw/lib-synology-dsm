# lib-synology-dsm

Python library for [Synology DSM](https://www.synology.com/en-global/dsm) API automation — shares, users, groups, NFS, and FileStation operations.

[![CI](https://github.com/by-openclaw/lib-synology-dsm/actions/workflows/ci.yml/badge.svg)](https://github.com/by-openclaw/lib-synology-dsm/actions/workflows/ci.yml)
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
import os
from synology_dsm import DSMClient, ShareManager, UserManager, GroupManager

with DSMClient(os.environ["NAS_HOST"], port=5001, verify_ssl=False) as client:
    client.login(os.environ["DSM_USER"], os.environ["DSM_PASS"])

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
# 141 passing | 100% coverage | htmlcov/index.html generated

# Integration tests (live NAS)
NAS_HOST=your-nas-host API_USER=your-user API_PASS=your-pass \
AUDIT_USER=your-audit AUDIT_PASS=your-audit-pass \
NFS_CLIENT=your-nfs-subnet TEST_USER_PASS=TmpPass123! \
python3 tests/integration/test_live_nas.py --report /tmp/nas-report
# Writes: /tmp/nas-report.json + /tmp/nas-report.txt
```

---

## Dev container

Open in VS Code with the Dev Containers extension — Python 3.12, ruff, mypy, pytest explorer all pre-configured.

See [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json).

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
    with DSMClient(os.environ["NAS_HOST"], verify_ssl=False) as client:
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
