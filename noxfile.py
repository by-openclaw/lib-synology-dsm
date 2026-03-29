"""Nox configuration — local multi-version testing without containers.

Usage:
    pip install nox
    nox               # run all sessions
    nox -s tests      # unit tests on all Python versions
    nox -s tests-3.10 # unit tests on Python 3.10 only
    nox -s lint       # lint + type check on 3.10 (minimum supported)
"""

from __future__ import annotations

import nox


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: nox.Session) -> None:
    """Run unit tests on all supported Python versions."""
    session.install("-e", ".[dev]")
    session.run(
        "pytest", "tests/unit/",
        "--cov=src/synology_dsm",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v", "--tb=short",
    )


@nox.session(python="3.10")
def lint(session: nox.Session) -> None:
    """Lint and type check against minimum Python version."""
    session.install("-e", ".[dev]")
    session.run("ruff", "check", "src/", "tests/")
    session.run("ruff", "format", "--check", "src/", "tests/")
    session.run("mypy", "src/synology_dsm/", "--ignore-missing-imports")


@nox.session(python="3.10")
def integration(session: nox.Session) -> None:
    """Run integration tests — requires NAS_HOST / API_USER / API_PASS env vars."""
    session.install("-e", ".[dev]")
    session.run(
        "pytest", "tests/integration/",
        "-m", "integration",
        "-v", "--tb=short",
    )
