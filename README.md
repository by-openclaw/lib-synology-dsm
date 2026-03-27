# lib-synology-dsm

Python library for Synology DSM API — idempotent operations for shared folders, NFS permissions, users, and groups.

## Usage

```python
from synology_dsm import DSMClient
from synology_dsm.shares import ShareManager

with DSMClient("10.6.224.6") as client:
    client.login("rune-api", "password")
    shares = ShareManager(client)
    
    # Create NFS share
    shares.create("srv-proxmox-poc-01-iso", description="PoC ISO storage")
    shares.set_nfs_permission("srv-proxmox-poc-01-iso", "10.6.224.105", rw=True)
    
    # List shares
    for s in shares.list():
        print(s["name"])
```

## Install

```bash
pip install synology-dsm  # from GitLab Package Registry (when published)
# or
pip install git+https://github.com/by-openclaw/lib-synology-dsm.git
```

## Credentials

Never hardcode credentials. Three patterns supported:

### .env file (development)

```bash
cp .env.example .env
# edit .env with your values
```

```python
from synology_dsm.credentials import EnvCredentialProvider
creds = EnvCredentialProvider().get()
```

### HashiCorp Vault (production)

```bash
pip install 'lib-synology-dsm[vault]'
export VAULT_ADDR=https://vault.by-systems.arpa
export VAULT_TOKEN=...
```

```python
from synology_dsm.credentials import get_credentials
creds = get_credentials()  # auto-detects Vault
```

### Explicit (testing only)

```python
with DSMClient("10.6.x.x") as client:
    client.login("svc-rune-dsm", "password")
```

See [docs/credentials.md](docs/credentials.md) for full details.

## Design

- Session lifecycle managed by `DSMClient` context manager (auto-logout)
- All operations idempotent
- Future: NetBox webhook integration for automated provisioning
- Future: Authentik group sync for NFS user permissions

## Modules

| Module | Purpose |
|---|---|
| `client.py` | Session management, auth, base request |
| `shares.py` | Shared folder CRUD |
| `nfs.py` | NFS export rules |
| `users.py` | User/group management |

## References

### Synology DSM API Documentation
- **Official Synology API Guide**: Available on your NAS at `http://NAS_IP:5000/webapi/entry.cgi?api=SYNO.API.Info&version=1&method=query&query=all`
- **Official DSM Docs Portal**: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf
- **Community API Reference (pmilano1)**: https://github.com/pmilano1/synology-dsm-api — comprehensive unofficial reference with examples for all major DSM APIs
- **DSM 7.x API Explorer** (on-NAS): `https://NAS_IP:5001/webapi/entry.cgi?api=SYNO.API.Info&version=1&method=query&query=SYNO.Core.User`

### Tested Against
- Hardware: Synology DS1513+
- DSM: 7.1.1-42962 Update 9
- API auth: SYNO.API.Auth v7 (entry.cgi)
