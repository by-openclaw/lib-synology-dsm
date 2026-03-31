#!/usr/bin/env bash
# 01-users.sh — Validate SYNO.Core.User API (lib: UserManager)
#
# Tests: list / create / ensure present / delete / ensure absent
# Each step is confirmed before proceeding to the next.
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=<REDACTED:password>
#   export TEST_USER_PASS=TmpPass123!   # optional, default used if not set
#   bash tests/integration/curl/01-users.sh
#
# Or with active session (skip login):
#   source tests/integration/curl/00-auth.sh
#   bash tests/integration/curl/01-users.sh

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
export NAS_HOST="${NAS_HOST:?NAS_HOST not set}"
export NAS_PORT="${NAS_PORT:-5001}"
export API_USER="${API_USER:?API_USER not set}"
export API_PASS="${API_PASS:?API_PASS not set}"
export TEST_USER_PASS="${TEST_USER_PASS:-TmpPass123!}"
export BASE="https://${NAS_HOST}:${NAS_PORT}/webapi/entry.cgi"

RUN_ID=$(head -c4 /dev/urandom | xxd -p)
TEST_USER="rune-u-${RUN_ID}"

PASS_SYM="✅"; FAIL_SYM="❌"; WARN_SYM="⚠️"
PASS=0; FAIL=0
LAST_OK=0

step() { local ok="$1" label="$2" detail="${3:-}"
    if [[ "$ok" == "1" ]]; then echo "  ${PASS_SYM}  ${label}${detail:+ — $detail}"; PASS=$((PASS+1))
    else                         echo "  ${FAIL_SYM}  ${label}${detail:+ — $detail}"; FAIL=$((FAIL+1)); fi
}
check_success() {
    local label="$1" resp="$2" local_ok local_detail
    local_ok=$(echo "$resp" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
    local_detail=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','') or '')" 2>/dev/null || echo "")
    LAST_OK="$local_ok"
    [[ "$local_ok" == "1" ]] && step 1 "$label" || step 0 "$label" "$local_detail"
}
api() { curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" --data "_sid=${SID}&$*"; }

echo "════════════════════════════════════════════════════════════"
echo "  01-users.sh — SYNO.Core.User (UserManager)"
echo "  Target: ${BASE}"
echo "  Run ID: ${RUN_ID}"
echo "════════════════════════════════════════════════════════════"

# ── Auth ──────────────────────────────────────────────────────────────────────
if [[ -z "${SID:-}" ]]; then
    echo ""
    echo "  (no active session — logging in)"
    RESP=$(curl -sk "${BASE}" --data "api=SYNO.API.Auth&version=6&method=login" \
        --data-urlencode "account=${API_USER}" --data-urlencode "passwd=${API_PASS}" \
        --data "session=DSM&format=sid&enable_syno_token=yes")
    SID=$(echo "$RESP"   | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['sid'])")
    TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('synotoken',''))")
    echo "  ${PASS_SYM}  Login — SID=${SID:0:12}… Token=${TOKEN:0:8}…"
fi
OWNS_SESSION=1

cleanup() {
    api "api=SYNO.Core.User&version=1&method=delete&name=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_USER}'])))")" > /dev/null 2>&1 || true
    [[ "${OWNS_SESSION:-0}" == "1" ]] && \
        curl -sk "${BASE}" --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true
}
trap cleanup EXIT

# ── Step 1: list ──────────────────────────────────────────────────────────────
echo ""
echo "  Step 1 — list all users"
R=$(api "api=SYNO.Core.User&version=1&method=list")
check_success "SYNO.Core.User list" "$R"
COUNT=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',{}).get('users',[])))" 2>/dev/null || echo "?")
[[ "$LAST_OK" == "1" ]] && echo "       ${COUNT} users found"

# ── Step 2: create ────────────────────────────────────────────────────────────
echo ""
echo "  Step 2 — create test user: ${TEST_USER}"
R=$(curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
    --data "_sid=${SID}&api=SYNO.Core.User&version=1&method=create&name=${TEST_USER}" \
    --data-urlencode "password=${TEST_USER_PASS}" \
    --data "email=&description=curl+validation+test")
check_success "SYNO.Core.User create" "$R"
ok=$LAST_OK
[[ "$ok" != "1" ]] && { echo "  Cannot continue — create failed"; exit 1; }

# ── Step 2b: list (verify user appears in basic list) ────────────────────────
echo ""
echo "  Step 2b — list: verify ${TEST_USER} in basic user list"
R=$(api "api=SYNO.Core.User&version=1&method=list")
check_success "SYNO.Core.User list" "$R"
FOUND=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
users=[u['name'] for u in d.get('data',{}).get('users',d.get('users',[]))]
print('1' if '${TEST_USER}' in users else '0')" 2>/dev/null || echo "0")
[[ "$FOUND" == "1" ]]     && step 1 "list — ${TEST_USER} visible in user list"     || step 0 "list — ${TEST_USER} NOT in user list"

# ── Step 2d: update user (change description) ─────────────────────────────────
echo ""
echo "  Step 2d — update: change description for ${TEST_USER}"
R=$(api "api=SYNO.Core.User&version=1&method=set&name=${TEST_USER}&description=updated-by-curl")
check_success "SYNO.Core.User set (description update)" "$R"
# Verify the change
R=$(curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
    --data "_sid=${SID}&api=SYNO.Core.User&version=1&method=list&limit=100&offset=0" \
    --data-urlencode 'additional=["description"]')
DESC=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
users=d.get('data',d).get('users',[])
match=[u for u in users if u.get('name')=='${TEST_USER}']
print(match[0].get('description','') if match else '')" 2>/dev/null || echo "")
[[ "$DESC" == "updated-by-curl" ]] \
    && step 1 "update verify — description is 'updated-by-curl'" \
    || step 0 "update verify — expected 'updated-by-curl', got '${DESC}'"

# ── Step 2e: list_detailed (verify extended fields — after update so desc is set) ──
echo ""
echo "  Step 2e — list_detailed: verify extended fields for ${TEST_USER}"
R=$(curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
    --data "_sid=${SID}&api=SYNO.Core.User&version=1&method=list&limit=100&offset=0" \
    --data-urlencode 'additional=["description","email","expired","2fa_status"]')
check_success "SYNO.Core.User list (additional fields)" "$R"
USER_INFO=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
users=d.get('data',d).get('users',[])
match=[u for u in users if u.get('name')=='${TEST_USER}']
import json as j; print(j.dumps(match[0]) if match else '{}')" 2>/dev/null || echo "{}")
HAS_EXPIRED=$(echo "$USER_INFO" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print('1' if 'expired' in d else '0')" 2>/dev/null || echo "0")
[[ "$HAS_EXPIRED" == "1" ]] \
    && step 1 "list_detailed — extended fields present: expired, email, 2fa_status" \
    || step 0 "list_detailed — extended fields missing: ${USER_INFO}"
# Verify description was persisted from the update step
DESC_CHECK=$(echo "$USER_INFO" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('description',''))" 2>/dev/null || echo "")
[[ "$DESC_CHECK" == "updated-by-curl" ]] \
    && step 1 "list_detailed — description field confirms update persisted" \
    || step 0 "list_detailed — description mismatch: got '${DESC_CHECK}'"

# ── Step 3: ensure present (verify create worked) ─────────────────────────────
echo ""
echo "  Step 3 — ensure present: verify ${TEST_USER} appears in list"
R=$(api "api=SYNO.Core.User&version=1&method=list")
FOUND=$(echo "$R" | python3 -c "
import sys,json
d=json.load(sys.stdin)
users=[u['name'] for u in d.get('data',{}).get('users',[])]
print('1' if '${TEST_USER}' in users else '0')
" 2>/dev/null || echo "0")
[[ "$FOUND" == "1" ]] \
    && step 1 "ensure present — ${TEST_USER} in user list" \
    || step 0 "ensure present — ${TEST_USER} NOT found in list"

# ── Step 4: delete ────────────────────────────────────────────────────────────
echo ""
echo "  Step 4 — delete test user: ${TEST_USER}"
NAME_JSON=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_USER}'])))")
R=$(api "api=SYNO.Core.User&version=1&method=delete&name=${NAME_JSON}")
check_success "SYNO.Core.User delete" "$R"; ok=$LAST_OK

# ── Step 5: ensure absent (verify delete worked) ──────────────────────────────
echo ""
echo "  Step 5 — ensure absent: verify ${TEST_USER} is gone from list"
R=$(api "api=SYNO.Core.User&version=1&method=list")
GONE=$(echo "$R" | python3 -c "
import sys,json
d=json.load(sys.stdin)
users=[u['name'] for u in d.get('data',{}).get('users',[])]
print('1' if '${TEST_USER}' not in users else '0')
" 2>/dev/null || echo "0")
[[ "$GONE" == "1" ]] \
    && step 1 "ensure absent — ${TEST_USER} no longer in list" \
    || step 0 "ensure absent — ${TEST_USER} still present after delete"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  TOTAL: $((PASS+FAIL))   ${PASS_SYM} ${PASS}   ${FAIL_SYM} ${FAIL}"
echo "────────────────────────────────────────────────────────────"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
