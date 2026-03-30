# Security Re-Audit

## 1. Current Positive State

1. Security tooling remains healthy.
   Evidence:
   Bandit found no medium/high issues.
   `pip-audit` found no known vulnerabilities.
2. Dependency attack surface remains very small.
   Evidence:
   runtime dependencies are still empty.
3. Security policy and hardening docs still exist and remain useful.
4. CI still runs a dedicated security job.

## 2. Remaining Findings

1. High: TLS verification is still insecure by default.
   Evidence:
   `DSMClient.__init__` still defaults to `verify_ssl=False`.
   Impact:
   insecure transport remains the default user path for the main client API.
2. High: insecure TLS usage is still normalized in docs/examples.
   Evidence:
   README examples still use `verify_ssl=False`.
   CONTRIBUTING still shows `verify_ssl=False`.
   Impact:
   documentation still teaches the insecure path first.
3. Medium: broad exception swallowing still exists in a few paths.
   Evidence:
   `client.py` still suppresses all logout errors.
   Impact:
   operational visibility is weaker than it should be during auth/session cleanup.
4. Medium: secret scanning exclusions are unchanged.
   Evidence:
   `.pre-commit-config.yaml` still excludes integration shell scripts and `.env.example`.
   Impact:
   the highest-risk manual testing assets still bypass local secret scanning.
5. Medium: GitHub Actions are still pinned by moving version tags rather than immutable SHAs.
6. Medium: Vault authentication is still token-first only.

## 3. Resolved Findings From Prior Audit

1. Resolved:
   broken Codecov dependency is gone.
   This removes one silent external-service failure mode from CI.
2. Resolved:
   build tooling is now installed in the normal dev extra.
   That improves contributor verification and reduces packaging surprises.

## 4. Recommendation Order

1. First:
   change secure TLS to the default path in code and docs.
2. Second:
   tighten secret-scanning coverage.
3. Third:
   reduce blanket exception swallowing or add controlled logging.
4. Fourth:
   consider stronger GitHub Actions pinning and a better Vault auth path.
