# Dependency Licenses

All runtime and development dependencies of `lib-synology-dsm` and their licenses.

## Runtime dependencies

| Package | Version constraint | License | Notes |
|---|---|---|---|
| `pydantic` | ≥2.0 | MIT | Data validation |

## Development dependencies

| Package | Version constraint | License | Notes |
|---|---|---|---|
| `pytest` | latest | MIT | Test runner |
| `pytest-cov` | latest | MIT | Coverage plugin |
| `ruff` | latest | MIT | Linter + formatter |
| `mypy` | latest | MIT | Static type checker |
| `python-dotenv` | ≥1.0 | BSD-3-Clause | `.env` file loader |
| `commitizen` | latest | MIT | Conventional commits + versioning |

## Optional dependencies

| Package | Version constraint | License | When required |
|---|---|---|---|
| `hvac` | latest | Apache-2.0 | Vault credential provider (`pip install lib-synology-dsm[vault]`) |
| `python-dotenv` | ≥1.0 | BSD-3-Clause | Also optional for non-dev use |

## License compatibility summary

All dependencies are permissive open-source licenses compatible with MIT:

| License | Commercial use | Redistribution | Modification | Patent rights |
|---|---|---|---|---|
| MIT | ✅ | ✅ | ✅ | ❌ explicit |
| BSD-3-Clause | ✅ | ✅ (with attribution) | ✅ | ❌ explicit |
| Apache-2.0 | ✅ | ✅ (with attribution) | ✅ | ✅ explicit grant |

No GPL, AGPL, LGPL, or proprietary dependencies.

## Compliance notes

- `python-dotenv` (BSD-3-Clause): redistribution must include the copyright notice. Not applicable to internal use.
- `hvac` (Apache-2.0): redistribution must include NOTICE file if applicable. Not applicable to internal use.
- This library itself is MIT licensed — see [`LICENSE`](../LICENSE).

## Verification

Dependencies can be verified with:

```bash
pip-licenses --format=markdown --order=license
# Requires: pip install pip-licenses
```
