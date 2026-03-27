# DSM API Version Reference

Synology DSM APIs support multiple versions. This library uses the following versions,
validated against DS1513+ running DSM 7.1.1:

| API | Min | Max | Used | Notes |
|---|---|---|---|---|
| SYNO.API.Auth | 1 | 7 | **7** | v7 returns synotoken + device_id + account |
| SYNO.Core.User | 1 | 1 | **1** | Only v1 available on DS1513+ DSM 7.1.1 |
| SYNO.Core.Group | 1 | 1 | **1** | Only v1 available |
| SYNO.Core.Share | 1 | 1 | **1** | Admin required for create/delete |
| SYNO.Core.Share.NFS | 1 | 1 | **1** | Admin required |
| SYNO.FileStation.List | 1 | 2 | **1** | v2 adds additional fields |

## Delete operations

DSM requires JSON array format for delete: `name=["value"]` not `name=value`.
This applies to: `SYNO.Core.User.delete`, `SYNO.Core.Group.delete`.

## Admin requirement

The following operations require the calling user to be in the `administrators` group:

- `SYNO.Core.Share` create/delete/modify
- `SYNO.Core.Share.NFS` set
- `SYNO.Core.User` create/delete (non-self)
- `SYNO.Core.Group` create/delete
