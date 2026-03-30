# Audit: GitHub Templates + CODEOWNERS

> **Scope:** `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/`, `.github/CODEOWNERS`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** MINOR — mostly solid, small alignment gaps

---

## Files audited

| File | Exists | Status |
|---|---|---|
| `.github/PULL_REQUEST_TEMPLATE.md` | Yes | Good |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Yes | Good |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Yes | Good |
| `.github/CODEOWNERS` | Yes | Minimal |
| `.github/dependabot.yml` | Yes | Not audited (automated) |
| `.github/workflows/` | Yes | Not audited here (CI scope) |

---

## PR Template

### What's good
- Type selection (bug fix, feature, breaking, docs)
- Quality gates checklist: ruff check, ruff format, mypy, pytest, 80% coverage
- Documentation and changelog requirements

### Issues

| Item | Problem | Fix |
|---|---|---|
| Coverage threshold | Says 80% — but README and project claim 100% | Align: either raise template to 100% or clarify 80% is minimum gate |
| No label requirement | Refactor doc §5.2.b identified missing label enforcement | Add `## Labels` section: require at least one label before merge |
| No link to DoD | PR checklist overlaps with DoD but doesn't reference it | Add: "Full Definition of Done: see CONTRIBUTING.md" |
| No closing keyword reminder | §5.2.a: `Closes #N` not enforced | Add to template: `Closes #___` pre-filled field |

---

## Issue Templates

### bug_report.md — good
- DSM version, hardware, lib version, Python version — all required fields
- Reproduction steps, logs sections

### feature_request.md — good
- DSM API/feature, use case, proposed interface

### Missing

| Item | Why |
|---|---|
| No `label` field pre-filled | Refactor doc §5.2.d — issues can be opened without labels |
| No issue template for "chore" or "docs" | Minor — not every type needs a template |

**Fix:** Add `labels: ["bug"]` to bug_report.md frontmatter, `labels: ["enhancement"]` to feature_request.md frontmatter.

---

## CODEOWNERS

Current: `@yboujraf` owns everything.

### Issues

| Item | Problem | Fix |
|---|---|---|
| No path-specific ownership | Single owner for all files — fine for now | No action until team grows |
| No team reference | Uses personal handle, not org team | Fine for single-owner repo |

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Add `Closes #___` field to PR template | MEDIUM | Low |
| A2 | Add `labels:` frontmatter to issue templates | MEDIUM | Low |
| A3 | Add DoD reference link to PR template | LOW | Low |
| A4 | Align coverage threshold (80% template vs 100% claim) | LOW | Low |

---

*Low priority overall. Templates are functional. Label enforcement is the most impactful fix.*
