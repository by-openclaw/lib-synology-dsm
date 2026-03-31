# 2FA / OTP API Compatibility Research — DSM 7.1.1

> **Purpose:** Verify whether SYNO.API.Auth v6 supports OTP before enabling 2FA on NAS accounts.
> **Decision rule:** Do NOT enable 2FA until lib-synology-dsm v2 supports it. See conclusion.

---

## Finding: SYNO.API.Auth v6 supports `otp_code`

### Evidence 1 — N4S4/synology-api (authoritative reference implementation)

Source: `synology_api/auth.py` — login() method:

```python
params_enc = {
    'account': self._username,
    'otp_code': '',          # ← always included in payload
    ...
}
# Then:
if self._otp_code:
    params['otp_code'] = self._otp_code    # ← overwritten if 2FA code provided
```

N4S4 also supports:
- `device_id` — trusted device token (skip 2FA after first login)
- `device_name` — name for device registration

### Evidence 2 — Synology DSM Login Web API Guide (official, Apr 2023)

API: `SYNO.API.Auth` method `login`

Relevant parameters:
| Parameter | Type | Description |
|---|---|---|
| `otp_code` | string | OTP code from authenticator app (when 2FA enabled) |
| `device_id` | string | Device token — if provided and valid, skips 2FA prompt |
| `device_name` | string | Name to register device as trusted |

### Evidence 3 — Our v2 client (`src/synology_dsm_v2/client.py`)

Current `login()` does **not** include `otp_code` in the request body:

```python
data = self._post(..., {
    "api": "SYNO.API.Auth",
    "version": "6",
    "method": "login",
    "account": account,
    "passwd": password,
    "session": session,
    "enable_syno_token": "yes",
    "format": "sid",
    # ← otp_code NOT present
})
```

If 2FA is enabled and `otp_code` is omitted → DSM returns error code `403` (OTP required).

---

## DSM error code for 2FA

| Code | Meaning |
|---|---|
| 403 | One-time password not specified |
| 404 | One-time password authentication failed |
| 406 | Enforce 2-step verification is enforced |

---

## Conclusion

| | |
|---|---|
| **API supports it?** | ✅ Yes — `otp_code` parameter documented and proven in reference impl |
| **Our v2 client supports it?** | ❌ No — `login()` does not accept or pass `otp_code` |
| **Safe to enable 2FA now?** | ❌ No — would break all lib automation immediately |

---

## Required work before enabling 2FA

Update `DSMClient.login()` to accept optional `otp_code` and `device_id`:

```python
def login(
    self,
    account: str,
    password: str,
    session: str = "DSM",
    otp_code: str | None = None,
    device_id: str | None = None,
    device_name: str | None = None,
) -> str:
    ...
    payload = {
        "api": "SYNO.API.Auth",
        "version": "6",
        "method": "login",
        "account": account,
        "passwd": password,
        "session": session,
        "enable_syno_token": "yes",
        "format": "sid",
    }
    if otp_code:
        payload["otp_code"] = otp_code
    if device_id and device_name:
        payload["device_id"] = device_id
        payload["device_name"] = device_name
```

**Recommended flow for service accounts:**
1. Add `otp_code` + `device_id` support to `DSMClient.login()`
2. First login with `otp_code` + `device_name="rune-automation"` → DSM returns a `device_id`
3. Store `device_id` in `infra-synology-nas.json` secrets
4. Subsequent logins pass only `device_id` → no OTP needed (trusted device)
5. Enable 2FA only after step 1-4 are tested and working

**This is a lib enhancement, not a blocker today.** Track as new issue.

---

## Recommendation to @yboujraf

**Do not enable 2FA yet.** Enable it only after:
1. lib v2 `login()` supports `otp_code` + `device_id`
2. Integration test covers 2FA login flow
3. `device_id` stored in secrets, automation uses device token (no live OTP)

*Generated: 2026-03-31 | Owner: Rune Agent | Review: Opus before enabling 2FA*
