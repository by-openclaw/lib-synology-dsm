## Summary

<!-- What does this PR do? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation / chore

## Checklist

- [ ] `ruff check src/ tests/` passes
- [ ] `ruff format --check src/ tests/` passes
- [ ] `mypy src/synology_dsm/ src/synology_dsm_v2/ --ignore-missing-imports` passes
- [ ] v1 unit tests pass: `pytest tests/unit/ --cov=src/synology_dsm --cov-fail-under=100`
- [ ] v2 unit tests pass: `pytest tests/unit_v2/ --cov=src/synology_dsm_v2 --cov-fail-under=100`
- [ ] Coverage gate passes (100% — both v1 and v2)
- [ ] New behaviour has unit tests
- [ ] Public API changes have docstrings (PEP 257)
- [ ] `CHANGELOG.md` entry added (or not needed for chore/docs)
- [ ] If NAS-touching: integration tests verified
  - v1: `pytest tests/integration/`
  - v2: `pytest tests/integration_v2/`
