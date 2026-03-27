# Contributing

## Development setup

```bash
git clone https://github.com/by-openclaw/lib-synology-dsm.git
cd lib-synology-dsm
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Standards
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
- All code formatted with `ruff format`
- All tests must pass: `pytest tests/`
- Type hints required on all public functions
- Docstrings required on all public classes and methods

## Adding a new module
1. Create `src/synology_dsm/{module}.py`
2. Add tests in `tests/test_{module}.py`
3. Export from `src/synology_dsm/__init__.py` if appropriate
4. Update README.md

## Session management
Always use `DSMClient` as a context manager — it handles login/logout automatically.
Never store session IDs in state — they are short-lived (30min default).
