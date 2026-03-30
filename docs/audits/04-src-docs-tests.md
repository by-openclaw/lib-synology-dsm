# Source, Docs, And Tests Re-Audit

## 1. Current Positive State

1. Source code remains well-separated by domain and easy to navigate.
2. Unit tests remain excellent.
   Evidence:
   `223 passed`, `100%` coverage.
3. Integration pytest coverage still exists.
   Evidence:
   README now documents pytest-based integration execution and the `curl` references more clearly.
4. README testing documentation improved.
   Evidence:
   coverage artifact location is now described,
   `curl` API reference scripts are now linked directly.

## 2. Source Progress

1. Major improvement:
   the former `mypy` failure set is fixed.
2. The project now has stronger evidence that source structure and annotations are maintainable.

## 3. Remaining Documentation Drift

1. Medium: README still contains old devcontainer wording.
   Evidence:
   README still mentions Python `3.12` in the devcontainer section, while the container image is now `3.13`.
2. Medium: CONTRIBUTING still contains old runtime wording.
   Evidence:
   Windows setup still recommends Python `3.12`.
   Devcontainer section still says Python `3.12`.
3. Medium: API reference still lags the actual public API.
   Evidence:
   `docs/api-reference.md` still does not document `UserManager.list_detailed()`.
   It also omits current `GroupManager` membership methods.
   It still describes older `create_with_permissions()` arguments.
4. Medium: API version reference is stale for group membership.
   Evidence:
   `docs/api-versions.md` still lists `member_set` under `SYNO.Core.Group`, while implementation relies on `SYNO.Core.Group.Member`.
5. Medium: feature coverage doc is partly stale.
   Evidence:
   `docs/feature-coverage.md` still marks user detail listing as planned even though `UserManager.list_detailed()` exists in code.

## 4. Remaining Test-Layer Notes

1. Medium: the shell integration layer still exists outside the main test gate.
   This is acceptable if treated as reference/debug tooling, but it should stay documented that way.
2. Low: the unit suite still emits intentional warnings.
   Evidence:
   Vault fallback `RuntimeWarning`,
   `UserManager.list_groups()` deprecation warnings.

## 5. Resolved Findings From Prior Audit

1. Resolved:
   README now points to CI coverage artifacts.
2. Resolved:
   README now surfaces `tests/integration/curl/`.
3. Resolved:
   stale `175 passed` count in README was corrected to `223`.

## 6. Recommended Next Docs Tasks

1. Sync README and CONTRIBUTING with the new Python `3.13` devcontainer.
2. Refresh `docs/api-reference.md` against the actual exported API surface.
3. Refresh `docs/api-versions.md` and `docs/feature-coverage.md` to match the current implementation.
