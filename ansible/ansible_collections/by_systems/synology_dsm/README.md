# by_systems.synology_dsm

Ansible modules for a Synology NAS (DSM 7), each a thin wrapper around a lib-synology-dsm v2
manager's `ensure()`: the module opens the session, calls `ensure()` (fetch, diff, no-op when
equal; check mode = the lib's dry run) and returns the result. No DSM API call lives here.

| Module | Wraps | Manages |
|---|---|---|
| `synology_dsm_share` | `CoreShareManager.ensure()` | a shared folder (create, description, delete) |
| `synology_dsm_nfs` | `CoreFileServNFSManager.ensure()` | one client's NFS rule on a shared folder; the other clients' rules are kept |

Requirements on the controller: `synology-dsm` (this repository's library) ≥ 0.11.0.

Install (private repository, pinned by commit):

```yaml
# requirements.yml
collections:
  - name: git+https://github.com/by-openclaw/lib-synology-dsm.git#/ansible/ansible_collections/by_systems/synology_dsm/
    type: git
    version: "<commit>"
```

The modules run on the controller (`delegate_to: localhost`); the DSM account and password come
from the caller (Vault), never from a file.
