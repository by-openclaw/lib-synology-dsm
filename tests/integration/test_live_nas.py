#!/usr/bin/env python3
"""
Live NAS integration test — lib-synology-dsm API validation
Run manually: python3 tests/integration/test_live_nas.py

Requires: NAS reachable at 10.6.224.6:5001
Credentials: rune-api (admin) / rune-audit (read-only)

Uses urllib only — no httpx dependency.
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.parse
import urllib.request
from typing import Any

# ── Config ─────────────────────────────────────────────────────────────────
NAS_HOST = "10.6.224.6"
NAS_PORT = 5001
BASE_URL = f"https://{NAS_HOST}:{NAS_PORT}/webapi/entry.cgi"

ADMIN_USER = "rune-api"
ADMIN_PASS = "YOUR_PASSWORD"
AUDIT_USER = "rune-audit"
AUDIT_PASS = "YOUR_PASSWORD"

TEST_USER = "rune-test-tmp"
TEST_USER_PASS = "YOUR_PASSWORDtest!"
TEST_GROUP = "rune-test-group"
TEST_SHARE = "rune-test-share"

# ── Helpers ────────────────────────────────────────────────────────────────
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

PASS = "✅"
WARN = "⚠️"
FAIL = "❌"

_results: list[tuple[str, str, str]] = []  # (status, name, detail)


def post(payload: dict[str, Any], token: str = "") -> dict:
    """POST to entry.cgi, return parsed JSON.

    Always sends X-SYNO-TOKEN header when available — required for all write
    operations on DSM 7.x (share create/delete, group set, user create/delete).
    """
    data = urllib.parse.urlencode(payload).encode()
    headers = {"X-SYNO-TOKEN": token} if token else {}
    req = urllib.request.Request(BASE_URL, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, context=_ctx, timeout=15) as resp:
        return json.loads(resp.read())


_synotoken: str = ""  # module-level token set on admin login


def login(account: str, password: str, session: str = "DSM") -> str | None:
    """Login and return SID, or None on failure. Sets module _synotoken on success."""
    global _synotoken
    resp = post(
        {
            "api": "SYNO.API.Auth",
            "version": "7",
            "method": "login",
            "account": account,
            "passwd": password,
            "session": session,
            "format": "sid",
            "enable_syno_token": "yes",  # required for write ops on DSM 7.x
        }
    )
    if resp.get("success"):
        _synotoken = resp["data"].get("synotoken", "")
        return resp["data"]["sid"]
    return None


def logout(sid: str) -> bool:
    resp = post(
        {
            "api": "SYNO.API.Auth",
            "version": "1",
            "method": "logout",
            "_sid": sid,
        }
    )
    return resp.get("success", False)


def api(sid: str, api_name: str, method: str, version: int = 1, **params) -> dict:
    payload = {
        "api": api_name,
        "version": str(version),
        "method": method,
        "_sid": sid,
        **params,
    }
    return post(payload, token=_synotoken)


def record(status: str, name: str, detail: str = "") -> None:
    _results.append((status, name, detail))
    icon = status
    msg = f"  {icon}  {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


# ── Tests ──────────────────────────────────────────────────────────────────


def test_auth_admin() -> str | None:
    section("1. Auth v7 — rune-api (admin)")
    sid = login(ADMIN_USER, ADMIN_PASS)
    if sid:
        record(PASS, "rune-api login", f"sid={sid[:12]}…")
        ok = logout(sid)
        if ok:
            record(PASS, "rune-api logout")
        else:
            record(WARN, "rune-api logout", "success=false (session may have auto-expired)")
        # Re-login for continued use
        sid = login(ADMIN_USER, ADMIN_PASS)
        if sid:
            record(PASS, "rune-api re-login (for subsequent tests)", f"sid={sid[:12]}…")
        return sid
    else:
        record(FAIL, "rune-api login", "Authentication failed")
        return None


def test_auth_audit() -> str | None:
    section("2. Auth v7 — rune-audit (read-only)")
    sid = login(AUDIT_USER, AUDIT_PASS)
    if sid:
        record(PASS, "rune-audit login", f"sid={sid[:12]}…")
        ok = logout(sid)
        if ok:
            record(PASS, "rune-audit logout")
        else:
            record(WARN, "rune-audit logout")
        return sid
    else:
        # Error 402 = account disabled in DSM. Check DSM Control Panel > User if rune-audit is disabled.
        # Error 400 = wrong password, 403 = 2FA required.
        record(
            WARN,
            "rune-audit login",
            "Failed — likely error 402 (account disabled). "
            "Enable rune-audit in DSM Control Panel → User & Group, or reset password.",
        )
        return None


def test_users(sid: str) -> None:
    section("3. SYNO.Core.User — list / create / delete")
    if not sid:
        record(WARN, "user tests skipped", "no admin session")
        return

    # List users
    resp = api(sid, "SYNO.Core.User", "list", version=1)
    if resp.get("success") is not False and "users" in resp.get("data", resp):
        data = resp.get("data", resp)
        users = data.get("users", [])
        record(PASS, "SYNO.Core.User list", f"{len(users)} users")
    else:
        # success may be implicit when data returned directly
        if isinstance(resp, dict) and "users" in resp:
            record(PASS, "SYNO.Core.User list", f"{len(resp['users'])} users")
        else:
            record(FAIL, "SYNO.Core.User list", str(resp)[:120])
            return

    # Create test user
    resp = api(
        sid,
        "SYNO.Core.User",
        "create",
        version=1,
        name=TEST_USER,
        password=TEST_USER_PASS,
        email="",
        description="Rune integration test — auto-deleted",
    )
    raw = resp if not isinstance(resp, dict) else resp
    if raw.get("success", True) is not False:
        record(PASS, f"SYNO.Core.User create ({TEST_USER})")
    else:
        err = raw.get("error", {})
        record(FAIL, f"SYNO.Core.User create ({TEST_USER})", f"error={err}")
        return

    # Delete test user — DSM requires JSON array
    resp = api(sid, "SYNO.Core.User", "delete", version=1, name=json.dumps([TEST_USER]))
    if resp.get("success", True) is not False:
        record(PASS, f"SYNO.Core.User delete ({TEST_USER})")
    else:
        record(FAIL, f"SYNO.Core.User delete ({TEST_USER})", str(resp)[:120])


def _api_raw(sid: str, api_name: str, method: str, version: int = 1, **params) -> dict:
    """Return the full raw response including 'success' key. Always sends X-SYNO-TOKEN."""
    payload = {
        "api": api_name,
        "version": str(version),
        "method": method,
        "_sid": sid,
        **params,
    }
    return post(payload, token=_synotoken)


def test_groups(sid: str) -> None:
    section("4. SYNO.Core.Group — list / create / members / delete")
    if not sid:
        record(WARN, "group tests skipped", "no admin session")
        return

    # List groups
    resp = _api_raw(sid, "SYNO.Core.Group", "list", version=1)
    if resp.get("success"):
        groups = resp.get("data", {}).get("groups", [])
        record(PASS, "SYNO.Core.Group list", f"{len(groups)} groups")
    else:
        record(FAIL, "SYNO.Core.Group list", str(resp)[:120])
        return

    # Create group
    resp = _api_raw(
        sid,
        "SYNO.Core.Group",
        "create",
        version=1,
        name=TEST_GROUP,
        description="Rune integration test — auto-deleted",
    )
    if resp.get("success"):
        record(PASS, f"SYNO.Core.Group create ({TEST_GROUP})")
    else:
        err = resp.get("error", {})
        record(FAIL, f"SYNO.Core.Group create ({TEST_GROUP})", f"error={err}")
        # Group might already exist — try to clean up anyway
        _api_raw(sid, "SYNO.Core.Group", "delete", version=1, name=json.dumps([TEST_GROUP]))
        record(WARN, "SYNO.Core.Group delete (cleanup attempt after create fail)")
        return

    # Add member — correct method on DS1513+ DSM 7.x: Group.set with members=
    # (member_set / add_member return error 103 — invalid param on this hardware)
    resp = _api_raw(
        sid,
        "SYNO.Core.Group",
        "set",
        version=1,
        name=TEST_GROUP,
        members=json.dumps([AUDIT_USER]),
        description="",
    )
    if resp.get("success"):
        record(PASS, f"SYNO.Core.Group set members ([{AUDIT_USER}] → {TEST_GROUP})")

    # List members
    resp = _api_raw(sid, "SYNO.Core.Group", "member_list", version=1, name=TEST_GROUP)
    if resp.get("success"):
        members = resp.get("data", {}).get("users", [])
        record(PASS, f"SYNO.Core.Group list_members ({TEST_GROUP})", f"{len(members)} members")
    else:
        # Try get method
        resp2 = _api_raw(sid, "SYNO.Core.Group", "get", version=1, name=TEST_GROUP)
        if resp2.get("success"):
            members = resp2.get("data", {}).get("members", resp2.get("data", {}).get("users", []))
            record(
                PASS,
                f"SYNO.Core.Group get/members ({TEST_GROUP})",
                f"via get: {len(members)} members",
            )
        else:
            record(
                WARN,
                "SYNO.Core.Group list_members",
                f"member_list: {resp.get('error')}, get: {resp2.get('error')}",
            )

    # Remove member — same pattern: Group.set with empty members list
    resp = _api_raw(
        sid,
        "SYNO.Core.Group",
        "set",
        version=1,
        name=TEST_GROUP,
        members=json.dumps([]),
        description="",
    )
    if resp.get("success"):
        record(PASS, f"SYNO.Core.Group clear members ({TEST_GROUP})")
    else:
        record(WARN, "SYNO.Core.Group clear members", str(resp.get("error", ""))[:80])

    # Delete group — JSON array like users
    resp = _api_raw(sid, "SYNO.Core.Group", "delete", version=1, name=json.dumps([TEST_GROUP]))
    if resp.get("success"):
        record(PASS, f"SYNO.Core.Group delete ({TEST_GROUP})")
    else:
        record(FAIL, f"SYNO.Core.Group delete ({TEST_GROUP})", str(resp.get("error", ""))[:80])


def test_shares(sid: str) -> None:
    section("5 & 6. SYNO.Core.Share — list / create / NFS / delete")
    if not sid:
        record(WARN, "share tests skipped", "no admin session")
        return

    # List shares
    resp = _api_raw(
        sid,
        "SYNO.Core.Share",
        "list",
        version=1,
        additional=json.dumps(["share_quota", "valid_users"]),
    )
    if resp.get("success"):
        shares = resp.get("data", {}).get("shares", [])
        record(PASS, "SYNO.Core.Share list", f"{len(shares)} shares")
    else:
        record(FAIL, "SYNO.Core.Share list", str(resp.get("error", ""))[:120])

    # Create share — must use shareinfo JSON object (not flat params).
    # Flat params (vol_path, desc) return 403 regardless of permissions.
    # Confirmed via browser DevTools on DSM WebUI.
    shareinfo = json.dumps(
        {
            "name": TEST_SHARE,
            "vol_path": "/volume1",
            "desc": "Rune integration test — auto-deleted",
            "name_org": "",
        }
    )
    resp = _api_raw(
        sid,
        "SYNO.Core.Share",
        "create",
        version=1,
        name=TEST_SHARE,
        shareinfo=shareinfo,
    )
    if resp.get("success"):
        record(PASS, f"SYNO.Core.Share create ({TEST_SHARE})")

        # Set NFS permission — correct API on DS1513+ DSM 7.x:
        # SYNO.Core.FileServ.NFS.SharePrivilege.save (not SYNO.Core.Share.NFS which returns 102)
        nfs_rule = json.dumps(
            [
                {
                    "client": "10.6.224.0/20",
                    "privilege": "rw",
                    "root_squash": "root",
                    "async": True,
                    "insecure": False,
                    "crossmnt": False,
                    "security_flavor": {
                        "sys": True,
                        "kerberos": False,
                        "kerberos_integrity": False,
                        "kerberos_privacy": False,
                    },
                }
            ]
        )
        resp_nfs = _api_raw(
            sid,
            "SYNO.Core.FileServ.NFS.SharePrivilege",
            "save",
            version=1,
            share_name=TEST_SHARE,
            rule=nfs_rule,
        )
        if resp_nfs.get("success"):
            record(PASS, f"NFS SharePrivilege save ({TEST_SHARE} → 10.6.224.0/20 rw)")
        else:
            record(WARN, "NFS SharePrivilege save", str(resp_nfs.get("error", ""))[:80])

        # Delete share
        resp_del = _api_raw(sid, "SYNO.Core.Share", "delete", version=1, name=TEST_SHARE)
        if resp_del.get("success"):
            record(PASS, f"SYNO.Core.Share delete ({TEST_SHARE})")
        else:
            record(
                FAIL, f"SYNO.Core.Share delete ({TEST_SHARE})", str(resp_del.get("error", ""))[:80]
            )
    else:
        err_code = resp.get("error", {}).get("code", "?")
        if err_code == 403 or str(err_code) == "403":
            record(
                WARN,
                f"SYNO.Core.Share create ({TEST_SHARE})",
                "HTTP 403 — rune-api lacks administrator privilege for share creation",
            )
        else:
            record(
                WARN, f"SYNO.Core.Share create ({TEST_SHARE})", f"error={resp.get('error', resp)}"
            )
        record(WARN, "SYNO.Core.Share.NFS set — skipped (create failed)")
        record(WARN, f"SYNO.Core.Share delete ({TEST_SHARE}) — skipped (create failed)")


def test_filestation(sid: str) -> None:
    section("7. SYNO.FileStation.List — list root (read-only)")
    if not sid:
        record(WARN, "FileStation tests skipped", "no admin session")
        return

    resp = _api_raw(sid, "SYNO.FileStation.List", "list_share", version=2)
    if resp.get("success"):
        shares = resp.get("data", {}).get("shares", [])
        record(PASS, "SYNO.FileStation.List list_share", f"{len(shares)} shares visible")
    else:
        record(FAIL, "SYNO.FileStation.List list_share", str(resp.get("error", ""))[:120])

    # Also test list (files in /)
    resp2 = _api_raw(sid, "SYNO.FileStation.List", "list", version=2, folder_path="/")
    if resp2.get("success"):
        files = resp2.get("data", {}).get("files", [])
        record(PASS, "SYNO.FileStation.List list /", f"{len(files)} entries")
    else:
        record(WARN, "SYNO.FileStation.List list /", str(resp2.get("error", ""))[:80])


def cleanup(sid: str) -> None:
    """Ensure all test artifacts are removed."""
    section("Cleanup — removing any leftover test artifacts")
    if not sid:
        return

    # Clean test user
    r = _api_raw(sid, "SYNO.Core.User", "delete", version=1, name=json.dumps([TEST_USER]))
    if r.get("success"):
        record(WARN, f"cleanup: deleted leftover user {TEST_USER}")

    # Clean test group
    r = _api_raw(sid, "SYNO.Core.Group", "delete", version=1, name=json.dumps([TEST_GROUP]))
    if r.get("success"):
        record(WARN, f"cleanup: deleted leftover group {TEST_GROUP}")

    # Clean test share
    r = _api_raw(sid, "SYNO.Core.Share", "delete", version=1, name=TEST_SHARE)
    if r.get("success"):
        record(WARN, f"cleanup: deleted leftover share {TEST_SHARE}")


def summary() -> None:
    section("Summary")
    passed = sum(1 for s, _, _ in _results if s == PASS)
    warned = sum(1 for s, _, _ in _results if s == WARN)
    failed = sum(1 for s, _, _ in _results if s == FAIL)
    total = len(_results)
    print(f"  Total: {total}  |  {PASS} {passed}  |  {WARN} {warned}  |  {FAIL} {failed}")
    if failed:
        print("\n  Failed tests:")
        for s, name, detail in _results:
            if s == FAIL:
                print(f"    {FAIL}  {name}: {detail}")
    sys.exit(1 if failed else 0)


# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  lib-synology-dsm — Live NAS Integration Test")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    admin_sid = test_auth_admin()
    test_auth_audit()

    if admin_sid:
        test_users(admin_sid)
        test_groups(admin_sid)
        test_shares(admin_sid)
        test_filestation(admin_sid)
        cleanup(admin_sid)
        # Final logout
        logout(admin_sid)
    else:
        record(FAIL, "All subsequent tests", "no admin SID available")

    summary()
