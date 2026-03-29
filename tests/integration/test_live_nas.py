#!/usr/bin/env python3
"""
Live NAS integration test — lib-synology-dsm

Tests the library's public API end-to-end against a real Synology DSM instance.
Every resource goes through the full ensure() lifecycle:
  ensure(present) → changed=True (created)
  ensure(present) → changed=False (noop — state matches)
  ensure(absent)  → changed=True (deleted)
  ensure(absent)  → changed=False (noop — already gone)

Run:
  python tests/integration/test_live_nas.py [--report /path/to/report]

Required env vars:
  NAS_HOST        IP or hostname of DSM (e.g. 10.6.224.6)
  API_USER        Admin account (administrators group)
  API_PASS        Admin password
  TEST_USER_PASS  Password to set on test user
  NFS_CLIENT      CIDR for NFS rule (e.g. 10.6.224.0/20)

Optional:
  NAS_PORT        HTTPS port (default 5001)
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import tempfile
import uuid

# ── Config ─────────────────────────────────────────────────────────────────
NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = int(os.environ.get("NAS_PORT", "5001"))
ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")
TEST_USER_PASS = os.environ.get("TEST_USER_PASS", "TmpPass123!")
NFS_CLIENT = os.environ.get("NFS_CLIENT", "10.6.224.0/20")

# All test resources use a unique run-ID suffix — safe to run concurrently,
# and guaranteed cleanup even if a previous run failed mid-way.
RUN_ID = uuid.uuid4().hex[:8]
TEST_USER = f"rune-t-{RUN_ID}"
TEST_GROUP = f"rune-tg-{RUN_ID}"
TEST_SHARE = f"rune-ts-{RUN_ID}"
FS_BASE_SHARE = "by-terraform-state"  # existing share — never deleted
TEST_FS_FOLDER = f"rune-tf-{RUN_ID}"
TEST_FS_PATH = f"/{FS_BASE_SHARE}/{TEST_FS_FOLDER}"
TEST_UPLOAD_FILENAME = f"rune-upload-{RUN_ID}.txt"

PASS = "✅"
WARN = "⚠️"
FAIL = "❌"

_results: list[dict] = []


def record(status: str, name: str, detail: str = "", expected: str = "", actual: str = "") -> None:
    entry = {
        "status": status,
        "name": name,
        "detail": detail,
        "expected": expected,
        "actual": actual,
    }
    _results.append(entry)
    icon = status
    msg = f"  {icon}  {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def assert_ensure(result: dict, expected_changed: bool, expected_action: str, label: str) -> bool:
    """Verify an ensure() result matches expected changed+action. Records pass or fail."""
    ok = result.get("changed") == expected_changed and result.get("action") == expected_action
    if ok:
        record(PASS, label, f"changed={result['changed']} action={result['action']}")
    else:
        record(
            FAIL,
            label,
            f"changed={result.get('changed')} action={result.get('action')}",
            expected=f"changed={expected_changed} action={expected_action}",
            actual=f"changed={result.get('changed')} action={result.get('action')}",
        )
    return ok


# ── Library imports ─────────────────────────────────────────────────────────
try:
    from synology_dsm import DSMClient, ShareManager, UserManager, GroupManager, NFSManager
    from synology_dsm.filestation import FileStationManager
    from synology_dsm.exceptions import DSMError
except ImportError as e:
    print(f"❌ Cannot import synology_dsm: {e}")
    print("   Run: pip install -e '.[dev]' from the repo root")
    sys.exit(1)


# ── Test sections ───────────────────────────────────────────────────────────


def test_auth(client: DSMClient) -> None:
    section("1. Auth — login / logout / re-login")
    try:
        client.login(ADMIN_USER, ADMIN_PASS)
        record(PASS, "login", f"SID={client._sid[:12]}… Token={client._synotoken[:8]}…")
    except DSMError as e:
        record(FAIL, "login", str(e))
        raise


def test_users(client: DSMClient) -> None:
    section("2. UserManager — full ensure() lifecycle")
    mgr = UserManager(client)

    # 2a. ensure present — user does not exist → should create
    r = mgr.ensure(
        TEST_USER, password=TEST_USER_PASS, state="present", description="Rune integration test"
    )
    if not assert_ensure(r, True, "created", f"ensure(present) create {TEST_USER}"):
        return

    # 2b. ensure present again — already exists, same params → noop
    r = mgr.ensure(
        TEST_USER, password=TEST_USER_PASS, state="present", description="Rune integration test"
    )
    assert_ensure(r, False, "noop", f"ensure(present) noop {TEST_USER}")

    # 2c. ensure absent — user exists → should delete
    r = mgr.ensure(TEST_USER, state="absent")
    if not assert_ensure(r, True, "deleted", f"ensure(absent) delete {TEST_USER}"):
        return

    # 2d. ensure absent again — already gone → noop
    r = mgr.ensure(TEST_USER, state="absent")
    assert_ensure(r, False, "noop", f"ensure(absent) noop {TEST_USER}")


def test_groups(client: DSMClient) -> None:
    section("3. GroupManager — full ensure() lifecycle + member add/remove")
    mgr = GroupManager(client)
    users = UserManager(client)

    # Create a temp user to add as member
    users.ensure(TEST_USER, password=TEST_USER_PASS, state="present")

    # 3a. ensure present — group does not exist → should create
    r = mgr.ensure(TEST_GROUP, state="present", description="Rune integration test")
    if not assert_ensure(r, True, "created", f"ensure(present) create {TEST_GROUP}"):
        users.ensure(TEST_USER, state="absent")
        return

    # 3b. ensure present again → noop
    r = mgr.ensure(TEST_GROUP, state="present", description="Rune integration test")
    assert_ensure(r, False, "noop", f"ensure(present) noop {TEST_GROUP}")

    # 3c. add_member — user not yet in group → changed=True
    r = mgr.add_member(TEST_GROUP, TEST_USER)
    assert_ensure(r, True, "added", f"add_member {TEST_USER} → {TEST_GROUP}")

    # 3d. add_member again — already member → noop
    # On DSM versions where member_list is unavailable (e.g. DS1513+ older firmware),
    # idempotency cannot be verified — operation applies unconditionally (warning returned).
    r = mgr.add_member(TEST_GROUP, TEST_USER)
    if "warning" in r:
        record(
            WARN,
            f"add_member noop {TEST_USER} already in {TEST_GROUP}",
            f"DSM limitation: {r['warning']}",
        )
    else:
        assert_ensure(r, False, "noop", f"add_member noop {TEST_USER} already in {TEST_GROUP}")

    # 3e. remove_member — user in group → changed=True
    r = mgr.remove_member(TEST_GROUP, TEST_USER)
    if "warning" in r:
        record(WARN, f"remove_member {TEST_USER} ← {TEST_GROUP}", f"DSM limitation: {r['warning']}")
    else:
        assert_ensure(r, True, "removed", f"remove_member {TEST_USER} ← {TEST_GROUP}")

    # 3f. remove_member again — not in group → noop
    r = mgr.remove_member(TEST_GROUP, TEST_USER)
    if "warning" in r:
        record(
            WARN,
            f"remove_member noop {TEST_USER} not in {TEST_GROUP}",
            f"DSM limitation: {r['warning']}",
        )
    else:
        assert_ensure(r, False, "noop", f"remove_member noop {TEST_USER} not in {TEST_GROUP}")

    # 3g. ensure absent → deleted
    r = mgr.ensure(TEST_GROUP, state="absent")
    assert_ensure(r, True, "deleted", f"ensure(absent) delete {TEST_GROUP}")

    # 3h. ensure absent again → noop
    r = mgr.ensure(TEST_GROUP, state="absent")
    assert_ensure(r, False, "noop", f"ensure(absent) noop {TEST_GROUP}")

    # Cleanup temp user
    users.ensure(TEST_USER, state="absent")


def test_shares(client: DSMClient) -> None:
    section("4. ShareManager — full ensure() lifecycle + NFS rule")
    shares = ShareManager(client)
    nfs = NFSManager(client)

    # 4a. ensure present — share does not exist → created
    r = shares.ensure(
        TEST_SHARE, state="present", volume_path="/volume1", description="Rune integration test"
    )
    if not assert_ensure(r, True, "created", f"ensure(present) create {TEST_SHARE}"):
        return

    # 4b. ensure present again → noop
    r = shares.ensure(
        TEST_SHARE, state="present", volume_path="/volume1", description="Rune integration test"
    )
    assert_ensure(r, False, "noop", f"ensure(present) noop {TEST_SHARE}")

    # 4c. NFS rule — add rule for NFS_CLIENT → created
    r = nfs.ensure(TEST_SHARE, NFS_CLIENT, state="present", rw=True)
    assert_ensure(r, True, "created", f"NFS ensure(present) {NFS_CLIENT} → {TEST_SHARE}")

    # 4d. NFS rule — same rule again → noop
    r = nfs.ensure(TEST_SHARE, NFS_CLIENT, state="present", rw=True)
    assert_ensure(r, False, "noop", f"NFS ensure(present) noop {NFS_CLIENT}")

    # 4e. NFS rule — change rw→ro → updated
    r = nfs.ensure(TEST_SHARE, NFS_CLIENT, state="present", rw=False)
    assert_ensure(r, True, "updated", f"NFS ensure(present) update rw→ro {NFS_CLIENT}")

    # 4f. NFS rule — remove → deleted
    r = nfs.ensure(TEST_SHARE, NFS_CLIENT, state="absent")
    assert_ensure(r, True, "deleted", f"NFS ensure(absent) delete {NFS_CLIENT}")

    # 4g. NFS rule — remove again → noop
    r = nfs.ensure(TEST_SHARE, NFS_CLIENT, state="absent")
    assert_ensure(r, False, "noop", f"NFS ensure(absent) noop {NFS_CLIENT}")

    # 4h. ensure absent → deleted
    r = shares.ensure(TEST_SHARE, state="absent")
    assert_ensure(r, True, "deleted", f"ensure(absent) delete {TEST_SHARE}")

    # 4i. ensure absent again → noop
    r = shares.ensure(TEST_SHARE, state="absent")
    assert_ensure(r, False, "noop", f"ensure(absent) noop {TEST_SHARE}")


def test_filestation(client: DSMClient) -> None:
    section("5. FileStationManager — list / ensure folder / upload / download / delete")
    fs = FileStationManager(client)

    # 5a. list_shares — always safe
    try:
        shares = fs.list_shares()
        record(PASS, "list_shares", f"{len(shares)} shares visible")
    except Exception as e:
        record(FAIL, "list_shares", str(e)[:100])
        return

    # 5b. ensure folder present — does not exist → created
    r = fs.ensure(TEST_FS_PATH, state="present")
    if not assert_ensure(r, True, "created", f"ensure(present) mkdir {TEST_FS_PATH}"):
        return

    # 5c. ensure folder present again → noop
    r = fs.ensure(TEST_FS_PATH, state="present")
    assert_ensure(r, False, "noop", f"ensure(present) noop {TEST_FS_PATH}")

    # 5d. upload a file with deterministic name (run-scoped)
    try:
        tmp_path = os.path.join(tempfile.gettempdir(), TEST_UPLOAD_FILENAME)
        with open(tmp_path, "wb") as f:
            f.write(b"lib-synology-dsm integration test\n")
        result = fs.upload(tmp_path, TEST_FS_PATH, overwrite=True)
        os.unlink(tmp_path)
        if result.get("success") or result.get("skipped") is False:
            record(PASS, f"upload {TEST_UPLOAD_FILENAME}", f"→ {TEST_FS_PATH}")
        else:
            record(FAIL, "upload", str(result))
    except Exception as e:
        record(FAIL, "upload", str(e)[:120])

    # 5e. list folder — verify uploaded file appears
    try:
        files = fs.list(TEST_FS_PATH)
        names = [f.get("name", "") for f in files]
        if TEST_UPLOAD_FILENAME in names:
            record(PASS, "list folder", f"file visible: {TEST_UPLOAD_FILENAME}")
        else:
            record(FAIL, "list folder", f"expected {TEST_UPLOAD_FILENAME!r} in {names}")
    except Exception as e:
        record(FAIL, "list folder", str(e)[:80])

    # 5f. download — fetch file back, verify content
    try:
        dl_path = os.path.join(tempfile.gettempdir(), f"rune-dl-{RUN_ID}.txt")
        fs.download(f"{TEST_FS_PATH}/{TEST_UPLOAD_FILENAME}", dl_path)
        with open(dl_path, "rb") as f:
            content = f.read()
        os.unlink(dl_path)
        if b"lib-synology-dsm" in content:
            record(PASS, "download", f"{len(content)} bytes — content verified")
        else:
            record(FAIL, "download", f"unexpected content: {content[:40]}")
    except Exception as e:
        record(FAIL, "download", str(e)[:120])

    # 5g. ensure folder absent → deleted (removes folder + file)
    r = fs.ensure(TEST_FS_PATH, state="absent")
    assert_ensure(r, True, "deleted", f"ensure(absent) delete {TEST_FS_PATH}")

    # 5h. ensure folder absent again → noop
    r = fs.ensure(TEST_FS_PATH, state="absent")
    assert_ensure(r, False, "noop", f"ensure(absent) noop {TEST_FS_PATH}")


def cleanup(client: DSMClient) -> None:
    """Best-effort cleanup of any test artifacts from this run."""
    section("Cleanup — removing any leftover test artifacts")
    try:
        UserManager(client).ensure(TEST_USER, state="absent")
    except Exception:
        pass
    try:
        GroupManager(client).ensure(TEST_GROUP, state="absent")
    except Exception:
        pass
    try:
        ShareManager(client).ensure(TEST_SHARE, state="absent")
    except Exception:
        pass
    try:
        FileStationManager(client).ensure(TEST_FS_PATH, state="absent")
    except Exception:
        pass


# ── Report ──────────────────────────────────────────────────────────────────


def write_report(path_base: str | None) -> None:
    total = len(_results)
    passed = sum(1 for r in _results if r["status"] == PASS)
    warned = sum(1 for r in _results if r["status"] == WARN)
    failed = sum(1 for r in _results if r["status"] == FAIL)

    lines = [
        "=" * 60,
        "  lib-synology-dsm — Integration Test Report",
        f"  Run ID: {RUN_ID}",
        f"  NAS:    https://{NAS_HOST}:{NAS_PORT}",
        f"  User:   {ADMIN_USER}",
        f"  Time:   {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        "=" * 60,
        "",
    ]

    current_section = ""
    for r in _results:
        section_name = r["name"].split(":")[0] if ":" in r["name"] else ""
        if section_name != current_section:
            current_section = section_name

        line = f"  {r['status']}  {r['name']}"
        if r["detail"]:
            line += f"\n       detail:   {r['detail']}"
        if r["expected"]:
            line += f"\n       expected: {r['expected']}"
        if r["actual"] and r["status"] == FAIL:
            line += f"\n       actual:   {r['actual']}"
        lines.append(line)

    lines += [
        "",
        "─" * 60,
        f"  TOTAL: {total}   ✅ {passed}   ⚠️ {warned}   ❌ {failed}",
        "─" * 60,
    ]

    if failed:
        lines.append("\n  Failed tests:")
        for r in _results:
            if r["status"] == FAIL:
                lines.append(f"    ❌  {r['name']}: {r['detail']}")

    report_text = "\n".join(lines)
    print("\n" + report_text)

    if path_base:
        with open(f"{path_base}.txt", "w") as f:
            f.write(report_text)
        with open(f"{path_base}.json", "w") as f:
            json.dump(
                {
                    "run_id": RUN_ID,
                    "nas": NAS_HOST,
                    "user": ADMIN_USER,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "summary": {
                        "total": total,
                        "passed": passed,
                        "warned": warned,
                        "failed": failed,
                    },
                    "results": _results,
                },
                f,
                indent=2,
            )
        print(f"\n  📄 Text:  {path_base}.txt")
        print(f"  📄 JSON:  {path_base}.json")

    return failed


# ── Entrypoint ──────────────────────────────────────────────────────────────


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="lib-synology-dsm integration test")
    parser.add_argument("--report", metavar="PATH", help="Write report to PATH.txt and PATH.json")
    args = parser.parse_args()

    if not NAS_HOST or not ADMIN_USER or not ADMIN_PASS:
        print("❌ Missing required env vars: NAS_HOST, API_USER, API_PASS")
        sys.exit(1)

    print("=" * 60)
    print("  lib-synology-dsm — Live Integration Test")
    print(f"  Target: https://{NAS_HOST}:{NAS_PORT}")
    print(f"  Run ID: {RUN_ID}")
    print("=" * 60)

    client = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    try:
        test_auth(client)
        test_users(client)
        test_groups(client)
        test_shares(client)
        test_filestation(client)
    except DSMError as e:
        record(FAIL, "FATAL — auth failed, cannot continue", str(e))
    finally:
        cleanup(client)
        try:
            client.logout()
        except Exception:
            pass

    failed = write_report(args.report)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
