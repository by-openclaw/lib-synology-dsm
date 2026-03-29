#!/usr/bin/env bash
# 02-groups.sh — Validate SYNO.Core.Group API (lib: GroupManager)
#
# Tests: list / create / ensure present / set members / delete / ensure absent
# Note on member_list: SYNO.Core.Group member_list returns error 103 on
# DSM 7.1.1-42962 Update 9. This is a known DSM firmware bug — tracked in
# platform-setup#54. The write side (set members) works correctly.
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=BySyst3ms_
#   bash tests/integration/curl/02-groups.sh

set -euo pipefail

export NAS_HOST="${NAS_HOST:?NAS_HOST not set}"
export NAS_PORT="${NAS_PORT:-5001}"
export API_USER="${API_USER:?API_USER not set}"
export API_PASS="${API_PASS:?API_PASS not set}"
export BASE="https://${NAS_HOST}:${NAS_PORT}/webapi/entry.cgi"

RUN_ID=$(head -c4 /dev/urandom | xxd -p)
TEST_GROUP="rune-g-${RUN_ID}"
TEST_MEMBER="${API_USER}"   # add the API user itself as a member for testing

PASS_SYM="✅"; FAIL_SYM="❌"; WARN_SYM="⚠️"
PASS=0; FAIL=0; WARN=0

step()  { local ok="$1" label="$2" detail="${3:-}"
    if [[ "$ok" == "1" ]]; then echo "  ${PASS_SYM}  ${label}${detail:+ — $detail}"; PASS=$((PASS+1))
    else                         echo "  ${FAIL_SYM}  ${label}${detail:+ — $detail}"; FAIL=$((FAIL+1)); fi; }
warn()  { echo "  ${WARN_SYM}  $1${2:+ — $2}"; WARN=$((WARN+1)); }
LAST_OK=0
check() { local label="$1" resp="$2"
    LAST_OK=$(echo "$resp" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
    local detail; detail=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','') or '')" 2>/dev/null || echo "")
    [[ "$LAST_OK" == "1" ]] && step 1 "$label" || step 0 "$label" "$detail"; }
api()   { curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" --data "_sid=${SID}&$*"; }

echo "════════════════════════════════════════════════════════════"
echo "  02-groups.sh — SYNO.Core.Group (GroupManager)"
echo "  Target: ${BASE}"
echo "  Run ID: ${RUN_ID}"
echo "════════════════════════════════════════════════════════════"

# ── Auth ──────────────────────────────────────────────────────────────────────
if [[ -z "${SID:-}" ]]; then
    RESP=$(curl -sk "${BASE}" --data "api=SYNO.API.Auth&version=6&method=login" \
        --data-urlencode "account=${API_USER}" --data-urlencode "passwd=${API_PASS}" \
        --data "session=DSM&format=sid&enable_syno_token=yes")
    SID=$(echo "$RESP"   | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['sid'])")
    TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('synotoken',''))")
    echo ""; echo "  ${PASS_SYM}  Login — SID=${SID:0:12}… Token=${TOKEN:0:8}…"
fi
OWNS_SESSION=1

cleanup() {
    local GJSON; GJSON=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_GROUP}'])))" 2>/dev/null || echo "")
    [[ -n "$GJSON" ]] && api "api=SYNO.Core.Group&version=1&method=delete&name=${GJSON}" > /dev/null 2>&1 || true
    [[ "${OWNS_SESSION:-0}" == "1" ]] && \
        curl -sk "${BASE}" --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true
}
trap cleanup EXIT

# ── Step 1: list ──────────────────────────────────────────────────────────────
echo ""; echo "  Step 1 — list all groups"
R=$(api "api=SYNO.Core.Group&version=1&method=list")
check "SYNO.Core.Group list" "$R"; ok=$LAST_OK
COUNT=$(echo "$R" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('groups',[])))" 2>/dev/null || echo "?")
[[ "$ok" == "1" ]] && echo "       ${COUNT} groups found"

# ── Step 2: create ────────────────────────────────────────────────────────────
echo ""; echo "  Step 2 — create test group: ${TEST_GROUP}"
R=$(api "api=SYNO.Core.Group&version=1&method=create&name=${TEST_GROUP}&description=curl+validation")
check "SYNO.Core.Group create" "$R"; ok=$LAST_OK
[[ "$ok" != "1" ]] && { echo "  Cannot continue — create failed"; exit 1; }

# ── Step 3: ensure present ────────────────────────────────────────────────────
echo ""; echo "  Step 3 — ensure present: verify ${TEST_GROUP} in list"
R=$(api "api=SYNO.Core.Group&version=1&method=list")
FOUND=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
groups=[g['name'] for g in d.get('data',{}).get('groups',[])]
print('1' if '${TEST_GROUP}' in groups else '0')" 2>/dev/null || echo "0")
[[ "$FOUND" == "1" ]] \
    && step 1 "ensure present — ${TEST_GROUP} in group list" \
    || step 0 "ensure present — ${TEST_GROUP} NOT found in list"

# ── Step 4: add member ────────────────────────────────────────────────────────
echo ""; echo "  Step 4 — add member: ${TEST_MEMBER} → ${TEST_GROUP}"
R=$(api "api=SYNO.Core.Group.Member&version=1&method=add&group=${TEST_GROUP}&name=${TEST_MEMBER}")
check "SYNO.Core.Group.Member add (${TEST_MEMBER})" "$R"

# ── Step 5: read members via correct API ──────────────────────────────────────
echo ""; echo "  Step 5 — member read-back (SYNO.Core.Group.Member list ingroup=true)"
R=$(api "api=SYNO.Core.Group.Member&version=1&method=list&group=${TEST_GROUP}&ingroup=true")
OK=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print('1' if d.get('success') or 'offset' in d else '0')" 2>/dev/null || echo "0")
if [[ "$OK" == "1" ]]; then
    MEMBERS=$(echo "$R" | python3 -c "import sys,json; print([u['name'] for u in json.load(sys.stdin).get('data',{}).get('users',[])])" 2>/dev/null || echo "[]")
    step 1 "SYNO.Core.Group.Member list — members: ${MEMBERS}"
else
    step 0 "SYNO.Core.Group.Member list" "$R"
fi

# ── Step 6: remove member ─────────────────────────────────────────────────────
echo ""; echo "  Step 6 — remove member: ${TEST_MEMBER} from ${TEST_GROUP}"
R=$(api "api=SYNO.Core.Group.Member&version=1&method=remove&group=${TEST_GROUP}&name=${TEST_MEMBER}")
check "SYNO.Core.Group.Member remove (${TEST_MEMBER})" "$R"

# ── Step 6b: verify member removed ────────────────────────────────────────────
echo ""; echo "  Step 6b — ensure member absent: verify ${TEST_MEMBER} not in group"
R=$(api "api=SYNO.Core.Group.Member&version=1&method=list&group=${TEST_GROUP}&ingroup=true")
GONE=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
users=[u['name'] for u in d.get('data',{}).get('users',d.get('users',[]))]
print('1' if '${TEST_MEMBER}' not in users else '0')" 2>/dev/null || echo "0")
[[ "$GONE" == "1" ]]     && step 1 "ensure member absent — ${TEST_MEMBER} removed from group"     || step 0 "ensure member absent — ${TEST_MEMBER} still in group"

# ── Step 7: delete ────────────────────────────────────────────────────────────
echo ""; echo "  Step 7 — delete: ${TEST_GROUP}"
NAME_JSON=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_GROUP}'])))")
R=$(api "api=SYNO.Core.Group&version=1&method=delete&name=${NAME_JSON}")
check "SYNO.Core.Group delete" "$R"

# ── Step 7: ensure absent ─────────────────────────────────────────────────────
echo ""; echo "  Step 8 — ensure absent: verify ${TEST_GROUP} is gone"
R=$(api "api=SYNO.Core.Group&version=1&method=list")
GONE=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
groups=[g['name'] for g in d.get('data',{}).get('groups',[])]
print('1' if '${TEST_GROUP}' not in groups else '0')" 2>/dev/null || echo "0")
[[ "$GONE" == "1" ]] \
    && step 1 "ensure absent — ${TEST_GROUP} no longer in list" \
    || step 0 "ensure absent — ${TEST_GROUP} still present after delete"

echo ""
echo "────────────────────────────────────────────────────────────"
echo "  TOTAL: $((PASS+FAIL+WARN))   ${PASS_SYM} ${PASS}   ${WARN_SYM} ${WARN}   ${FAIL_SYM} ${FAIL}"
echo "────────────────────────────────────────────────────────────"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
