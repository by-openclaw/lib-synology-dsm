#!/usr/bin/env bash
# validate-api.sh — curl-native API validation for lib-synology-dsm
#
# Purpose: Validate every DSM API endpoint used by the library directly via curl.
#          Run this FIRST when debugging. If curl fails, the lib will also fail.
#          If curl succeeds but the lib fails, the bug is in the lib.
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=<REDACTED:password>
#   bash tests/integration/validate-api.sh
#
# Optional:
#   export NAS_PORT=5001           # default 5001
#   export NFS_CLIENT=10.6.224.0/20
#   export TEST_USER_PASS=TmpPass123!
#   export FS_BASE_SHARE=by-terraform-state

set -euo pipefail

HOST="${NAS_HOST:?NAS_HOST not set}"
PORT="${NAS_PORT:-5001}"
USER="${API_USER:?API_USER not set}"
PASS="${API_PASS:?API_PASS not set}"
NFS_CLIENT="${NFS_CLIENT:-10.6.224.0/20}"
TEST_USER_PASS="${TEST_USER_PASS:-TmpPass123!}"
FS_BASE_SHARE="${FS_BASE_SHARE:-by-terraform-state}"
BASE="https://${HOST}:${PORT}/webapi/entry.cgi"

# Unique run ID — safe to run concurrently, guaranteed cleanup
RUN_ID=$(head -c4 /dev/urandom | xxd -p)
TEST_USER="rune-v-${RUN_ID}"
TEST_GROUP="rune-vg-${RUN_ID}"
TEST_SHARE="rune-vs-${RUN_ID}"
TEST_FS_FOLDER="rune-vf-${RUN_ID}"
TEST_FS_PATH="/${FS_BASE_SHARE}/${TEST_FS_FOLDER}"
UPLOAD_FILE="/tmp/rune-upload-${RUN_ID}.txt"

PASS_SYM="✅"
FAIL_SYM="❌"
PASS_COUNT=0
FAIL_COUNT=0

# ── Helpers ───────────────────────────────────────────────────────────────────

check() {
    local label="$1"
    local response="$2"
    local expect_key="${3:-success}"    # key to check in response
    local expect_val="${4:-true}"       # expected value

    actual=$(echo "$response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    # Handle compound API responses
    if 'has_fail' in d.get('data', {}):
        print('false' if d['data']['has_fail'] else 'true')
    else:
        print(str(d.get('${expect_key}', 'MISSING')).lower())
except Exception as e:
    print(f'PARSE_ERROR: {e}')
" 2>&1)

    if [[ "$actual" == "$expect_val" ]]; then
        echo "  ${PASS_SYM}  ${label}"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "  ${FAIL_SYM}  ${label}"
        echo "       expected: ${expect_key}=${expect_val}"
        echo "       actual:   ${actual}"
        echo "       response: $(echo "$response" | head -c 300)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

api() {
    curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" --data "_sid=${SID}&$*"
}

compound() {
    curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
        --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
        --data-urlencode "compound=$1"
}

cleanup() {
    api "api=SYNO.Core.User&version=1&method=delete&name=$(python3 -c "import json; print(json.dumps(['${TEST_USER}'])) " | python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read().strip()))")" > /dev/null 2>&1 || true
    api "api=SYNO.Core.Group&version=1&method=delete&name=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_GROUP}']))); ")" > /dev/null 2>&1 || true
    api "api=SYNO.Core.Share&version=1&method=delete&name=${TEST_SHARE}" > /dev/null 2>&1 || true
    api "api=SYNO.FileStation.Delete&version=2&method=start&path=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['/by-terraform-state/${TEST_FS_FOLDER}'])))") &recursive=true" > /dev/null 2>&1 || true
    rm -f "$UPLOAD_FILE" "/tmp/rune-dl-${RUN_ID}.txt"
}

trap cleanup EXIT

echo "============================================================"
echo "  lib-synology-dsm — curl API Validation"
echo "  Target: ${BASE}"
echo "  Run ID: ${RUN_ID}"
echo "============================================================"

# ── 1. Auth ───────────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  1. Auth — SYNO.API.Auth login / logout"
echo "────────────────────────────────────────────────────────────"

RESP=$(curl -sk "${BASE}" \
    --data "api=SYNO.API.Auth&version=6&method=login&account=${USER}&passwd=${PASS}&session=DSM&format=sid&enable_syno_token=yes")
SID=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['sid'])" 2>/dev/null || echo "")
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data'].get('synotoken',''))" 2>/dev/null || echo "")

if [[ -n "$SID" ]]; then
    echo "  ${PASS_SYM}  login — SID=${SID:0:12}… Token=${TOKEN:0:8}…"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo "  ${FAIL_SYM}  login FAILED — ${RESP}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    exit 1
fi

# ── 2. User CRUD ──────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  2. SYNO.Core.User — list / create / verify / delete / verify"
echo "────────────────────────────────────────────────────────────"

R=$(api "api=SYNO.Core.User&version=1&method=list")
check "User list" "$R"

R=$(api "api=SYNO.Core.User&version=1&method=create&name=${TEST_USER}&password=${TEST_USER_PASS}&email=&description=curl+validation+test")
check "User create ${TEST_USER}" "$R"

R=$(api "api=SYNO.Core.User&version=1&method=list")
FOUND=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print('true' if any(u['name']=='${TEST_USER}' for u in d.get('data',{}).get('users',[])) else 'false')" 2>/dev/null)
[[ "$FOUND" == "true" ]] && { echo "  ${PASS_SYM}  User ensure present — ${TEST_USER} in list"; PASS_COUNT=$((PASS_COUNT+1)); } \
                          || { echo "  ${FAIL_SYM}  User ensure present — ${TEST_USER} NOT in list"; FAIL_COUNT=$((FAIL_COUNT+1)); }

NAME_JSON=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_USER}']))); ")
R=$(api "api=SYNO.Core.User&version=1&method=delete&name=${NAME_JSON}")
check "User delete ${TEST_USER}" "$R"

R=$(api "api=SYNO.Core.User&version=1&method=list")
GONE=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print('true' if all(u['name']!='${TEST_USER}' for u in d.get('data',{}).get('users',[])) else 'false')" 2>/dev/null)
[[ "$GONE" == "true" ]] && { echo "  ${PASS_SYM}  User ensure absent — ${TEST_USER} gone"; PASS_COUNT=$((PASS_COUNT+1)); } \
                         || { echo "  ${FAIL_SYM}  User ensure absent — ${TEST_USER} still present"; FAIL_COUNT=$((FAIL_COUNT+1)); }

# ── 3. Group CRUD ─────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  3. SYNO.Core.Group — list / create / set members / delete"
echo "────────────────────────────────────────────────────────────"

R=$(api "api=SYNO.Core.Group&version=1&method=list")
check "Group list" "$R"

R=$(api "api=SYNO.Core.Group&version=1&method=create&name=${TEST_GROUP}&description=curl+validation")
check "Group create ${TEST_GROUP}" "$R"

MEMBERS_JSON=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${USER}'])));")
R=$(api "api=SYNO.Core.Group&version=1&method=set&name=${TEST_GROUP}&description=&members=${MEMBERS_JSON}")
check "Group set members ([${USER}] → ${TEST_GROUP})" "$R"

NAME_JSON=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_GROUP}']))); ")
R=$(api "api=SYNO.Core.Group&version=1&method=delete&name=${NAME_JSON}")
check "Group delete ${TEST_GROUP}" "$R"

# ── 4. Share CRUD + NFS ───────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  4. SYNO.Core.Share + NFS — create / set / NFS rule / delete"
echo "────────────────────────────────────────────────────────────"

R=$(api "api=SYNO.Core.Share&version=1&method=list")
check "Share list" "$R"

SHAREINFO=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps({'name':'${TEST_SHARE}','vol_path':'/volume1','desc':'','name_org':''}))); ")
R=$(api "api=SYNO.Core.Share&version=1&method=create&name=${TEST_SHARE}&shareinfo=${SHAREINFO}")
check "Share create ${TEST_SHARE}" "$R"

NFS_COMPOUND='[{"api":"SYNO.Core.FileServ.NFS.SharePrivilege","method":"save","version":1,"share_name":"'"${TEST_SHARE}"'","rule":[{"client":"'"${NFS_CLIENT}"'","privilege":"rw","root_squash":"root","async":true,"insecure":false,"crossmnt":false,"security_flavor":{"kerberos":false,"kerberos_integrity":false,"kerberos_privacy":false,"sys":true}}]},{"api":"SYNO.Core.Share","method":"set","version":1,"name":"'"${TEST_SHARE}"'","shareinfo":{"name":"'"${TEST_SHARE}"'","vol_path":"/volume1","desc":"","encryption":false,"enc_passwd":""}}]'
R=$(curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
    --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
    --data-urlencode "compound=${NFS_COMPOUND}")
check "NFS rule set (${NFS_CLIENT} rw → ${TEST_SHARE})" "$R"

R=$(api "api=SYNO.Core.Share&version=1&method=delete&name=${TEST_SHARE}")
check "Share delete ${TEST_SHARE}" "$R"

# ── 5. FileStation ────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  5. SYNO.FileStation — list / mkdir / upload / list / download / delete"
echo "────────────────────────────────────────────────────────────"

R=$(api "api=SYNO.FileStation.List&version=2&method=list_share")
check "FileStation list_share" "$R"

FOLDER_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('/${FS_BASE_SHARE}'));")
R=$(api "api=SYNO.FileStation.CreateFolder&version=2&method=create&folder_path=${FOLDER_PATH}&name=${TEST_FS_FOLDER}&force_parent=true")
check "FileStation mkdir ${TEST_FS_PATH}" "$R"

echo "lib-synology-dsm curl validation test" > "$UPLOAD_FILE"
UPLOAD_DEST=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${TEST_FS_PATH}'));")
R=$(curl -sk "${BASE}?SynoToken=${TOKEN}" \
    -H "Cookie: id=${SID}" \
    -F "api=SYNO.FileStation.Upload" \
    -F "version=2" \
    -F "method=upload" \
    -F "path=${TEST_FS_PATH}" \
    -F "create_parents=true" \
    -F "overwrite=true" \
    -F "file=@${UPLOAD_FILE};filename=rune-upload-${RUN_ID}.txt")
check "FileStation upload rune-upload-${RUN_ID}.txt" "$R"

LIST_PATH=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${TEST_FS_PATH}'));")
R=$(api "api=SYNO.FileStation.List&version=2&method=list&folder_path=${LIST_PATH}")
FOUND=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); files=d.get('data',{}).get('files',[]); print('true' if any('rune-upload-${RUN_ID}' in f.get('name','') for f in files) else 'false')" 2>/dev/null)
[[ "$FOUND" == "true" ]] && { echo "  ${PASS_SYM}  FileStation list — file visible: rune-upload-${RUN_ID}.txt"; PASS_COUNT=$((PASS_COUNT+1)); } \
                           || { echo "  ${FAIL_SYM}  FileStation list — file NOT found"; FAIL_COUNT=$((FAIL_COUNT+1)); }

DL_URL="${BASE}?api=SYNO.FileStation.Download&version=2&method=download&path=$(python3 -c "import urllib.parse,json; print(urllib.parse.quote(json.dumps(['${TEST_FS_PATH}/rune-upload-${RUN_ID}.txt'])));")&mode=open&_sid=${SID}"
curl -sk -H "X-SYNO-TOKEN: ${TOKEN}" "$DL_URL" -o "/tmp/rune-dl-${RUN_ID}.txt"
if grep -q "curl validation" "/tmp/rune-dl-${RUN_ID}.txt" 2>/dev/null; then
    echo "  ${PASS_SYM}  FileStation download — content verified"
    PASS_COUNT=$((PASS_COUNT+1))
else
    echo "  ${FAIL_SYM}  FileStation download — content mismatch or file empty"
    FAIL_COUNT=$((FAIL_COUNT+1))
fi

DEL_PATH=$(python3 -c "import urllib.parse,json; print(urllib.parse.quote(json.dumps(['${TEST_FS_PATH}'])));")
R=$(api "api=SYNO.FileStation.Delete&version=2&method=start&path=${DEL_PATH}&recursive=true")
check "FileStation delete ${TEST_FS_PATH}" "$R"

# ── Logout ────────────────────────────────────────────────────────────────────
R=$(curl -sk "${BASE}" --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}")
check "logout" "$R"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  TOTAL: $((PASS_COUNT+FAIL_COUNT))   ${PASS_SYM} ${PASS_COUNT}   ${FAIL_SYM} ${FAIL_COUNT}"
echo "────────────────────────────────────────────────────────────"

[[ $FAIL_COUNT -eq 0 ]] && exit 0 || exit 1
