# Audit: SECURITY.md + docs/hardening.md

> **Scope:** `lib-synology-dsm/SECURITY.md` + `lib-synology-dsm/docs/hardening.md`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — stale version, scope overlap between two security files

---

## Purpose

Two files cover security:

| File | Purpose |
|---|---|
| `SECURITY.md` | **Vulnerability disclosure policy** — how to report, SLA, scope |
| `docs/hardening.md` | **Operational hardening guide** — DSM account config, network restrictions, audit logging |

These serve different audiences: SECURITY.md is for external reporters, hardening.md is for operators.

---

## SECURITY.md — current state

- **Supported versions:** 0.8.x (stale — current is 0.9.3)
- **Contact:** security@by-systems.be
- **SLA:** 48h acknowledge, 14-day fix
- **Scope notes:** verify_ssl=False acknowledged, Vault integration planned

### Issues

| Item | Problem | Fix |
|---|---|---|
| Supported version | Says 0.8.x | Update to 0.9.x |
| Vault note | Says "Vault integration with token auth, AppRole planned" | Verify — is Vault still Phase 2? If so, keep. Add "(Phase 2)" label. |
| No GPG key for encrypted reports | security@ is email-only — no PGP key for sensitive reports | Consider adding — this is a CISO-grade environment |

---

## docs/hardening.md — current state

- **DSM account config:** admin group, allowed apps, password policy, 2FA disabled
- **Network restrictions:** 10.6.224.0/20 + 10.6.240.0/20
- **Audit logging:** File access + user/group changes

### Issues

| Item | Problem | Fix |
|---|---|---|
| Service account name | Says "future: svc-rune-dsm" | Is this still the plan? Confirm or update. |
| IP ranges | Hardcoded — will change when VLAN topology is finalized | Add note: "Ranges are PoC — update when production topology decided" |
| No reference to TLS strategy | verify_ssl=False is a security concern documented in CLAUDE.md but not hardening.md | Add section or reference to CLAUDE.md TLS decision |

---

## Scope overlap

Both files mention verify_ssl and Vault. Clarify ownership:

| Topic | Owner | Other |
|---|---|---|
| Vulnerability reporting | SECURITY.md | — |
| DSM account hardening | hardening.md | — |
| verify_ssl/TLS strategy | CLAUDE.md (pending decision) | SECURITY.md references |
| Vault credential provider | docs/credentials.md | hardening.md references |

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Update SECURITY.md supported version to 0.9.x | HIGH | Low |
| A2 | Add "(Phase 2)" to Vault reference in SECURITY.md | LOW | Low |
| A3 | Add TLS strategy reference to hardening.md | MEDIUM | Low |
| A4 | Confirm svc-rune-dsm service account name plan | LOW | Decision |
| A5 | Add PoC caveat to hardcoded IP ranges in hardening.md | LOW | Low |

---

*To apply: A1 is quick and should be done with any README update.*
