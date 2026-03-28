# DSM API Version Reference

Tested against: **DS1513+ running DSM 7.1.1-42962 Update 9**

All requests use `entry.cgi` endpoint. Login uses `entry.cgi` (not auth.cgi).

## Authentication

| API | Min | Max | Used | Notes |
|---|---|---|---|---|
| SYNO.API.Auth | 1 | 7 | **6** | Add `enable_syno_token=yes` to get real SynoToken |

Login params: `format=sid`, `enable_syno_token=yes`, `session=DSM`
Response includes `sid` + `synotoken` — both required for write ops.
Include `X-SYNO-TOKEN: <synotoken>` header on all write requests.

## User Management

| API | Used | Notes |
|---|---|---|
| SYNO.Core.User | v1 | list, create, set (update), delete |
| SYNO.Core.Group | v1 | list, create, set (update), delete, member_set |

**Delete format:** `name=["username"]` — JSON array string, not plain value.

## Share Management

| API | Used | Notes |
|---|---|---|
| SYNO.Core.Share | v1 | list, create (shareinfo JSON), set, delete |
| SYNO.Core.Share.Permission | v1 | set (via compound) — user_group_type: local_user or local_group |
| SYNO.Entry.Request | v1 | Compound/batch calls — required for permissions + NFS |
| SYNO.Core.FileServ.NFS.SharePrivilege | v1 | save (set NFS), load (get NFS) — param: share_name |

**Share create required format:**
```json
shareinfo={"name":"SHARENAME","vol_path":"/volume1","desc":"","name_org":""}
```
`name_org` field is required — omitting it causes 403.

**NFS param name:** `share_name` (not `sharename` — causes 2301 error).

## Compound Requests (SYNO.Entry.Request)

All write operations after create use compound batching:
1. Permission or NFS operation
2. Share.set with full shareinfo to finalize

```json
compound=[
  {"api":"SYNO.Core.Share.Permission","method":"set","version":1,...},
  {"api":"SYNO.Core.Share","method":"set","version":1,"shareinfo":{...}}
]
```

## System APIs (read-only, tested)

| API | Used | Notes |
|---|---|---|
| SYNO.Core.FileServ.NFS | v3 | get — global NFS service config |
| SYNO.FileStation.List | v1-v2 | list_share |
