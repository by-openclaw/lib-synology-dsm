# Cross-Repo Sync Summary

> **Scope:** All 5 repos + workspace — what should exist everywhere, what's missing where
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)

---

## Per-repo file matrix

| File | lib-synology-dsm | ansible-platform | infra-terraform-proxmox | platform-setup | doc-platform-core |
|---|---|---|---|---|---|
| **CLAUDE.md** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **AGENTS.md** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **README.md** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **CONTRIBUTING.md** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **CHANGELOG.md** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **SECURITY.md** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **LICENSE** | ✅ (MIT) | ❌ | ❌ | ❌ | ✅ (CC BY-SA) |
| **RAID.md** | ❌ | ❌ | ❌ | ❌ | ✅ (docs/raid.md) |
| **docs/adr/** | ✅ (5 ADRs) | ✅ (empty) | ✅ (empty) | ✅ (empty) | ✅ (8 ADRs) |
| **docs/audits/agent-files/** | ✅ (18 files) | ✅ (created) | ✅ (created) | ✅ (created) | ✅ (created) |
| **docs/archive/** | ✅ (created) | ❌ | ❌ | ❌ | ✅ |
| **.github/CODEOWNERS** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **.github/ISSUE_TEMPLATE/** | ✅ (2) | ❌ | ❌ | ✅ (3 RAID) | ❌ |
| **.github/PULL_REQUEST_TEMPLATE.md** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **project-board-sync.yml** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **release-please.yml** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **discord-notify.yml** | ❌ (removed) | ⚠️ VERIFY | ⚠️ VERIFY | ⚠️ VERIFY | ❌ |

---

## What every repo SHOULD have (per ADR-0006 charter)

| File | Required by | Status across repos |
|---|---|---|
| README.md | ADR-0006 | ✅ All 5 |
| CLAUDE.md | ADR-0006 | ✅ All 5 |
| AGENTS.md | ADR-0006 | ✅ All 5 |
| CHANGELOG.md | ADR-0006 | ✅ All 5 |
| CONTRIBUTING.md | Best practice | ❌ Missing in 4/5 repos |
| SECURITY.md | Best practice (especially for infra/security repos) | ❌ Missing in 4/5 repos |
| docs/adr/ | ADR-0006 | ✅ All 5 (but 3 are empty) |
| docs/archive/ | Decision Q4 | ❌ Missing in 3/5 repos |
| .github/ISSUE_TEMPLATE/ | ADR-0006 | ❌ Missing in 3/5 repos |
| .github/PULL_REQUEST_TEMPLATE.md | Best practice | ❌ Missing in 4/5 repos |
| .github/CODEOWNERS | Best practice | ❌ Missing in 1/5 repos |
| project-board-sync.yml | ADR-0003 (atomic rule) | ❌ Missing in 3/5 repos |

---

## Cross-repo consistency issues

### 1. CONTRIBUTING.md exists only in lib-synology-dsm

The other 4 repos have no contributor guide. A template exists in `doc-platform-core/docs/templates/CONTRIBUTING.tpl.md` — instantiate it per repo.

### 2. SECURITY.md exists only in lib-synology-dsm

ansible-platform (security hardening), infra-terraform-proxmox (infrastructure), and platform-setup (configs) all handle sensitive operations. They need disclosure policies.

### 3. Issue templates exist in only 2/5 repos

lib-synology-dsm has bug/feature templates. platform-setup has RAID templates. The other 3 have none.

**Recommendation:** All repos get at minimum a bug report template. platform-setup's RAID templates should be shared across all repos (since the RAID atomic rule applies everywhere).

### 4. Project board automation in only 2/5 repos

platform-setup and doc-platform-core have `project-board-sync.yml`. The other 3 don't. The atomic rule (ADR-0003) applies to all repos.

### 5. Empty ADR directories in 3 repos

ansible-platform, infra-terraform-proxmox, and platform-setup have `docs/adr/README.md` but zero ADRs. Each repo has decisions worth recording:

| Repo | ADR candidates |
|---|---|
| ansible-platform | SSH port 22222, break-glass pattern, sshd full replacement |
| infra-terraform-proxmox | bpg/proxmox provider choice, local state + NAS backup, module structure |
| platform-setup | Tool layout convention, config description rule, anonymization strategy |

### 6. CLAUDE.md / AGENTS.md duplication pattern repeats

Same finding as lib-synology-dsm (audit 02): standing rules, commit standards, and "What NOT to do" items appear in both CLAUDE.md and AGENTS.md across all repos. The deduplication strategy from audit 02 should be applied everywhere.

### 7. discord-notify.yml status unclear in 3 repos

MEMORY.md says removed. Audit 14 says may still exist. Verify in ansible-platform, infra-terraform-proxmox, platform-setup.

---

## Secrets requiring redaction across repos

| Repo | File | Content | Format |
|---|---|---|---|
| infra-terraform-proxmox | docs/variables-reference.md:30 | Password `BySyst3ms_` | `<REDACTED:password>` |
| infra-terraform-proxmox | docs/vm-test-spec-review.md:81,133 | Password `BySyst3ms_` | `<REDACTED:password>` |
| doc-platform-core | docs/stack.md:437,447 | Discord webhook token (FULL) | `<REDACTED:token>` **CRITICAL** |
| doc-platform-core | docs/adr/0008:54 | Password in API example | `<REDACTED:password>` |
| doc-platform-core | docs/adr/0006:96-97 | SSH public keys | `<REDACTED:ssh-pubkey>` |

**Workspace-level (not in repos):**

| Location | Content | Format |
|---|---|---|
| workspace/TOOLS.md:53,58,63,80 | SSH keys + password | `<REDACTED:ssh-pubkey>`, `<REDACTED:password>` |
| workspace/memory/2026-03-26.md:235,237 | Password | `<REDACTED:password>` |
| workspace/memory/2026-03-27.md:59,181 | Password | `<REDACTED:password>` |
| workspace/docs/stack.md:437,447 | Discord webhook token | `<REDACTED:token>` **CRITICAL** |

---

## Priority execution order

### Wave 1 — Security (do immediately)

1. Redact Discord webhook token in doc-platform-core + workspace (CRITICAL)
2. Redact all passwords across repos + workspace
3. Rotate Discord webhook
4. Verify discord-notify.yml removal in 3 repos

### Wave 2 — Missing files (one PR per repo)

5. Create CONTRIBUTING.md in 4 repos (from template)
6. Create SECURITY.md in 3 repos (ansible, terraform, platform-setup)
7. Add issue templates to 3 repos (copy from lib-synology-dsm)
8. Add PR template to 4 repos
9. Add project-board-sync.yml to 3 repos
10. Add CODEOWNERS to ansible-platform

### Wave 3 — Content alignment (one PR per repo)

11. Deduplicate CLAUDE.md vs AGENTS.md in all repos (same pattern as lib-synology-dsm)
12. Record repo-level ADRs (at least 1-2 per repo)
13. Create docs/archive/ in 3 repos
14. Update stale CLAUDE.md snapshots (platform-setup, infra-terraform-proxmox)

### Wave 4 — Workspace cleanup

15. Resolve workspace/docs/ duplication with doc-platform-core
16. Archive memory/ daily logs
17. Remove or repurpose IDENTITY.md
18. Verify infra/secrets/ not git-tracked

---

## Workspace file hierarchy — proposed canonical model

```
workspace/
  SOUL.md              → Agent identity (who Rune is)
  USER.md              → Human identity (who My Lord is)
  MEMORY.md            → Hot memory (~80 lines, curated)
  MEMORY-archive.md    → Cold memory (historical, append-only)
  AGENTS.md            → Workspace-level agent onboarding (session startup, sync rules)
  HEARTBEAT.md         → Periodic check directives
  TOOLS.md             → Local environment specifics

  repos/
    lib-synology-dsm/
      CLAUDE.md        → Repo-specific Claude contract
      AGENTS.md        → Repo-specific agent onboarding
      CONTRIBUTING.md  → How to contribute
      ...

    ansible-platform/   → same pattern
    infra-terraform-proxmox/ → same pattern
    platform-setup/     → same pattern
    doc-platform-core/  → same pattern (canonical docs source)
```

**Reading order for any agent, any session:**
1. `workspace/SOUL.md` (who am I)
2. `workspace/USER.md` (who is the human)
3. `workspace/AGENTS.md` (session rules)
4. `{repo}/AGENTS.md` (repo onboarding)
5. `{repo}/CLAUDE.md` (repo-specific rules)
6. `workspace/MEMORY.md` (on demand — session context)

---

*This summary is the map. The per-repo audits (00-overview.md in each repo) are the territory. Execute wave by wave.*
