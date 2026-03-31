# ADR-0009: Local Secrets JSON Schema (Vault KV v2 Migration Format)

**Status:** Accepted
**Date:** 2026-03-31
**Deciders:** @yboujraf

## Context

Platform credentials (NAS API, Proxmox tokens, GitHub PATs) are stored locally on the Rune VM during Phase 1 (pre-Vault). Previously scattered across `.env` files with inconsistent naming and no metadata. When HashiCorp Vault is deployed (Phase 2), credentials must migrate with zero ambiguity.

## Decision

**One JSON file per credential at `workspace/infra/secrets/`, following Vault KV v2 structure.**

Schema:
```json
{
  "vault_path": "secret/{scope}/{service}/{context}",
  "description": "Human-readable purpose",
  "access": "rw|ro",
  "owner": "rune|yboujraf",
  "target": "Device — IP:port",
  "fields": {
    "key": "value"
  }
}
```

- `vault_path` — exact Vault KV v2 path for migration: `vault kv put <vault_path> <fields>`
- `description`, `access`, `owner` — human context only
- `fields` — flat KV, 1:1 with Vault. No nesting beyond one level.
- **No version, no history, no rotation timestamps** — Vault handles all of that

Naming: `{service}-{context}.json` (e.g., `synology-api.json`, `proxmox-nonprod.json`)

**Separation from OpenClaw:** OpenClaw agent secrets stay in OpenClaw's own config format. `workspace/infra/secrets/*.json` is for platform infrastructure credentials only.

## Consequences

**Positive:**
- Migration to Vault is one command per file — no reformatting
- `description` field prevents wrong credential used under pressure
- Consistent format across all platform credentials
- Old `.env` files deprecated — single format going forward

**Negative:**
- JSON not directly sourceable by shell scripts (`.env` was). Scripts must parse or use a helper.
- Local files have no encryption at rest (Vault solves this in Phase 2)

## Notes

- Old `.env` files (`.synology.env`, `.proxmox-nonprod.env`) kept as deprecated — redacted, not deleted
- Repo `.env` files (e.g., `lib-synology-dsm/.env`) are local consumers, gitignored, populated manually
- Redaction format: `<REDACTED:{type}>` per OPERATING-STANDARD.md §6.1

## Compliance

| Framework | Control | Relevance |
|---|---|---|
| ISO 27001 | A.10.1.1 | Cryptographic controls — structured schema enforces per-env secret isolation |
| ISO 27001 | A.9.4.3 | Password management — JSON schema validates credential structure, prevents plaintext leaks |
| NIS2 | Art.21(2)(d) | Supply chain security — secrets schema enables automated credential auditing |
