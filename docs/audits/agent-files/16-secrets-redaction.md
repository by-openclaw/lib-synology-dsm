# Audit: Secrets, Credentials, and Sensitive Content Redaction

> **Scope:** All workspace files + all 5 repos — secrets, passwords, tokens, SSH keys, webhooks
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** YES — plaintext password in multiple files, Discord webhook token fully exposed

---

## Redaction format standard

All sensitive values must be redacted using one consistent format:

```
<REDACTED:{type}>
```

Where `{type}` describes what was redacted:

| Type | Example | Used for |
|---|---|---|
| `<REDACTED:password>` | replaces `BySyst3ms_` | Any password |
| `<REDACTED:token>` | replaces webhook token strings | API tokens, Discord tokens, PATs |
| `<REDACTED:ssh-pubkey>` | replaces `ssh-ed25519 AAAA...` | SSH public keys |
| `<REDACTED:ssh-privkey>` | replaces private key content | SSH private keys |
| `<REDACTED:secret>` | replaces generic secrets | Anything else sensitive |
| `<REDACTED:ip-range>` | replaces `10.6.x.x/y` | Internal IP ranges (when needed) |

**Rule:** The tag replaces the value only, not the surrounding context. Example:
```
# Before:
password: BySyst3ms_

# After:
password: <REDACTED:password>
```

---

## Findings — by severity

### CRITICAL: Discord webhook token fully exposed

| File | Line | Content |
|---|---|---|
| `workspace/docs/stack.md` | 437 | Full webhook URL with token: `https://discord.com/api/webhooks/1486554668401164370/p9KvIUO84N...7/github` |
| `workspace/docs/stack.md` | 447 | Same full token in `gh api` command example |

**Action:** Redact token, rotate the webhook immediately (token is compromised if this file was ever shared or pushed).

**After:**
```
https://discord.com/api/webhooks/1486554668401164370/<REDACTED:token>/github
```

---

### HIGH: Plaintext password `BySyst3ms_` in 6+ files

| File | Lines | Context |
|---|---|---|
| `workspace/TOOLS.md` | 80 | VM user password |
| `workspace/memory/2026-03-27.md` | 59, 181 | API login, SSH passphrase |
| `workspace/memory/2026-03-26.md` | 235, 237 | Proxmox root password, SSH key passphrase |
| `repos/infra-terraform-proxmox/docs/vm-test-spec-review.md` | 81, 133 | Console password |
| `repos/infra-terraform-proxmox/docs/variables-reference.md` | 30 | Terraform variable default |
| `repos/doc-platform-core/docs/adr/0008-terraform-state-management.md` | 54 | API login example |

**Action:** Replace all instances with `<REDACTED:password>`.

---

### MEDIUM: SSH public keys in docs

SSH public keys are not secrets (they're designed to be public). However, documenting them in markdown files creates inventory management issues — if a key is rotated, every doc with the old key is stale.

| File | Lines | Key comment |
|---|---|---|
| `workspace/TOOLS.md` | 53, 58, 63 | `by-systems@ws-win11-ref`, `by-systems@rune-vm`, `rune@by-systems-rune-vm` |
| `workspace/MEMORY.md` | 115–116 | Two keys (already flagged in audit 04) |
| `repos/doc-platform-core/docs/adr/0006-platform-charter.md` | 96–97 | `yboujraf@personal`, `rune@by-systems-rune-vm` |
| `repos/infra-terraform-proxmox/docs/vm-test-spec-review.md` | 82–83 | Two keys |
| `repos/platform-setup/tools/proxmox/runbooks/installation-baseline.md` | 351 | Legacy key |

**Recommendation:** Two options:
- **A: Redact** — replace with `<REDACTED:ssh-pubkey>` and reference the key management source (Terraform variables, `~/.ssh/`)
- **B: Keep** — public keys are safe to share. But add a note: "Authoritative source: Terraform variables / cloud-init config. This copy may be stale."

**Recommended: Option A** for docs/memory files (reduce stale copies). Keep in Terraform variables (that's the source of truth).

---

### LOW: Internal IP addresses

IP ranges (`10.6.224.0/20`, `10.6.225.x`, etc.) appear in:
- `workspace/MEMORY.md`, `MEMORY-archive.md`
- `.env.example` files
- `docs/hardening.md`
- `docs/adr/0006-platform-charter.md`
- Various audit files in this set

**Recommendation: Don't redact.** Internal RFC 1918 addresses are not secrets. They're needed for context. Anyone with repo access needs them to understand the network topology.

**Exception:** If the repos go public, redact IP addresses. Currently all repos are private — keep them.

---

### LOW: Email addresses

`security@by-systems.be` appears in SECURITY.md — this is intentional (vulnerability reporting contact).

Other email references are in naming conventions and templates — not sensitive.

**Action: No redaction needed.**

---

### CLEAN: lib-synology-dsm repo

The lib-synology-dsm repo itself is **clean**:
- `.env.example` has empty placeholders
- `detect-secrets` pre-commit hook active
- No real tokens, passwords, or SSH keys in source code
- `TmpPass123!` in README/CONTRIBUTING is a documented test example (acceptable)
- All credential handling goes through `DSMCredentials` provider pattern

---

## Summary of required redactions

| # | File | What to redact | Format |
|---|---|---|---|
| R1 | `workspace/docs/stack.md:437,447` | Discord webhook token (FULL TOKEN) | `<REDACTED:token>` |
| R2 | `workspace/TOOLS.md:80` | Password `BySyst3ms_` | `<REDACTED:password>` |
| R3 | `workspace/memory/2026-03-27.md:59,181` | Password `BySyst3ms_` | `<REDACTED:password>` |
| R4 | `workspace/memory/2026-03-26.md:235,237` | Password `BySyst3ms_` | `<REDACTED:password>` |
| R5 | `repos/infra-terraform-proxmox/docs/vm-test-spec-review.md:81,133` | Password `BySyst3ms_` | `<REDACTED:password>` |
| R6 | `repos/infra-terraform-proxmox/docs/variables-reference.md:30` | Password default `BySyst3ms_` | `<REDACTED:password>` |
| R7 | `repos/doc-platform-core/docs/adr/0008-terraform-state-management.md:54` | Password in API example | `<REDACTED:password>` |
| R8 | `workspace/TOOLS.md:53,58,63` | SSH public keys | `<REDACTED:ssh-pubkey>` |
| R9 | `workspace/MEMORY.md:115-116` | SSH public keys | `<REDACTED:ssh-pubkey>` |
| R10 | `repos/doc-platform-core/docs/adr/0006-platform-charter.md:96-97` | SSH public keys | `<REDACTED:ssh-pubkey>` |
| R11 | `repos/infra-terraform-proxmox/docs/vm-test-spec-review.md:82-83` | SSH public keys | `<REDACTED:ssh-pubkey>` |
| R12 | `repos/platform-setup/tools/proxmox/runbooks/installation-baseline.md:351` | SSH public key (legacy) | `<REDACTED:ssh-pubkey>` |

---

## Post-redaction actions

1. **Rotate Discord webhook** — the token in `stack.md` is compromised if the file was ever accessible. Generate a new webhook in Discord server settings.
2. **Consider rotating the password** — `BySyst3ms_` appears in 6+ files across workspace and repos. If any of these were pushed to a remote, the password is compromised.
3. **Add `<REDACTED:*>` pattern to detect-secrets baseline** — so the redaction tags themselves don't trigger false positives.
4. **Update Terraform variables** — if `ci_password` default is changed, update the Terraform variable definition.

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Redact Discord webhook token in stack.md + rotate webhook | CRITICAL | Low |
| A2 | Redact all `BySyst3ms_` instances (R2–R7) | HIGH | Low |
| A3 | Redact SSH public keys in docs/memory files (R8–R12) | MEDIUM | Low |
| A4 | Rotate Discord webhook after redaction | HIGH | Low |
| A5 | Consider rotating password after redaction | MEDIUM | Decision |
| A6 | Add redaction format to CONTRIBUTING.md or SOUL.md as a standard | LOW | Low |

---

## Design principles applied

- **Consistent format:** One redaction tag pattern across all files, all repos. `<REDACTED:{type}>` — no variations.
- **Preserve context:** Redact the value, not the surrounding documentation. The doc remains useful.
- **Single source of truth for secrets:** Credentials live in Vault (Phase 2) or Terraform variables (Phase 1). Docs reference, not duplicate.
- **Defence in depth:** detect-secrets catches new leaks. This audit catches historical ones. Rotation limits blast radius.

---

*To apply: Start with A1 (Discord webhook — CRITICAL). Then A2 (passwords). Then A3 (SSH keys). A4 and A5 are post-redaction follow-ups.*
