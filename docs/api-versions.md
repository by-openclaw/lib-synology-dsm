# DSM API Version Reference

Tested against: **DS1513+ running DSM 7.1.1-42962 Update 9**

All requests use `entry.cgi` endpoint. Login uses `auth.cgi` (SYNO.API.Auth v7).

## Authentication (DSMClient)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.API.Auth | v7 | login, logout | `enable_syno_token=yes` for SynoToken |

Login params: `format=sid`, `enable_syno_token=yes`, `session=DSM`
Response includes `sid` + `synotoken` — both required for write ops.
Include `X-SYNO-TOKEN: <synotoken>` header on all write requests.

## User Management (UserManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.User | v1 | list, create, set, delete | Delete: `name=["username"]` (JSON array string) |

## Group Management (GroupManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.Group | v1 | list, create, set, delete, get, member_list | member_list broken on DSM 7.1.x |
| SYNO.Core.Group.Member | v1 | list, add, remove | Primary membership API (matches DSM UI) |

**Member listing fallback chain:** Group.Member list → Group member_list → Group get.

## Share Management (ShareManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.Share | v1 | list, create, set, delete | create requires `shareinfo` JSON object |
| SYNO.Core.Share.Permission | v1 | set, list_by_group | user_group_type: local_user or local_group |
| SYNO.Entry.Request | v1 | request (compound) | Batch calls — required for permissions + NFS |
| SYNO.Core.FileServ.NFS.SharePrivilege | v1 | save, load | Per-share NFS rules — param: `share_name` |

**Share create required format:**
```json
shareinfo={"name":"SHARENAME","vol_path":"/volume1","desc":"","name_org":""}
```
`name_org` field is required — omitting it causes 403.

**NFS param name:** `share_name` (not `sharename` — causes 2301 error).

## Share Permissions (SharePermissionManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.Share.Permission | v1 | list_by_user, list_by_group, set | Standalone permission manager |

## NFS Management (NFSManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.FileServ.NFS.SharePrivilege | v1 | load, save | Per-share NFS client rules |

**Note:** SYNO.Core.Share.NFS does NOT exist on DSM 7.x — returns error 102.

## FileStation (FileStationManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.FileStation.List | v2 | list_share, list | Share/folder listing |
| SYNO.FileStation.CreateFolder | v2 | create | Folder creation |
| SYNO.FileStation.Upload | v2 | upload | SynoToken in URL query; session as cookie |
| SYNO.FileStation.Download | v2 | download | Binary response |
| SYNO.FileStation.Delete | v2 | delete | Path-based deletion |

**Upload quirks:** SynoToken in URL query string only; session as cookie `id=`; field `path` not `dest_folder_path`.

## Quota Management (QuotaManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.Quota | v1 | list, set | Per-user and per-group quota on volumes |

## Bandwidth Control (BandwidthManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.BandwidthControl | v2 | get, set | Per-user/group upload/download speed limits |

## Storage (StorageManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.Storage.Volume | v1 | list | Volume capacity, status, filesystem info |

## Traffic Control (TrafficControlManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.Core.Network.TrafficControl.Rules | v1 | load, save | Per-adapter network traffic rules |

## System Info (SystemManager)

| API | Version | Methods | Notes |
|---|---|---|---|
| SYNO.DSM.Info | v2 | getinfo | Primary — model, serial, DSM version |
| SYNO.Core.System | v1 | info | Fallback if DSM.Info unavailable |

## Compound Requests (SYNO.Entry.Request)

All write operations after share create use compound batching:
1. Permission or NFS operation
2. Share.set with full shareinfo to finalize

```json
compound=[
  {"api":"SYNO.Core.Share.Permission","method":"set","version":1,...},
  {"api":"SYNO.Core.Share","method":"set","version":1,"shareinfo":{...}}
]
```
