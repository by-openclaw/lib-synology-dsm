# API Reference

## DSMClient

Session manager for Synology DSM API.

```python
from synology_dsm import DSMClient

with DSMClient("10.6.224.6", port=5001) as client:
    client.login("rune-api", "password")
    # ... use managers
# session automatically closed on exit
```

### Methods
- `login(account, password, session)` → str (session ID)
- `logout()` → None
- `request(api, method, version, **params)` → dict

## ShareManager

```python
from synology_dsm.shares import ShareManager
mgr = ShareManager(client)
```

### Methods
- `list()` → list[dict]
- `create(name, volume_path, description)` → dict
- `delete(name)` → None
- `set_nfs_permission(share, hostname, rw)` → dict

## NFSManager

```python
from synology_dsm.nfs import NFSManager
mgr = NFSManager(client)
```

### Methods
- `get_rules(share)` → list[dict]

## UserManager

```python
from synology_dsm.users import UserManager
mgr = UserManager(client)
```

### Methods
- `list()` → list[dict]
- `create(name, password, email, description)` → dict
- `disable(name)` → None (audit trail preserved — never delete)
- `list_groups()` → list[dict]
