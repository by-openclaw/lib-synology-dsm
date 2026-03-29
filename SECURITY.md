# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.8.x | ✅ Current |
| < 0.8 | ❌ No fixes |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report privately via: security@by-systems.be

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Affected version(s)

We aim to acknowledge reports within 48 hours and provide a fix within 14 days for confirmed issues.

## Scope

This library handles Synology DSM credentials. Key security considerations:
- Credentials are passed at runtime — never hardcoded in the library
- `verify_ssl=False` is intentional for self-signed NAS certificates (typical lab/home setup)
- Vault integration uses token auth — AppRole planned (platform-setup#7)
