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
# List all available APIs and their version ranges (757 APIs on DS1513+ DSM 7.1.1)
curl -sk "https://NAS_IP:5001/webapi/query.cgi?api=SYNO.API.Info&method=query&version=1&query=all" | python3 -m json.tool

# Query specific API version range
curl -sk "https://NAS_IP:5001/webapi/query.cgi?api=SYNO.API.Info&method=query&version=1&query=SYNO.Core.User"
```

For the full list of implemented vs planned API coverage, see [feature-coverage.md](./feature-coverage.md).
