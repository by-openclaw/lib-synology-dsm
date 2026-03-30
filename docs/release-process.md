# Release Process — `lib-synology-dsm`

> **Date:** 2026-03-30
> **Applies from:** v0.9.0 onwards

---

## TL;DR

```
push commits with conventional messages → release-please opens a PR → you merge it → done
```

Never edit version numbers manually. Never run `cz bump`.

---

## Why we had version mismatches

The repo had **two release tools configured at the same time**, both doing the same job:

| Tool | Where configured | Status |
|---|---|---|
| **release-please** | `.github/workflows/release-please.yml` + `release-please-config.json` | ✅ Keep — this is the actual tool |
| **commitizen** | `pyproject.toml [tool.commitizen]` | ❌ Remove — conflicts with release-please |

When version numbers were bumped manually in `pyproject.toml` instead of via a release-please PR, commitizen's internal version tracker fell behind and `__init__.py` was sometimes missed. Three fields ended up at three different values.

---

## The correct release tool — release-please

release-please is a Google-maintained GitHub Action that:

1. Watches commits on `main`
2. Reads conventional commit messages (`feat:`, `fix:`, `chore:`, etc.)
3. Opens a **Release PR** automatically when there is something to release
4. The Release PR updates — in one atomic operation:
   - `pyproject.toml` version
   - `src/synology_dsm/__init__.py` `__version__`
   - `CHANGELOG.md`
   - `.release-please-manifest.json`
5. When you merge the Release PR → creates the git tag (e.g. `v0.9.0`)

**Version mismatch is impossible** when you use this workflow — all files are updated together by the same tool in the same PR.

---

## Correct release workflow — step by step

### 1. Write commits using conventional commit format

```bash
feat: add QuotaManager and BandwidthManager
fix: correct SYNO.Core.Group.Member API shape
chore: update action versions to fix Node.js warning
docs: add dev container LAN access README
test: fix list_members mock to use correct offset key
```

| Prefix | Semver bump | When to use |
|---|---|---|
| `feat:` | minor (0.8.x → 0.9.0) | New feature, new manager, new method |
| `fix:` | patch (0.8.1 → 0.8.2) | Bug fix, wrong API call, wrong param |
| `chore:` | none | Config, deps, CI, docs, refactor |
| `docs:` | none | Documentation only |
| `test:` | none | Tests only |
| `feat!:` or `BREAKING CHANGE:` | major (0.x → 1.0.0) | Breaking API change |

### 2. Push to main

release-please monitors `main` continuously. After your push it checks the commit history and determines if a release is needed.

### 3. release-please opens a Release PR

You will see a PR appear automatically, typically within a minute:

```
Title: chore(main): release 0.9.0
```

The PR contains:
- Updated version in `pyproject.toml`
- Updated `__version__` in `src/synology_dsm/__init__.py`
- Updated `CHANGELOG.md` with all changes since last release
- Updated `.release-please-manifest.json`

### 4. Review and merge the Release PR

Check the CHANGELOG looks correct. Merge the PR.

### 5. release-please creates the git tag

Tag `v0.9.0` is created automatically on merge. No manual tagging needed.

---

## What to remove from the repo

commitizen is no longer needed. Remove it to avoid future confusion:

**`pyproject.toml` — remove the entire `[tool.commitizen]` section:**

```toml
# DELETE this entire block:
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.8.0"
version_files = [
    "pyproject.toml:^version",
    "src/synology_dsm/__init__.py:^__version__"
]
tag_format = "v$version"
update_changelog_on_bump = true
changelog_file = "CHANGELOG.md"
```

**`pyproject.toml` — remove `commitizen` from dev dependencies:**

```toml
# before
dev = ["pre-commit", "detect-secrets", "pytest", "pytest-cov", "ruff",
       "mypy", "python-dotenv>=1.0", "commitizen", "bandit", "pip-audit"]

# after
dev = ["pre-commit", "detect-secrets", "pytest", "pytest-cov", "ruff",
       "mypy", "python-dotenv>=1.0", "bandit", "pip-audit"]
```

Commit with:
```bash
git commit -m "chore: remove commitizen — release-please owns versioning"
```

---

## One-time fix for current mismatch (v0.8.2)

The three version fields are currently out of sync. Fix once before the next release:

```bash
# 1. Fix __init__.py (still shows 0.8.1)
sed -i 's/__version__: str = "0.8.1"/__version__: str = "0.8.2"/' \
    src/synology_dsm/__init__.py

# 2. Verify .release-please-manifest.json already shows 0.8.2
cat .release-please-manifest.json
# expected: {"." : "0.8.2"}

# 3. Commit
git add pyproject.toml src/synology_dsm/__init__.py
git commit -m "chore: align version fields to 0.8.2 — one-time fix"
git push
```

After this, release-please owns all version updates. Never edit them manually again.

---

## Quick reference

| Action | Command |
|---|---|
| Normal commit | `git commit -m "fix: correct NFS rule param name"` |
| New feature | `git commit -m "feat: add StorageManager.list_volumes"` |
| Release | Merge the release-please PR — that's it |
| Check current version | `python -c "import synology_dsm; print(synology_dsm.__version__)"` |
| Check release-please manifest | `cat .release-please-manifest.json` |

---

## What NOT to do

| ❌ Don't | ✅ Do instead |
|---|---|
| Edit `version =` in `pyproject.toml` manually | Merge the release-please PR |
| Run `cz bump` | Merge the release-please PR |
| Run `git tag v0.9.0` manually | Merge the release-please PR |
| Skip the Release PR and push a version commit directly | Merge the release-please PR |
