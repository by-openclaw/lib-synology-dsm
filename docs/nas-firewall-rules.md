# NAS Firewall Port Inventory — DS1513+ (DSM 7.1.1)

> **Purpose:** Reference for @yboujraf to configure DSM firewall rules (Security > Firewall).
> **Scope:** Ports required by lib-synology-dsm v2, Proxmox NFS storage, and SSH admin access.
> **Action:** Enable DSM firewall, allow only these ports from trusted source IPs.

---

## Required ports

| Port | Protocol | Service | Used by | Notes |
|---|---|---|---|---|
| 5001 | TCP | HTTPS | lib-synology-dsm v2 API, DSM Web UI | **Primary — use this only. Disable 5000.** |
| 5000 | TCP | HTTP | DSM Web UI (insecure) | **Block/disable — all API calls use HTTPS** |
| 22 | TCP | SSH | Admin access, Rune automation | Restrict to trusted IPs only (10.6.224.x) |
| 111 | TCP+UDP | portmapper (rpcbind) | NFS prerequisite | Required for Proxmox NFS mounts |
| 2049 | TCP+UDP | NFS | Proxmox PoC storage mounts | Core NFS port |
| 892 | TCP+UDP | mountd | NFS mount daemon | Required for NFS mount negotiation |
| 32765–32768 | TCP+UDP | nlockmgr / statd | NFS lock manager | Required for NFS file locking |

## Ports NOT required (block/disable)

| Port | Service | Why |
|---|---|---|
| 5000 | HTTP DSM | All lib calls are HTTPS. No reason to expose HTTP. |
| 443 | WebDAV HTTPS | WebDAV not enabled or used. |
| 80 | WebDAV HTTP | WebDAV not enabled or used. |

## Recommended firewall rule set

**Source zones to allow:**

| Zone | CIDR | Allowed ports |
|---|---|---|
| Infra management | 10.6.224.0/24 | 5001, 22, 111, 2049, 892, 32765-32768 |
| PoC VMs | 10.6.225.0/24 | 5001, 111, 2049, 892, 32765-32768 |
| All others | * | DENY all |

> **Note:** Lock 5001 to management/PoC subnets only. No WAN exposure.
> NFS ports (111, 892, 2049, 32765–32768) should be restricted to Proxmox node IPs.

## lib-synology-dsm v2 — transport summary

All API calls in `src/synology_dsm_v2/client.py` use:
- `https://<host>:5001/webapi/entry.cgi` (default)
- `verify_ssl=False` intentional (no cert infra yet — ADR decision 2026-03-30)
- Port configurable via `DSMClient(host, port=5001, https=True)`

No other ports are touched by the library.

---

*Generated: 2026-03-31 | Owner: Rune Agent | Review: @yboujraf before applying firewall rules*
