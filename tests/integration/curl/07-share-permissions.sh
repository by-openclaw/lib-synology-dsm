#!/usr/bin/env bash
# 07-share-permissions.sh — Validate SYNO.Core.Share.Permission list_by_group
#                            (lib: ShareManager.list_shares_for_group)
#
# Tests:
#   - list shares accessible by group (administrators)
#   - verify response shape: name, is_writable, is_readonly, is_deny
#   - list with additional fields (hidden, encryption, is_aclmode)
#   - list with custom share_type filter (local only)
#
# Payload confirmed via Chrome DevTools F12 on DSM 7.1.1-42962 Update 9
# (Image 3 — SYNO.Core.Share.Permission list_by_group payload).
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=<REDACTED:password>
#   export QUERY_GROUP=administrators    # group to query (default: administrators)
#   bash tests/integration/curl/07-share-permissions.sh

set -euo pipefail

export NAS_HOST="${NAS_HOST:?NAS_HOST not set}"
export NAS_PORT="${NAS_PORT:-5001}"
export API_USER="${API_USER:?API_USER not set}"
export API_PASS="${API_PASS:?API_PASS not set}"
export QUERY_GROUP="${QUERY_GROUP:-administrators}"
export BASE="https://${NAS_HOST}:${NAS_PORT}/webapi/entry.cgi"

PASS_SYM="✅"; FAIL_SYM="❌"
PASS=0; FAIL=0

step() { local ok="$1" label="$2" detail="${3:-}"
    if [[ "$ok" == "1" ]]; then echo "  ${PASS_SYM}  ${label}${detail:+ — $detail}"; PASS=$((PASS+1))
    else                         echo "  ${FAIL_SYM}  ${label}${detail:+ — $detail}"; FAIL=$((FAIL+1)); fi
}

api() {
    curl -sk -X POST "${BASE}" \
        --data "_sid=${SID}" \
        -H "X-SYNO-TOKEN: ${TOKEN}" \
        --data "$1"
}

echo "════════════════════════════════════════════════════════════"
echo "  07-share-permissions.sh — SYNO.Core.Share.Permission list_by_group"
echo "  Target: ${BASE}"
echo "  Query group: ${QUERY_GROUP}"
echo "════════════════════════════════════════════════════════════"

# ── Auth ──────────────────────────────────────────────────────────────────────
echo ""
echo "  Auth"
LOGIN=$(curl -sk -X POST "${BASE}" \
    --data "api=SYNO.API.Auth&version=6&method=login" \
    --data "account=${API_USER}&passwd=${API_PASS}" \
    --data "session=DSM&format=sid&enable_syno_token=yes")
SID=$(echo "$LOGIN"   | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['sid'])" 2>/dev/null || echo "")
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('synotoken',''))" 2>/dev/null || echo "")
[[ -n "$SID" ]] && step 1 "Login" "SID=${SID:0:12}…" || { step 0 "Login FAILED"; exit 1; }

SHARE_TYPES='["dec","local","usb","sata","cluster","c2","cold_storage"]'

# ── Step 1: list shares for group ─────────────────────────────────────────────
echo ""
echo "  Step 1 — list_by_group: ${QUERY_GROUP}"
R=$(api "api=SYNO.Core.Share.Permission&version=1&method=list_by_group&name=${QUERY_GROUP}&user_group_type=local_group&share_type=${SHARE_TYPES}")
OK=$(echo "$R" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
COUNT=$(echo "$R" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('shares',[])))" 2>/dev/null || echo "0")
step "$OK" "SYNO.Core.Share.Permission list_by_group" "shares=${COUNT}"

# ── Step 2: verify response fields ────────────────────────────────────────────
echo ""
echo "  Step 2 — verify share fields: name, is_writable, is_readonly, is_deny"
FIELDS_OK=$(echo "$R" | python3 -c "
import sys, json
d = json.load(sys.stdin)
shares = d.get('data', {}).get('shares', [])
if not shares:
    print('1')  # no shares is valid — group may have no access
    sys.exit()
s = shares[0]
required = ['name', 'is_writable', 'is_readonly', 'is_deny']
missing = [f for f in required if f not in s]
print('0' if missing else '1')
" 2>/dev/null || echo "0")
step "$FIELDS_OK" "Share permission fields present"

# ── Step 3: display share access summary ──────────────────────────────────────
echo ""
echo "  Step 3 — share access summary for ${QUERY_GROUP}"
echo "$R" | python3 -c "
import sys, json
d = json.load(sys.stdin)
shares = d.get('data', {}).get('shares', [])
if not shares:
    print('    (no shares accessible)')
for s in shares:
    if s.get('is_writable'):   access = 'rw'
    elif s.get('is_readonly'): access = 'ro'
    elif s.get('is_deny'):     access = 'deny'
    else:                      access = '?'
    print(f\"    {s.get('name','?'):30s}  {access}\")
" 2>/dev/null || true
step 1 "Share access summary displayed"

# ── Step 4: list with additional fields ───────────────────────────────────────
echo ""
echo "  Step 4 — list_by_group with additional=[hidden, encryption, is_aclmode]"
ADDITIONAL='["hidden","encryption","is_aclmode"]'
R2=$(api "api=SYNO.Core.Share.Permission&version=1&method=list_by_group&name=${QUERY_GROUP}&user_group_type=local_group&share_type=${SHARE_TYPES}&additional=${ADDITIONAL}")
OK2=$(echo "$R2" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
step "$OK2" "list_by_group with additional fields"

# ── Step 5: list with custom share_type filter ────────────────────────────────
echo ""
echo "  Step 5 — list_by_group with share_type=[local] only"
R3=$(api "api=SYNO.Core.Share.Permission&version=1&method=list_by_group&name=${QUERY_GROUP}&user_group_type=local_group&share_type=[\"local\"]")
OK3=$(echo "$R3" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
COUNT3=$(echo "$R3" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('shares',[])))" 2>/dev/null || echo "0")
step "$OK3" "list_by_group share_type=[local]" "shares=${COUNT3}"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────"
echo "  Total: $((PASS+FAIL))  |  ${PASS_SYM} ${PASS}  |  ${FAIL_SYM} ${FAIL}"

curl -sk -X POST "${BASE}" \
    --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true

[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
