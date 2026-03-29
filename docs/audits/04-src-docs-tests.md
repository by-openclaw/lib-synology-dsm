# Source, Docs, And Tests Audit

## 1. Healthy Points

1. Source layout is easy to navigate.
   Evidence:
   managers are separated by domain: `client`, `users`, `groups`, `shares`, `nfs`, `filestation`, `storage`, `quota`, `bandwidth`, `credentials`, `exceptions`.
2. Unit test coverage is excellent.
   Evidence:
   `.venv/bin/pytest tests/unit/ --cov=src/synology_dsm --cov-report=term-missing -q`
   produced `223 passed` and `100.00%` total coverage.
3. Integration test structure exists in pytest form, not only shell form.
   Evidence:
   `tests/integration/test_live_nas.py` contains 51 collected integration tests.
4. Offline behavior is strong.
   Evidence:
   the unit suite is fully mocked and passes without NAS access.
5. Documentation coverage is broad.
   Evidence:
   README, API reference, credentials guide, hardening guide, ADRs, feature matrix, and contributing guide all exist.

## 2. Findings In Source

1. High: type annotations are materially out of sync with implementation.
   Evidence:
   `mypy` reports 27 errors across `client.py`, `users.py`, `groups.py`, `shares.py`, `storage.py`, `filestation.py`, and `nfs.py`.
   Impact:
   the code is tested at runtime but not type-safe at the level the project claims.
2. Medium: class methods named `list` interact poorly with later annotations using `list[...]`.
   Evidence:
   `mypy` errors such as `Function "synology_dsm.shares.ShareManager.list" is not valid as a type`.
   Impact:
   annotations inside class scope are colliding with method names and creating avoidable type-checking failures.
3. Medium: API return types are very loose.
   Evidence:
   many methods return bare `dict` or `list[dict]`.
   Impact:
   callers get weak editor/type support, and regressions are harder to catch statically.

## 3. Findings In Documentation

1. Medium: README contains stale test-count text.
   Evidence:
   one section says `223 passing`; devcontainer section still says `175 passed`.
2. Medium: README Python support badge is stale.
   Evidence:
   badge omits Python `3.13`, while CI and classifiers include it.
3. Medium: API reference lags the code.
   Evidence:
   `docs/api-reference.md` does not document several current public methods such as `UserManager.list_detailed()`, `GroupManager.add_member()`, `GroupManager.remove_member()`, and `GroupManager.list_members()`.
4. Medium: API reference still describes older signatures.
   Evidence:
   `create_with_permissions()` is documented with an older parameter shape not matching the implementation.
5. Low: documentation still centers direct script execution for integration tests.
   Evidence:
   README and CONTRIBUTING emphasize `python tests/integration/test_live_nas.py` even though the repo also supports pytest marker-based execution.

## 4. Findings In Tests

1. Medium: there are two integration-test systems to maintain.
   Evidence:
   pytest integration suite exists alongside multiple shell scripts under `tests/integration/` and `tests/integration/curl/`.
   Impact:
   API changes must be updated in at least two places, increasing drift risk.
2. Medium: `tests/integration/conftest.py` has an unguarded login fixture.
   Evidence:
   `dsm_client` logs in immediately without a skip guard.
   Impact:
   future integration tests that consume that fixture without explicit skip logic may fail noisily when env vars are absent.
3. Low: shell integration artifacts are useful as references, but they are not integrated with the main quality gates.
   Impact:
   they may silently become stale while pytest remains green.
4. Low: warnings in the unit suite are expected but should stay intentional.
   Evidence:
   unit tests currently emit a `RuntimeWarning` for Vault fallback and `DeprecationWarning` for `UserManager.list_groups()`.

## 5. Recommendations

1. Fix `mypy` before expanding the public surface further.
2. Introduce `TypedDict` or domain models for high-value API responses.
3. Refresh `docs/api-reference.md` from the actual public API surface.
4. Update README counts and compatibility badge whenever CI/test counts change.
5. Decide whether shell integration scripts are:
   primary,
   secondary references,
   or legacy assets.
   Then document that decision explicitly.
6. Add a skip guard to `tests/integration/conftest.py` so any future fixture use fails safe.

## 6. Current Evidence Snapshot

1. Unit tests:
   `223 passed`, `3 warnings`, `100% coverage`.
2. Integration tests without env:
   `51 skipped`.
3. Ruff:
   clean.
4. Format:
   clean.
5. Mypy:
   failing.
