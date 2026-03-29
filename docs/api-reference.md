# API Reference

Tested against: **DS1513+ running DSM 7.1.1-42962 Update 9**

All API calls use `entry.cgi`. Auth v6 with `enable_syno_token=yes` is required for write operations.

---

## DSMClient

Session manager for Synology DSM API.

```python
from synology_dsm import DSMClient

with DSMClient("your-nas-host", port=5001) as client:
    client.login(os.environ["DSM_USER"], os.environ["DSM_PASS"])
    # ... use managers
# session automatically closed on exit
```

### Auth details
- API: `SYNO.API.Auth` v6
- Params: `format=sid`, `enable_syno_token=yes`, `session=DSM`
- Response: `sid` + `synotoken` — both required
- All write requests: include `X-SYNO-TOKEN: <synotoken>` header

### Methods
- `login(account, password, session="DSM")` → str (session ID)
- `logout()` → None
- `request(api, method, version, **params)` → dict

---

## UserManager

```python
from synology_dsm.users import UserManager
mgr = UserManager(client)
```

### Methods

| Method | DSM API | Notes |
|---|---|---|
| `list()` | `SYNO.Core.User` method=list v1 | Returns list of user dicts |
| `create(name, password, description)` | `SYNO.Core.User` method=create v1 | Returns `{"success": true}` |
| `update(name, **fields)` | `SYNO.Core.User` method=set v1 | Update description, email, etc. |
| `delete(name)` | `SYNO.Core.User` method=delete v1 | `name` sent as JSON array: `["username"]` |
| `get(name)` | `SYNO.Core.User` method=get v1 | Returns single user dict |
| `ensure(name, state, **kwargs)` | — | Idempotent: state=present/absent |

**Delete format (critical):** `name=["username"]` — JSON array string. Plain string returns error 101.

---

## GroupManager

```python
from synology_dsm.groups import GroupManager
mgr = GroupManager(client)
```

### Methods

| Method | DSM API | Notes |
|---|---|---|
| `list()` | `SYNO.Core.Group` method=list v1 | Returns list of group dicts |
| `create(name, description)` | `SYNO.Core.Group` method=create v1 | Returns `{"success": true}` |
| `update(name, **fields)` | `SYNO.Core.Group` method=set v1 | Update description, etc. |
| `delete(name)` | `SYNO.Core.Group` method=delete v1 | `name` sent as JSON array: `["groupname"]` |
| `get(name)` | `SYNO.Core.Group` method=get v1 | Returns single group dict |
| `ensure(name, state, **kwargs)` | — | Idempotent: state=present/absent |

**Known DSM 7.1.1 limitation:** `member_set` method returns error 103 (method not implemented).
Group membership management via `SYNO.Core.Group` is not available on this DSM version.

---

## ShareManager

```python
from synology_dsm.shares import ShareManager
mgr = ShareManager(client)
```

### Methods

| Method | DSM API | Notes |
|---|---|---|
| `list()` | `SYNO.Core.Share` method=list v1 | Returns list of share dicts |
| `create(name, vol_path, description)` | `SYNO.Core.Share` method=create v1 | Requires `shareinfo` JSON with `name_org` field |
| `update(name, **fields)` | `SYNO.Core.Share` method=set v1 | Uses compound call |
| `delete(name)` | `SYNO.Core.Share` method=delete v1 | Returns `{"success": true}` |
| `set_permission(name, account, type)` | `SYNO.Core.Share.Permission` method=set v1 | Via `SYNO.Entry.Request` compound |
| `set_nfs_permission(name, client_ip, **opts)` | `SYNO.Core.FileServ.NFS.SharePrivilege` method=save v1 | Via `SYNO.Entry.Request` compound |
| `get_nfs_rules(name)` | `SYNO.Core.FileServ.NFS.SharePrivilege` method=load v1 | `share_name` param (not `sharename`) |
| `create_with_permissions(name, vol_path, user_perms, group_perms, nfs_rules)` | — | Full share lifecycle in one call |
| `ensure(name, state, **kwargs)` | — | Idempotent: state=present/absent |

### Share create — required shareinfo format

```json
{
  "name": "SHARENAME",
  "vol_path": "/volume1",
  "desc": "optional description",
  "name_org": ""
}
```

`name_org` is required. Omitting it returns HTTP 403.

### NFS permission — compound request example

```python
compound = [
    {
        "api": "SYNO.Core.FileServ.NFS.SharePrivilege",
        "method": "save",
        "version": 1,
        "share_name": "myshare",
        "rule": [{
            "client": "10.0.0.100",
            "privilege": "rw",
            "root_squash": "root",
            "async": True,
            "insecure": False,
            "crossmnt": False,
            "security_flavor": {
                "kerberos": False,
                "kerberos_integrity": False,
                "kerberos_privacy": False,
                "sys": True
            }
        }]
    },
    {
        "api": "SYNO.Core.Share",
        "method": "set",
        "version": 1,
        "name": "myshare",
        "shareinfo": {"name": "myshare", "vol_path": "/volume1", "desc": "", "encryption": False, "enc_passwd": ""}
    }
]
```

**NFS param name:** `share_name` (not `sharename` — causes error 2301).

### Permission set — user_group_type values

| Value | Description |
|---|---|
| `local_user` | DSM local user account |
| `local_group` | DSM local group |

### Permission object shape

```json
{
  "name": "username_or_group",
  "is_readonly": false,
  "is_writable": true,
  "is_deny": false,
  "is_custom": false
}
```

---

## Compound Requests (SYNO.Entry.Request)

All permission and NFS write operations use batched compound calls via `SYNO.Entry.Request`.

```http
POST /webapi/entry.cgi
X-SYNO-TOKEN: <token>

api=SYNO.Entry.Request&method=request&version=1
&stop_when_error=true&mode=sequential
&compound=[...]&_sid=<sid>
```

Response shape:
```json
{
  "success": true,
  "data": {
    "has_fail": false,
    "result": [...]
  }
}
```

Check `data.has_fail == false` for success (not top-level `success`).
