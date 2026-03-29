# PEP Compliance Audit

## 1. PEP Areas Reviewed

1. PEP 8:
   style and formatting.
2. PEP 257:
   docstrings.
3. PEP 484:
   type hints.
4. PEP 561:
   typed package marker.
5. PEP 621:
   project metadata in `pyproject.toml`.
6. PEP 440:
   version string format.

## 2. Healthy Points

1. PEP 8 formatting is in good shape.
   Evidence:
   `ruff check src/ tests/` passed.
   `ruff format --check src/ tests/` passed.
2. Public API docstring coverage is broadly good.
   Evidence:
   core modules and managers are consistently documented.
3. PEP 561 support is present.
   Evidence:
   `src/synology_dsm/py.typed` exists.
4. PEP 621 metadata usage is correct in principle.
   Evidence:
   project name, version, description, readme, license, Python requirement, authors, classifiers, and URLs are in `pyproject.toml`.
5. PEP 440 version formatting is valid.
   Evidence:
   `0.9.0` is a valid normalized version.

## 3. Findings

1. High: PEP 484 typing compliance is the weakest area in the repository.
   Evidence:
   `mypy` fails with 27 errors across 7 files.
   Impact:
   the repository advertises typed quality but does not currently satisfy its own type-checking contract.
2. High: annotation design is being undercut by class-scope naming collisions.
   Evidence:
   methods named `list` cause `mypy` errors where later annotations use `list[...]`.
   Impact:
   this is a correctness issue in the typing layer, not just a cosmetic warning.
3. Medium: many public methods return bare `dict` or `list[dict]`.
   Impact:
   type hints exist, but they do not provide strong semantic guarantees.
4. Medium: some functions return `Any` through untyped JSON access patterns.
   Evidence:
   `mypy` reports multiple `Returning Any from function declared to return ...` errors.
   Impact:
   static guarantees are weakened around the API boundary.
5. Low: lint configuration intentionally ignores some simplification rules.
   Evidence:
   `SIM105`, `SIM117`, and `C408` are ignored in Ruff.
   Impact:
   this is acceptable if intentional, but it should be treated as style policy, not as accidental debt.

## 4. Recommendations

1. Resolve the `mypy` failures before claiming type-checking as a required contributor gate.
2. Rename ambiguous methods or qualify builtins to avoid class-scope collisions.
   Example direction:
   use `builtins.list[...]` carefully,
   or rename public methods like `list()` to more specific names only if the API can absorb that change,
   or use alias types defined outside class scope.
3. Add `TypedDict` models for:
   user records,
   group records,
   share records,
   NFS rules,
   storage volumes.
4. Tighten return annotations at the client boundary.
   Even partial internal helper types would reduce `Any` leakage.
5. Keep Ruff and mypy aligned.
   A green linter plus a red type checker should be treated as incomplete compliance, not mostly compliant.

## 5. Compliance Verdict

1. PEP 8:
   strong.
2. PEP 257:
   good.
3. PEP 484:
   currently failing in practice.
4. PEP 561:
   good.
5. PEP 621:
   good.
6. PEP 440:
   good.
