# Audit: pyproject.toml

> **Scope:** `lib-synology-dsm/pyproject.toml`
> **Audited:** 2026-03-30
> **Auditor:** Rune (via Claude Opus)
> **Action required:** MINOR — well-structured, small gaps

---

## Purpose

pyproject.toml is the **single source of truth** for:
- Package metadata (name, version, Python requirement)
- Build system (hatchling)
- Dependencies (zero runtime, dev/vault/container extras)
- Tool configuration (ruff, mypy, pytest)

---

## Current state

- **Package:** synology-dsm v0.9.3
- **Python:** >=3.10
- **Build:** hatchling
- **Runtime deps:** zero (stdlib only — ADR-0001)
- **Extras:** dev, container, vault
- **Ruff:** line-length 100
- **Mypy:** strict, disallow_untyped_defs
- **Pytest:** tests/unit/, 80% coverage threshold

---

## What's good

| Aspect | Verdict | Notes |
|---|---|---|
| Zero runtime deps | Strong | Enforces ADR-0001 at package level |
| Three extras (dev/container/vault) | Good | Clean separation of optional deps |
| Ruff + mypy config in pyproject | Good | Single config file, no tox.ini/setup.cfg drift |
| Hatchling build backend | Good | Modern, PEP 517/518 compliant |
| Coverage threshold | Set at 80% | See issue below |

---

## Issues

| Item | Problem | Fix |
|---|---|---|
| Coverage threshold = 80% | README claims 100%, PR template says 80%, pyproject enforces 80%. The gate is lower than the claim. | Decision: raise to 95% (allows minor drift) or keep 80% as safety net. 100% as gate is fragile. |
| `build` in dev deps | CLAUDE.md open issues says "build not in dev deps — wheel/sdist not CI-validated" | Verify — is `build` now in `[project.optional-dependencies.dev]`? If yes, close the issue. |
| No `nox` in dev deps | CONTRIBUTING.md will document nox usage (audit 06-M5) but nox isn't in dev extras | Add `nox` to dev deps if multi-python testing is expected |
| mypy strict mode | Good, but 27 errors still open | Not a pyproject issue — tracked in CLAUDE.md |

---

## Action items

| # | Action | Priority | Effort |
|---|---|---|---|
| A1 | Decide coverage threshold: keep 80% gate or raise | LOW | Decision |
| A2 | Verify `build` is in dev deps — close CLAUDE.md open issue if resolved | LOW | Low |
| A3 | Add `nox` to dev deps if nox usage is adopted | LOW | Low |

---

## Design principles applied

- **Single source of truth:** Version, deps, and tool config all in pyproject.toml. No setup.py, no setup.cfg.
- **Minimal surface:** Zero runtime deps enforced at package level, not just by convention.
- **Fail-fast:** Mypy strict mode catches type issues at lint time, not runtime.

---

*Lowest priority audit. pyproject.toml is healthy.*
