# Credential Providers

`lib-synology-dsm` supports three credential sources, in priority order when using auto-detect:

1. **HashiCorp Vault** — production environments
2. **Environment variables / `.env` file** — development and CI
3. **Explicit values** — fallback / testing (passed directly to `DSMClient.login()`)

> **Integration tests** use `infra-synology-nas.json` (KV `fields` block) directly via `conftest.py` —
> not `EnvCredentialProvider`. See [CONTRIBUTING.md](../CONTRIBUTING.md#credentials--always-first).

---

## Auto-detect (recommended)

```python
from synology_dsm.credentials import get_credentials
from synology_dsm import DSMClient

creds = get_credentials()
with DSMClient(creds.host, port=creds.port) as client:
    client.login(creds.user, creds.password)
```

`get_credentials()` will:
1. Check for `VAULT_ADDR` + `VAULT_TOKEN` environment variables → use Vault if both are set
2. Fall back to `EnvCredentialProvider` (reads `.env` or environment)

---

## Provider: Environment / `.env` file

Suitable for local development and CI pipelines.

```bash
cp .env.example .env
# Edit .env with your values
```

```python
from synology_dsm.credentials import EnvCredentialProvider

creds = EnvCredentialProvider().get()
```

**Environment variables read:**

| Variable | Required | Default | Description |
|---|---|---|---|
| `SYNOLOGY_HOST` | ✅ | — | NAS IP or hostname |
| `SYNOLOGY_PORT` | ❌ | `5001` | HTTPS port |
| `SYNOLOGY_USER` | ❌ | `""` | API user |
| `SYNOLOGY_PASS` | ❌ | `""` | API password |

`python-dotenv` is used automatically if installed. If not installed, raw environment variables are used.

Install with: `pip install 'synology-dsm[dev]'`

---

## Provider: HashiCorp Vault (KV v2)

Suitable for production. Requires `hvac`.

```bash
pip install 'synology-dsm[vault]'
export VAULT_ADDR=https://vault.by-systems.arpa
export VAULT_TOKEN=s.xxxxxxxxxxxxxxxx
```

```python
from synology_dsm.credentials import VaultCredentialProvider

creds = VaultCredentialProvider(
    vault_addr="https://vault.by-systems.arpa",
    vault_token="s.xxxxxxxxxxxxxxxx",  # or set VAULT_TOKEN env var
    secret_path="secret/data/synology/nas01",
).get()
```

**Vault secret structure (KV v2):**

```json
{
  "host": "your-nas-host",
  "port": 5001,
  "user": "svc-rune-dsm",
  "password": "..."
}
```

Write the secret:
```bash
vault kv put secret/synology/nas01 \
  host=your-nas-host \
  port=5001 \
  user=svc-rune-dsm \
  password=...
```

---

## Provider: Explicit (testing only)

Pass credentials directly. Never use in production.

```python
from synology_dsm import DSMClient

with DSMClient("your-nas-host") as client:
    client.login("svc-rune-dsm", "password")
```

---

## Security notes

- `.env` is excluded from git via `.gitignore`
- Never commit credentials — use `.env.example` as a template
- For production, prefer Vault over environment variables
- Rotate credentials via Vault leases or DSM user management
