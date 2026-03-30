# Git Workflow Re-Audit

## 1. Progress Confirmed

1. The worktree is clean.
   Evidence: `git status --short --branch` returned `## main`.
2. The repo still uses CI, PR templates, CODEOWNERS, and Dependabot.
3. The duplicate local release script path has been removed.
   Evidence: `scripts/` no longer exists.
   This is a real improvement over the previous audit.
4. Recent commits show active follow-through on audit findings.
   Evidence:
   `fix(types): resolve all 27 mypy errors across 7 files`
   `docs: replace Codecov badge with static 100% badge, expand Testing section`
   `chore(devcontainer): update Python 3.12 → 3.13`.

## 2. Remaining Findings

1. High: release/tag provenance is still inconsistent.
   Evidence:
   project version is `0.9.0`,
   release commits for `0.8.2` and `0.9.0` exist,
   local tags still stop at `v0.7.0`.
   Impact:
   release history cannot yet be treated as fully authoritative from git metadata alone.
2. Medium: Release Please still depends on a custom secret.
   Evidence:
   `.github/workflows/release-please.yml` still uses `secrets.GH_TOKEN`.
   Impact:
   release automation still has an avoidable secret-management dependency.
3. Medium: branch governance is still not locally provable.
   Evidence:
   no local artifact proves branch protection, required checks, review rules, or signed commit enforcement.
4. Medium: local secret scanning still excludes the integration shell layer.
   Evidence:
   `.pre-commit-config.yaml` still excludes `tests/integration/.*\.sh`.

## 3. Resolved Findings From Prior Audit

1. Resolved:
   dual release paths.
   `release.sh` is gone.
2. Resolved:
   stale Python support badge in README.
   README now shows `3.10 | 3.11 | 3.12 | 3.13`.
3. Resolved:
   broken Codecov dependency in CI/README.
   Codecov upload step is removed and coverage artifacts remain in GitHub Actions.

## 4. Recommended Next Git Workflow Tasks

1. Verify whether `v0.8.2` and `v0.9.0` exist remotely and were not fetched, or whether they were never published.
2. If missing, repair the tag history before the next release.
3. Consider switching Release Please to the default `GITHUB_TOKEN` if repository policy allows it.
4. Narrow the `detect-secrets` exclusions for integration shell files instead of excluding the whole layer.
