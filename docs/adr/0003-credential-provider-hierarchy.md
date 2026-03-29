# ADR-0003: Layered credential provider hierarchy

**Date:** 2026-03-29
**Status:** Accepted

## Context

The library needs DSM credentials (host, port, user, password) in multiple environments:
- **Development:** local `.env` file or environment variables on a workstation
- **CI/CD:** environment variables injected by the pipeline
- **Production:** HashiCorp Vault (when deployed, Phase 2+)
- **Tests:** explicit values passed directly (no file, no Vault)

A single hardcoded credential strategy would not work across all these contexts.

## Decision

Implement a layered provider hierarchy in `synology_dsm.credentials`:

```
Priority 1: VaultCredentialProvider — VAULT_ADDR + VAULT_TOKEN set → fetch from Vault KV v2
Priority 2: EnvCredentialProvider  — SYNOLOGY_HOST env var set → read from env / .env file
Priority 3: Explicit               — pass host/user/password directly to DSMClient (tests)
```

`get_credentials()` auto-detects the right provider. Individual providers can be instantiated directly for explicit control.

`DSMCredentials` is a plain dataclass — providers return it, callers consume it.

`hvac` (Vault SDK) is an optional dependency — `ImportError` raised with clear install instructions if Vault provider is used without it.

## Consequences

**Positive:**
- Same code runs in dev (`.env`) and prod (Vault) without changes
- Vault integration test is mocked — no live Vault needed until Phase 2
- Explicit fallback always works for unit tests (no env setup required)

**Negative:**
- Vault AppRole authentication not yet implemented — currently only token auth
- `.env` file loading requires `python-dotenv` (optional dep, added to dev extras)
- Priority logic in `get_credentials()` may surprise users who have both VAULT_ADDR and SYNOLOGY_HOST set — Vault takes priority, with silent fallback to env on Vault error
