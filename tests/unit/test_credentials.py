"""Unit tests — credential providers."""

import os
from unittest.mock import MagicMock, patch

import pytest

from synology_dsm.credentials import (
    DSMCredentials,
    EnvCredentialProvider,
    VaultCredentialProvider,
    get_credentials,
)


class TestDSMCredentials:
    def test_dataclass_fields(self):
        creds = DSMCredentials(host="nas.local", port=5001, user="admin", password="secret")
        assert creds.host == "nas.local"
        assert creds.port == 5001
        assert creds.user == "admin"
        assert creds.password == "secret"


class TestEnvCredentialProvider:
    def test_get_reads_env_vars(self):
        env = {
            "SYNOLOGY_HOST": "192.168.1.100",
            "SYNOLOGY_PORT": "5001",
            "SYNOLOGY_USER": "dsm-user",
            "SYNOLOGY_PASS": "s3cr3t",
        }
        with patch.dict(os.environ, env, clear=False):
            creds = EnvCredentialProvider(env_file=None).get()
        assert creds.host == "192.168.1.100"
        assert creds.port == 5001
        assert creds.user == "dsm-user"
        assert creds.password == "s3cr3t"

    def test_get_raises_when_host_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="SYNOLOGY_HOST not set"):
                EnvCredentialProvider(env_file=None).get()

    def test_get_default_port_5001(self):
        env = {"SYNOLOGY_HOST": "nas.local", "SYNOLOGY_USER": "u", "SYNOLOGY_PASS": "p"}
        with patch.dict(os.environ, env, clear=False):
            # Remove SYNOLOGY_PORT if set
            os.environ.pop("SYNOLOGY_PORT", None)
            creds = EnvCredentialProvider(env_file=None).get()
        assert creds.port == 5001

    def test_dotenv_loaded_when_file_exists(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("SYNOLOGY_HOST=dotenv-host\nSYNOLOGY_USER=u\nSYNOLOGY_PASS=p\n")
        # Ensure env is clean of SYNOLOGY_HOST
        with patch.dict(os.environ, {}, clear=True):
            try:
                from dotenv import load_dotenv  # noqa: F401

                creds = EnvCredentialProvider(env_file=str(env_file)).get()
                assert creds.host == "dotenv-host"
            except ImportError:
                pytest.skip("python-dotenv not installed")

    def test_missing_dotenv_file_falls_through(self):
        env = {"SYNOLOGY_HOST": "nas.local", "SYNOLOGY_USER": "u", "SYNOLOGY_PASS": "p"}
        with patch.dict(os.environ, env, clear=False):
            creds = EnvCredentialProvider(env_file="/nonexistent/.env").get()
        assert creds.host == "nas.local"

    def test_dotenv_import_error_falls_through(self, tmp_path):
        """If dotenv is installed but load raises ImportError somehow, falls through."""
        env_file = tmp_path / ".env"
        env_file.write_text("SYNOLOGY_HOST=fallback\nSYNOLOGY_USER=u\nSYNOLOGY_PASS=p\n")
        env = {"SYNOLOGY_HOST": "env-host", "SYNOLOGY_USER": "u", "SYNOLOGY_PASS": "p"}
        with patch.dict(os.environ, env, clear=False):
            # Simulate dotenv not importable — provider must still work via raw env
            with patch.dict(__import__("sys").modules, {"dotenv": None}):
                creds = EnvCredentialProvider(env_file=str(env_file)).get()
        # Falls through to raw env — SYNOLOGY_HOST from os.environ
        assert creds.host == "env-host"


class TestVaultCredentialProvider:
    def test_raises_import_error_without_hvac(self):
        import sys

        with patch.dict(sys.modules, {"hvac": None}):
            provider = VaultCredentialProvider(
                vault_addr="https://vault.example.com",
                vault_token="tok",
            )
            with pytest.raises(ImportError, match="hvac not installed"):
                provider.get()

    def test_raises_on_unauthenticated(self):
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_hvac.Client.return_value = mock_client

        with patch.dict(__import__("sys").modules, {"hvac": mock_hvac}):
            provider = VaultCredentialProvider(
                vault_addr="https://vault.example.com",
                vault_token="bad-token",
            )
            with pytest.raises(RuntimeError, match="Vault authentication failed"):
                provider.get()

    def test_reads_secret_from_vault(self):
        mock_hvac = MagicMock()
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {
                "data": {
                    "host": "vault-nas.local",
                    "port": "5001",
                    "user": "vault-user",
                    "password": "vault-pass",
                }
            }
        }
        mock_hvac.Client.return_value = mock_client

        with patch.dict(__import__("sys").modules, {"hvac": mock_hvac}):
            provider = VaultCredentialProvider(
                vault_addr="https://vault.example.com",
                vault_token="valid-token",
                secret_path="secret/data/synology/nas01",
            )
            creds = provider.get()

        assert creds.host == "vault-nas.local"
        assert creds.user == "vault-user"
        assert creds.password == "vault-pass"
        assert creds.port == 5001


class TestGetCredentials:
    def test_uses_env_when_vault_not_configured(self):
        env = {
            "SYNOLOGY_HOST": "env-nas",
            "SYNOLOGY_USER": "u",
            "SYNOLOGY_PASS": "p",
        }
        clean = dict.fromkeys(["VAULT_ADDR", "VAULT_TOKEN"], "")
        with patch.dict(os.environ, {**env, **clean}, clear=False):
            os.environ.pop("VAULT_ADDR", None)
            os.environ.pop("VAULT_TOKEN", None)
            creds = get_credentials(env_file=None)
        assert creds.host == "env-nas"

    def test_falls_back_to_env_when_vault_fails(self):
        env = {
            "VAULT_ADDR": "https://vault.example.com",
            "VAULT_TOKEN": "tok",
            "SYNOLOGY_HOST": "fallback-nas",
            "SYNOLOGY_USER": "u",
            "SYNOLOGY_PASS": "p",
        }
        with (
            patch.dict(os.environ, env, clear=False),
            patch(
                "synology_dsm.credentials.VaultCredentialProvider.get",
                side_effect=Exception("vault down"),
            ),
        ):
            creds = get_credentials(env_file=None)
        assert creds.host == "fallback-nas"
