"""
Credential providers for lib-synology-dsm.

Supports three sources (in priority order when using auto-detect):
  1. HashiCorp Vault (via hvac) — production
  2. Environment variables / .env file — development
  3. Explicit values passed to DSMClient — fallback / testing

Usage:
    # Auto-detect (Vault if configured, else env)
    from synology_dsm.credentials import get_credentials
    creds = get_credentials()
    with DSMClient(creds.host, port=creds.port) as client:
        client.login(creds.user, creds.password)

    # Explicit Vault
    from synology_dsm.credentials import VaultCredentialProvider
    creds = VaultCredentialProvider(
        vault_addr="https://vault.by-systems.arpa",
        vault_token="...",
        secret_path="secret/data/synology/nas01"
    ).get()

    # .env / environment
    from synology_dsm.credentials import EnvCredentialProvider
    creds = EnvCredentialProvider().get()
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DSMCredentials:
    """Resolved credentials for a DSM connection."""

    host: str
    port: int
    user: str
    password: str


class EnvCredentialProvider:
    """Load credentials from environment variables or .env file.

    Reads: SYNOLOGY_HOST, SYNOLOGY_PORT, SYNOLOGY_USER, SYNOLOGY_PASS
    Optionally loads a .env file if python-dotenv is installed.
    """

    def __init__(self, env_file: str | None = ".env") -> None:
        """Initialise the provider.

        Args:
            env_file: Path to .env file. Pass None to skip dotenv loading.
        """
        self._env_file = env_file

    def _load_dotenv(self) -> None:
        """Attempt to load the .env file if present and python-dotenv is installed.

        Silently skips if the file does not exist or dotenv is not installed.
        Uses override=False so existing environment variables take precedence.
        """
        if self._env_file and os.path.exists(self._env_file):
            try:
                from dotenv import load_dotenv

                load_dotenv(self._env_file, override=False)
            except ImportError:
                pass  # python-dotenv not installed; fall through to raw env

    def get(self) -> DSMCredentials:
        """Resolve and return credentials."""
        self._load_dotenv()
        host = os.environ.get("SYNOLOGY_HOST")
        if not host:
            raise RuntimeError(
                "SYNOLOGY_HOST not set. Copy .env.example to .env and fill in values."
            )
        return DSMCredentials(
            host=host,
            port=int(os.environ.get("SYNOLOGY_PORT", "5001")),
            user=os.environ.get("SYNOLOGY_USER", ""),
            password=os.environ.get("SYNOLOGY_PASS", ""),
        )


class VaultCredentialProvider:
    """Load credentials from HashiCorp Vault (KV v2) using token authentication.

    Requires: pip install hvac  (or: pip install 'lib-synology-dsm[vault]')
    Secret must contain keys: host, port (optional), user, password

    Example Vault secret path: secret/data/synology/nas01

    Authentication:
        Token auth only — pass ``vault_token`` or set ``VAULT_TOKEN`` env var.

    Not yet implemented:
        AppRole authentication — tracked in GitHub issue #7.
        Use token auth until Vault is deployed (Phase 2).
    """

    def __init__(
        self,
        vault_addr: str,
        vault_token: str | None = None,
        secret_path: str = "secret/data/synology/nas01",
    ) -> None:
        """Initialise the provider.

        Args:
            vault_addr:   Vault server URL (e.g. ``https://vault.example.com``).
            vault_token:  Vault token. Falls back to VAULT_TOKEN env var.
            secret_path:  KV v2 path to the secret.
        """
        self._vault_addr = vault_addr
        self._vault_token = vault_token or os.environ.get("VAULT_TOKEN")
        self._secret_path = secret_path

    def get(self) -> DSMCredentials:
        """Fetch credentials from Vault and return."""
        try:
            import hvac
        except ImportError as e:
            raise ImportError(
                "hvac not installed. Run: pip install 'lib-synology-dsm[vault]'"
            ) from e

        client = hvac.Client(url=self._vault_addr, token=self._vault_token)
        if not client.is_authenticated():
            raise RuntimeError(f"Vault authentication failed at {self._vault_addr}")

        # Parse path for KV v2: split mount and key
        parts = self._secret_path.split("/data/", 1)
        mount = parts[0] if len(parts) > 1 else "secret"
        key = parts[1] if len(parts) > 1 else self._secret_path

        secret = client.secrets.kv.v2.read_secret_version(path=key, mount_point=mount)
        data = secret["data"]["data"]

        return DSMCredentials(
            host=data["host"],
            port=int(data.get("port", 5001)),
            user=data["user"],
            password=data["password"],
        )


def get_credentials(env_file: str | None = ".env") -> DSMCredentials:
    """Auto-detect credential source.

    Priority:
    1. Vault — if VAULT_ADDR + VAULT_TOKEN env vars are set
    2. Environment / .env file — fallback

    For production, set VAULT_ADDR and VAULT_TOKEN and store the secret at
    secret/data/synology/nas01 in your Vault instance.
    """
    vault_addr = os.environ.get("VAULT_ADDR")
    vault_token = os.environ.get("VAULT_TOKEN")

    if vault_addr and vault_token:
        try:
            return VaultCredentialProvider(
                vault_addr=vault_addr,
                vault_token=vault_token,
            ).get()
        except Exception as exc:
            import warnings

            warnings.warn(
                f"Vault credential provider failed ({exc!r}), falling back to environment variables.",
                RuntimeWarning,
                stacklevel=2,
            )

    return EnvCredentialProvider(env_file=env_file).get()
