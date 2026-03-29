# Security Audit

## 1. Healthy Points

1. Security documentation exists.
   Evidence: `SECURITY.md`, `docs/hardening.md`, `docs/credentials.md`.
2. Secret detection exists in local workflow.
   Evidence: `.pre-commit-config.yaml` uses `detect-secrets`.
3. Static security scan configuration exists in CI.
   Evidence: `.github/workflows/ci.yml` runs Bandit and pip-audit.
4. Dependency exposure is small.
   Evidence: runtime `dependencies = []` in `pyproject.toml`.
5. Audit results during this review were clean at the tool level.
   Evidence:
   `.venv/bin/bandit -r src/ -ll -ii` -> no medium/high findings.
   `.venv/bin/pip-audit --skip-editable` -> no known vulnerabilities found.

## 2. Findings

1. High: TLS certificate verification is insecure by default.
   Evidence:
   `DSMClient.__init__` defaults to `verify_ssl=False`.
   `src/synology_dsm/client.py` builds an unverified SSL context when HTTPS is used with default settings.
   Impact:
   users are guided toward a man-in-the-middle-prone configuration by default.
2. High: insecure transport usage is normalized in examples and tests.
   Evidence:
   `README.md` quick start uses `verify_ssl=False`.
   `CONTRIBUTING.md` session example uses `verify_ssl=False`.
   integration fixtures also use `verify_ssl=False`.
   Impact:
   the project’s safest path is not the default mental model presented to users or contributors.
3. Medium: broad exception swallowing hides security-relevant operational failures.
   Evidence:
   `client.py` swallows all exceptions in `logout()`.
   `groups.py` swallows all exceptions in membership fallback logic.
   `filestation.py` swallows all exceptions in `_file_exists()`.
   Impact:
   auth, permission, and network failures can be masked as cleanup noise or false no-op behavior.
4. Medium: secret scanning excludes integration shell scripts and `.env.example`.
   Evidence:
   `.pre-commit-config.yaml` excludes `tests/integration/.*\.sh` and `.env.example`.
   Impact:
   the repo allows a category of credential-shaped strings to bypass local scanning.
5. Medium: GitHub Actions are version-pinned by major tag, not immutable commit SHA.
   Evidence:
   workflow files use `actions/checkout@v6`, `setup-python@v6`, `codecov-action@v6`, `release-please-action@v4`.
   Impact:
   this is common practice, but it is weaker than full SHA pinning for supply-chain hardening.
6. Medium: Vault support relies on token auth only.
   Evidence:
   `VaultCredentialProvider` documentation explicitly says token auth only; AppRole is not implemented.
   Impact:
   long-lived or manually managed Vault tokens are usually weaker operationally than workload identity or short-lived auth methods.
7. Low: environment credential validation is incomplete.
   Evidence:
   `EnvCredentialProvider.get()` hard-fails on missing host but allows empty user and password.
   Impact:
   misconfiguration is detected late, often during login rather than at credential resolution time.

## 3. Recommendations

1. Change `verify_ssl` to default `True`.
   If lab/self-signed support is necessary, keep `False` as an explicit override with strong warnings.
2. Update documentation examples to show the secure path first.
   Present insecure TLS only in a dedicated self-signed troubleshooting section.
3. Replace blanket `except Exception` blocks with narrower exceptions and optional debug logging.
4. Revisit pre-commit exclusions.
   If shell scripts must stay excluded, add a separate shell-oriented secret scan in CI.
5. Pin GitHub Actions by full commit SHA for stronger provenance.
6. Add AppRole, OIDC, or another non-token-first Vault authentication path.
7. Validate `SYNOLOGY_USER` and `SYNOLOGY_PASS` eagerly in `EnvCredentialProvider.get()`.

## 4. Risk Prioritization

1. First fix:
   insecure TLS default and documentation pattern.
2. Second fix:
   visibility around swallowed exceptions.
3. Third fix:
   secret-scanning scope and CI supply-chain hardening.
