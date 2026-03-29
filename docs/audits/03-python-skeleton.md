# Python Skeleton Project Audit

## 1. Healthy Points

1. The repository follows the `src/` layout correctly.
   Evidence: package code lives under `src/synology_dsm`.
2. Packaging metadata is modern and mostly complete.
   Evidence:
   `pyproject.toml` uses PEP 517/518 build settings and PEP 621 project metadata.
3. Typed package signaling exists.
   Evidence: `src/synology_dsm/py.typed`.
4. The library is intentionally lightweight.
   Evidence: no runtime dependencies are declared.
5. Multi-version execution intent exists.
   Evidence:
   `requires-python = ">=3.10"`,
   CI matrix includes `3.10`, `3.11`, `3.12`, `3.13`,
   `noxfile.py` also targets those versions.

## 2. Findings

1. High: packaging/build verification is not first-class in the developer environment.
   Evidence:
   `.venv/bin/python -m build --sdist --wheel` failed because `build` is not installed.
   `.[dev]` does not include `build` or a packaging smoke test.
   Impact:
   the repository is structured like a distributable library, but buildability is not continuously exercised in the standard dev toolchain.
2. Medium: version signaling is inconsistent across repository layers.
   Evidence:
   project metadata says `0.9.0`, but local tags stop at `v0.7.0`.
   Impact:
   package consumers and maintainers may disagree on what has actually been released.
3. Medium: developer environment is pinned to Python 3.12 while support starts at 3.10 and CI already tests 3.13.
   Evidence:
   `.devcontainer/devcontainer.json` uses `mcr.microsoft.com/devcontainers/python:3.12`.
   Impact:
   the default local environment does not match either the minimum supported version or the newest tested version.
4. Medium: pytest default discovery excludes integration tests by design.
   Evidence:
   `pyproject.toml` sets `testpaths = ["tests/unit"]`.
   Impact:
   this is acceptable for safety, but it means integration confidence depends on explicit human action and documentation accuracy.
5. Low: the README Python support badge is stale.
   Evidence:
   README badge shows `3.10 | 3.11 | 3.12` while CI includes `3.13`.
   Impact:
   public compatibility signaling is behind actual CI claims.

## 3. Recommendations

1. Add `build` to `dev` dependencies or create a dedicated `nox`/CI packaging session.
2. Add a wheel/sdist smoke build to CI.
3. Decide whether the dev container should target:
   minimum supported Python,
   current default development Python,
   or a multi-version workflow via `nox`.
4. Keep the README compatibility badge synchronized with CI and classifiers.
5. Treat tag/version consistency as part of packaging health, not only git process health.

## 4. Suggested Definition Of Done

1. `pip install -e ".[dev]"` gives all core contributor tools, including packaging validation.
2. CI proves:
   lint,
   types,
   tests,
   build.
3. README, classifiers, CI matrix, and devcontainer tell the same Python support story.
