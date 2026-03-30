# Re-Audit Overview

Audit date: 2026-03-29
Repository: `lib-synology-dsm`
Audited branch: `main`
Audited HEAD: `185353d`

## 1. Purpose

1. This re-audit verifies progress since the previous `docs/audits/` review.
2. The goal is to confirm which findings are now fixed, which are still open, and which should be carried into the next task cycle.
3. This is still a repository-local audit.
   GitHub branch protection, secret configuration, and remote release/tag state cannot be fully proven from the local clone alone.

## 2. Evidence Collected

1. Repository state:
   `git status --short --branch`
   `git log --oneline --decorate -n 12`
   `git tag --sort=-version:refname`
2. Quality checks:
   `.venv/bin/mypy src/synology_dsm/ --ignore-missing-imports`
   `.venv/bin/pytest tests/unit/ --cov=src/synology_dsm --cov-report=term-missing -q`
   `.venv/bin/bandit -r src/ -ll -ii`
   `.venv/bin/pip-audit --skip-editable`
3. Packaging/build checks:
   `.venv/bin/python -m build --sdist --wheel --outdir /tmp/lib-synology-dsm-build-reaudit`
4. Drift checks:
   README, CONTRIBUTING, CI, devcontainer, API reference, API versions, feature coverage, and release workflow files were re-read.

## 3. Confirmed Progress Since Last Audit

1. The broken Codecov badge issue is fixed.
   README now uses a static `100%` coverage badge and CI no longer uploads to Codecov.
2. `mypy` is fixed.
   Current result: `Success: no issues found in 12 source files`.
3. Packaging smoke-build support is fixed.
   `build` is now in `.[dev]`, and wheel/sdist build succeeded.
4. The duplicate manual release path is removed.
   `scripts/release.sh` no longer exists.
5. The devcontainer Python image is updated to `3.13`.
6. The README now documents CI coverage artifacts and `curl` API reference scripts.

## 4. Highest Remaining Issues

1. High:
   source/release metadata still says `0.9.0`, but local git tags still stop at `v0.7.0`.
2. High:
   `DSMClient` still defaults to `verify_ssl=False`.
3. Medium:
   docs still have drift after the latest fixes.
   README and CONTRIBUTING still mention Python `3.12` in devcontainer text.
   API docs still lag actual code in a few places.
4. Medium:
   release automation still depends on `secrets.GH_TOKEN`.
5. Medium:
   pre-commit still excludes integration shell scripts from secret scanning.

## 5. Current Health Snapshot

1. Git workflow:
   improved, but release provenance is still not fully trustworthy.
2. Security:
   tooling is good, but transport defaults and secret-scan coverage still need work.
3. Python library skeleton:
   materially improved and now build-verifiable.
4. Source, docs, tests:
   source and tests are strong; documentation is the main remaining drift area.
5. PEP/style:
   materially improved because typing is now green, not just formatting.

## 6. Audit Files

1. `01-git-workflow.md`
2. `02-security.md`
3. `03-python-skeleton.md`
4. `04-src-docs-tests.md`
5. `05-pep-compliance.md`
