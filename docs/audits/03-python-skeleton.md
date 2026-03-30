# Python Skeleton Project Re-Audit

## 1. Progress Confirmed

1. The project still follows a clean `src/` library layout.
2. Modern metadata is still present in `pyproject.toml`.
3. `py.typed` is still present.
4. The developer extra now includes packaging support.
   Evidence:
   `build` and `pygments` were added to `project.optional-dependencies.dev`.
5. Packaging smoke build now works.
   Evidence:
   `python -m build --sdist --wheel` succeeded and produced:
   `synology_dsm-0.9.0.tar.gz`
   `synology_dsm-0.9.0-py3-none-any.whl`.
6. Devcontainer alignment improved.
   Evidence:
   `.devcontainer/devcontainer.json` now uses Python `3.13`.

## 2. Remaining Findings

1. Medium: version/tag consistency is still unresolved.
   Evidence:
   package metadata says `0.9.0`, but local tags stop at `v0.7.0`.
2. Medium: developer docs still partially describe the old container/runtime state.
   Evidence:
   README still says the first build downloads Python `3.12`.
   CONTRIBUTING still says the dev container is Python `3.12`.
   Impact:
   the skeleton is healthier than the docs currently admit.
3. Low: pytest still defaults to unit-only discovery.
   Evidence:
   `testpaths = ["tests/unit"]`.
   Impact:
   acceptable for safety, but still worth documenting clearly as an intentional choice.

## 3. Resolved Findings From Prior Audit

1. Resolved:
   build verification was not first-class.
   It is now first-class enough to validate locally via `.[dev]`.
2. Resolved:
   devcontainer mismatch with current upper bound.
   Container now matches Python `3.13`.
3. Resolved:
   stale Python support badge in README.

## 4. Next Skeleton Tasks

1. Sync README and CONTRIBUTING text with the new Python `3.13` devcontainer.
2. Repair release tag history so packaging metadata and git history tell the same story.
3. Consider adding a dedicated build session to CI if not already proven in remote runs.
