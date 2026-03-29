# ADR-0001: Use stdlib urllib instead of httpx for HTTP calls

**Date:** 2026-03-29
**Status:** Accepted

## Context

The library needs to make HTTPS calls to the Synology DSM WebAPI. Initial implementation used `httpx` (a third-party async-capable HTTP client). The deployment environment (Rune VM, DevOps workstations) has a strict policy: no external HTTP dependencies in infrastructure libraries. The constraint is operational — infrastructure tooling must be installable on air-gapped or restricted environments without pulling additional packages.

## Decision

Use Python stdlib `urllib.request` for all HTTP operations. No `httpx`, no `requests`, no `aiohttp`.

Implementation:
- `DSMClient._post()` — form-encoded POST using `urllib.request.Request` + `urlopen`
- `FileStationManager.upload()` — multipart POST using `_build_multipart()` + `urlopen`
- `FileStationManager.download()` — GET using `urlopen` with streaming read
- SSL context: `ssl._create_unverified_context()` for self-signed NAS certs (verify_ssl=False)

Network errors wrapped as `DSMConnectionError` — callers never need to import `urllib.error`.

## Consequences

**Positive:**
- Zero external HTTP dependencies — `pip install lib-synology-dsm` pulls only `pydantic`
- Works in air-gapped environments
- No version conflicts with other packages that also depend on httpx/requests

**Negative:**
- `urllib` is more verbose than httpx — especially for multipart upload
- No built-in async support (not needed for current scope)
- No HTTP/2 (DSM does not require it)
- Cookie handling is manual (needed for FileStation upload auth quirk)
