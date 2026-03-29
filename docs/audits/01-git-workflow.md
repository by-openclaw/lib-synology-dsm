# Git Workflow Audit

## 1. Healthy Points

1. The worktree was clean during audit.
   Evidence: `git status --short --branch` returned `## main`.
2. Commit history follows a mostly conventional style.
   Evidence: recent commits include `feat:`, `fix:`, `test:`, `ci:`, `chore(main): release ...`.
3. CI exists for push and pull request events on `main`.
   Evidence: `.github/workflows/ci.yml`.
4. Release automation exists.
   Evidence: `.github/workflows/release-please.yml`, `release-please-config.json`, `tool.commitizen` in `pyproject.toml`, and `scripts/release.sh`.
5. Contribution workflow guardrails exist.
   Evidence: `.pre-commit-config.yaml`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/CODEOWNERS`, `.github/dependabot.yml`.

## 2. Findings

1. High: release/tag provenance is inconsistent.
   Evidence:
   `pyproject.toml` version is `0.9.0`.
   `src/synology_dsm/__init__.py` version is `0.9.0`.
   git log contains `chore(main): release 0.8.2` and `chore(main): release 0.9.0`.
   local tags stop at `v0.7.0`.
   Impact:
   release history cannot be trusted from git tags alone, and tooling depending on tags may produce wrong changelogs, ranges, or rollback points.
2. High: two release mechanisms exist and are not obviously harmonized.
   Evidence:
   repository uses both Release Please and `scripts/release.sh` with Commitizen.
   Impact:
   parallel release paths increase the chance of mismatched versions, duplicate release commits, or tag drift.
3. Medium: Release Please depends on a custom secret instead of the default repository token.
   Evidence:
   `.github/workflows/release-please.yml` uses `secrets.GH_TOKEN`.
   Impact:
   release automation has an avoidable operational dependency on secret provisioning.
   If `GH_TOKEN` is missing, rotated, or over-scoped, releases fail or become harder to audit.
4. Medium: the release script mutates docs after version bump and creates an extra commit.
   Evidence:
   `scripts/release.sh` updates `AGENTS.md`, then may create `docs: update project docs to ${NEW_TAG}` after `cz bump`.
   Impact:
   one release may create multiple commits with mixed responsibilities, which complicates changelog interpretation and bisectability.
5. Medium: pre-commit secret scanning explicitly excludes integration shell scripts.
   Evidence:
   `.pre-commit-config.yaml` excludes `tests/integration/.*\.sh`.
   Impact:
   the repo’s highest-risk manual test layer is outside the local secret-scanning safety net.
6. Medium: branch governance cannot be verified locally.
   Evidence:
   no local artifact proves branch protection, required status checks, review requirements, or signed commit enforcement.
   Impact:
   the repository may still rely on convention rather than enforced policy.

## 3. Recommendations

1. Make one release path authoritative.
   Prefer either Release Please or Commitizen-driven local release automation, not both.
2. Reconcile tag history immediately.
   Verify whether `v0.8.2` and `v0.9.0` exist remotely but were not fetched, or whether they were never published.
3. If Release Please remains the source of truth, use the default `GITHUB_TOKEN` unless a stronger reason exists for `GH_TOKEN`.
4. Move post-release documentation/stat updates into the same controlled release workflow or remove them from the release script.
5. Re-enable secret scanning for shell integration assets, or replace the exclusion with narrower allowlists.
6. Document the enforced repository rules outside code.
   Add a short `docs/audits` or `CONTRIBUTING.md` note describing branch protection, required checks, and release authority.

## 4. Suggested Action Order

1. Verify remote tags for `v0.8.2` and `v0.9.0`.
2. Decide which release mechanism is canonical.
3. Simplify the workflow to one release source plus one tag source.
4. Tighten pre-commit exclusions.
5. Document branch protection assumptions.
