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
- [ ] `mypy src/synology_dsm/ --ignore-missing-imports` passes
- [ ] Unit tests pass: `pytest tests/unit/ --cov=src/synology_dsm --cov-fail-under=80`
- [ ] Coverage gate passes (≥80%)
- [ ] New behaviour has unit tests
- [ ] Public API changes have docstrings (PEP 257)
- [ ] `CHANGELOG.md` entry added (or not needed for chore/docs)
- [ ] If NAS-touching: integration tests verified (`pytest tests/integration/ -m integration`)
