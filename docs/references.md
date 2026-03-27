# API References & Resources

## Official Sources

| Resource | URL | Notes |
|---|---|---|
| Synology Developer Guide | https://global.download.synology.com/download/Document/Software/DeveloperGuide/ | PDF guides per package |
| On-NAS API Explorer | `http://{NAS_IP}:5000/webapi/entry.cgi?api=SYNO.API.Info&version=1&method=query&query=all` | Lists all APIs + supported versions |
| DSM FileStation API Guide | https://global.download.synology.com/download/Document/Software/DeveloperGuide/Package/FileStation/All/enu/Synology_File_Station_API_Guide.pdf | File operations |

## Community References

| Resource | URL | Notes |
|---|---|---|
| synology-dsm-api (pmilano1) | https://github.com/pmilano1/synology-dsm-api | Comprehensive API reference, quick-start guides, examples |
| Synology Community | https://community.synology.com/enu/forum | Official community forum |
| DSM Open API GitHub | https://github.com/synology-community/synology-api | Python community library (alternative reference) |

## How to discover API versions on your NAS

```bash
# List all available APIs and their version ranges
curl -sk "https://NAS_IP:5001/webapi/entry.cgi?api=SYNO.API.Info&version=1&method=query&query=all" | python3 -m json.tool

# Query specific API
curl -sk "https://NAS_IP:5001/webapi/entry.cgi?api=SYNO.API.Info&version=1&method=query&query=SYNO.Core.User"
```

## Useful API endpoints tested in this lib

| API | Endpoint | Version | Methods |
|---|---|---|---|
| SYNO.API.Auth | entry.cgi | 7 | login, logout |
| SYNO.Core.User | entry.cgi | 1 | list, create, set, delete |
| SYNO.Core.Group | entry.cgi | 1 | list, create, set, delete, get, member_set |
| SYNO.Core.Share | entry.cgi | 1 | list, create, set, delete |
| SYNO.Core.Share.NFS | entry.cgi | 1 | set, get |
| SYNO.FileStation.List | entry.cgi | 1-2 | list_share, list |
