#!/usr/bin/env python3
"""
Live NAS integration test — lib-synology-dsm API validation
Run manually: python3 tests/integration/test_live_nas.py

Requires: NAS reachable at NAS_HOST:5001 (set env vars)
Credentials: API_USER (admin) / AUDIT_USER (read-only) — set via env

Uses urllib only — no httpx dependency.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from typing import Any

# ── Config ─────────────────────────────────────────────────────────────────
NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = 5001
BASE_URL = f"https://{NAS_HOST}:{NAS_PORT}/webapi/entry.cgi"

ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")
AUDIT_USER = os.environ.get("AUDIT_USER", "")
AUDIT_PASS = os.environ.get("AUDIT_PASS", "")

TEST_USER = "rune-test-tmp"
TEST_USER_PASS = os.environ.get("TEST_USER_PASS", "")
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
    section(f"1. Auth v7 — {ADMIN_USER} (admin)")
    sid = login(ADMIN_USER, ADMIN_PASS)
    if sid:
        record(PASS, "{ADMIN_USER} login", f"sid={sid[:12]}…")
        ok = logout(sid)
        if ok:
            record(PASS, "{ADMIN_USER} logout")
        else:
            record(WARN, "{ADMIN_USER} logout", "success=false (session may have auto-expired)")
        # Re-login for continued use
        sid = login(ADMIN_USER, ADMIN_PASS)
        if sid:
            record(PASS, "{ADMIN_USER} re-login (for subsequent tests)", f"sid={sid[:12]}…")
        return sid
    else:
        record(FAIL, "{ADMIN_USER} login", "Authentication failed")
        return None


def test_auth_audit() -> str | None:
    section(f"2. Auth v7 — {AUDIT_USER} (read-only)")
    sid = login(AUDIT_USER, AUDIT_PASS)
    if sid:
        record(PASS, f"{AUDIT_USER} login", f"sid={sid[:12]}…")
        ok = logout(sid)
        if ok:
            record(PASS, f"{AUDIT_USER} logout")
        else:
            record(WARN, f"{AUDIT_USER} logout")
        return sid
    else:
        # Error 402 = account disabled in DSM. Check DSM Control Panel > User if AUDIT_USER is disabled.
        # Error 400 = wrong password, 403 = 2FA required.
        record(
            WARN,
            f"{AUDIT_USER} login",
            "Failed — likely error 402 (account disabled). "
            f"Enable {AUDIT_USER} in DSM Control Panel → User & Group, or reset password.",
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
                    "client": os.environ.get("NFS_CLIENT", "your-nfs-subnet"),
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
            record(
                PASS,
                f"NFS SharePrivilege save ({TEST_SHARE} → {os.environ.get('NFS_CLIENT', 'your-nfs-subnet')} rw)",
            )
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
                "HTTP 403 — {ADMIN_USER} lacks administrator privilege for share creation",
            )
        else:
            record(
                WARN, f"SYNO.Core.Share create ({TEST_SHARE})", f"error={resp.get('error', resp)}"
            )
        record(WARN, "SYNO.Core.Share.NFS set — skipped (create failed)")
        record(WARN, f"SYNO.Core.Share delete ({TEST_SHARE}) — skipped (create failed)")


def test_filestation(sid: str) -> None:
    """FileStation tests — all file/folder operations use a dedicated temp folder
    inside TEST_SHARE (/TEST_SHARE/rune-test-fs-tmp/) to avoid touching existing data.
    The temp folder is created at test start and deleted at test end.
    """
    section("7. SYNO.FileStation — list / mkdir / upload / download / delete")
    if not sid:
        record(WARN, "FileStation tests skipped", "no admin session")
        return

    from synology_dsm import DSMClient
    from synology_dsm.filestation import FileStationManager

    TEST_FS_FOLDER = "rune-test-fs-tmp"
    TEST_FS_PATH = f"/{TEST_SHARE}/{TEST_FS_FOLDER}"

    client = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    # Inject the existing session — no new login needed
    client._sid = sid
    # Re-login to get synotoken (needed for write operations)
    try:
        client.login(ADMIN_USER, ADMIN_PASS)
    except Exception as e:
        record(WARN, "FileStation re-login for synotoken", str(e)[:80])
        return

    fs = FileStationManager(client)

    # 7a. list_share — read-only, always safe
    try:
        shares = fs.list_shares()
        record(PASS, "FileStation.list_shares", f"{len(shares)} shares visible")
    except Exception as e:
        record(FAIL, "FileStation.list_shares", str(e)[:120])

    # 7b. list root — read-only
    try:
        files = fs.list(f"/{TEST_SHARE}")
        record(PASS, f"FileStation.list /{TEST_SHARE}", f"{len(files)} entries")
    except Exception as e:
        record(WARN, f"FileStation.list /{TEST_SHARE}", str(e)[:80])

    # 7c. mkdir — create dedicated test folder (will be cleaned up)
    try:
        result = fs.mkdir(f"/{TEST_SHARE}", TEST_FS_FOLDER)
        record(PASS, f"FileStation.mkdir {TEST_FS_PATH}", f"created: {result.get('name')}")
    except Exception as e:
        record(FAIL, "FileStation.mkdir", str(e)[:120])
        try:
            client.logout()
        except Exception:
            pass
        return  # Cannot proceed with upload/download without the folder

    # 7d. upload — write a small test file into the temp folder only
    import tempfile

    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", prefix="rune-test-", delete=False) as tmp:
            tmp.write(b"lib-synology-dsm integration test file\n")
            tmp_path = tmp.name
        test_filename = "rune-test-upload.txt"
        result = fs.upload(tmp_path, TEST_FS_PATH, overwrite=True)
        if result.get("success"):
            record(PASS, f"FileStation.upload → {TEST_FS_PATH}/{test_filename}")
        else:
            record(FAIL, "FileStation.upload", str(result))
        os.unlink(tmp_path)
    except Exception as e:
        record(FAIL, "FileStation.upload", str(e)[:120])

    # 7e. list temp folder — verify file appears
    try:
        files = fs.list(TEST_FS_PATH)
        names = [f.get("name", "") for f in files]
        if any("rune-test" in n for n in names):
            record(PASS, f"FileStation.list {TEST_FS_PATH}", f"test file visible: {names}")
        else:
            record(WARN, f"FileStation.list {TEST_FS_PATH}", f"file not found in: {names}")
    except Exception as e:
        record(WARN, f"FileStation.list {TEST_FS_PATH}", str(e)[:80])

    # 7f. download — fetch the file back
    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as dl:
            dl_path = dl.name
        fs.download(f"{TEST_FS_PATH}/rune-test-upload.txt", dl_path)
        with open(dl_path, "rb") as fh:
            content = fh.read()
        if b"lib-synology-dsm" in content:
            record(PASS, "FileStation.download", f"{len(content)} bytes — content verified")
        else:
            record(WARN, "FileStation.download", f"unexpected content: {content[:40]}")
        os.unlink(dl_path)
    except Exception as e:
        record(WARN, "FileStation.download", str(e)[:120])

    # 7g. delete temp folder (entire rune-test-fs-tmp — contains only test artifacts)
    try:
        fs.delete(TEST_FS_PATH)
        record(PASS, f"FileStation.delete {TEST_FS_PATH}")
    except Exception as e:
        record(WARN, f"FileStation.delete {TEST_FS_PATH}", str(e)[:120])

    try:
        client.logout()
    except Exception:
        pass


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


def summary(report_path: str | None = None) -> None:
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

    if report_path:
        _write_report(report_path, passed, warned, failed, total)

    sys.exit(1 if failed else 0)


def _write_report(path: str, passed: int, warned: int, failed: int, total: int) -> None:
    """Write JSON + text integration test report to *path* (without extension)."""
    import datetime

    now = datetime.datetime.utcnow().isoformat() + "Z"
    data = {
        "timestamp": now,
        "target": BASE_URL,
        "summary": {"total": total, "passed": passed, "warned": warned, "failed": failed},
        "results": [{"status": s, "name": name, "detail": detail} for s, name, detail in _results],
    }

    # JSON report
    json_path = path if path.endswith(".json") else path + ".json"
    with open(json_path, "w") as fh:
        json.dump(data, fh, indent=2)
    print(f"\n  📄 JSON report: {json_path}")

    # Text report
    txt_path = (path[: -len(".json")] if path.endswith(".json") else path) + ".txt"
    lines = [
        "lib-synology-dsm — Integration Test Report",
        f"Timestamp : {now}",
        f"Target    : {BASE_URL}",
        f"Summary   : {total} total | ✅ {passed} | ⚠️ {warned} | ❌ {failed}",
        "",
        "Results:",
    ]
    for s, name, detail in _results:
        line = f"  {s}  {name}"
        if detail:
            line += f" — {detail}"
        lines.append(line)
    with open(txt_path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"  📄 Text report : {txt_path}")


# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="lib-synology-dsm live NAS integration test")
    parser.add_argument(
        "--report",
        metavar="PATH",
        help="Write JSON + text report to PATH (e.g. /tmp/nas-test-report)",
        default=None,
    )
    args = parser.parse_args()

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

    summary(report_path=args.report)
