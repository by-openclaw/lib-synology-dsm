#!/usr/bin/env bash
# 04-filestation.sh — Validate SYNO.FileStation API (lib: FileStationManager)
#
# Tests: list_shares / mkdir / ensure present / upload / list folder /
#        download + verify content / delete / ensure absent
#
# Upload quirk (discovered via DevTools, documented in CLAUDE.md):
#   - SynoToken MUST be in URL query string: ?SynoToken=<token>
#   - Session passed as Cookie: id=<SID>  (NOT _sid form field)
#   - Form field is "path" (NOT "dest_folder_path")
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=BySyst3ms_
#   export FS_BASE_SHARE=by-terraform-state  # existing share to use as test base
#   bash tests/integration/curl/04-filestation.sh

set -euo pipefail

export NAS_HOST="${NAS_HOST:?NAS_HOST not set}"
export NAS_PORT="${NAS_PORT:-5001}"
export API_USER="${API_USER:?API_USER not set}"
export API_PASS="${API_PASS:?API_PASS not set}"
export FS_BASE_SHARE="${FS_BASE_SHARE:-by-terraform-state}"
export BASE="https://${NAS_HOST}:${NAS_PORT}/webapi/entry.cgi"

RUN_ID=$(head -c4 /dev/urandom | xxd -p)
TEST_FOLDER="rune-f-${RUN_ID}"
TEST_PATH="/${FS_BASE_SHARE}/${TEST_FOLDER}"
UPLOAD_FILENAME="rune-upload-${RUN_ID}.txt"
UPLOAD_LOCAL="/tmp/${UPLOAD_FILENAME}"
DOWNLOAD_LOCAL="/tmp/rune-dl-${RUN_ID}.txt"

PASS_SYM="✅"; FAIL_SYM="❌"; WARN_SYM="⚠️"
PASS=0; FAIL=0; WARN=0

step()  { local ok="$1" label="$2" detail="${3:-}"
    if [[ "$ok" == "1" ]]; then echo "  ${PASS_SYM}  ${label}${detail:+ — $detail}"; PASS=$((PASS+1))
    else                         echo "  ${FAIL_SYM}  ${label}${detail:+ — $detail}"; FAIL=$((FAIL+1)); fi; }
api()   { curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" --data "_sid=${SID}&$*"; }
LAST_OK=0
check_ok() { local label="$1" resp="$2"
    LAST_OK=$(echo "$resp" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
    local detail; detail=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','') or '')" 2>/dev/null || echo "")
    [[ "$LAST_OK" == "1" ]] && step 1 "$label" || step 0 "$label" "$detail"; }

echo "════════════════════════════════════════════════════════════"
echo "  04-filestation.sh — SYNO.FileStation (FileStationManager)"
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
    local DEL_PATH; DEL_PATH=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_PATH}'])))" 2>/dev/null || echo "")
    [[ -n "$DEL_PATH" ]] && \
        curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
            --data "_sid=${SID}&api=SYNO.FileStation.Delete&version=2&method=start&path=${DEL_PATH}&recursive=true" > /dev/null 2>&1 || true
    rm -f "$UPLOAD_LOCAL" "$DOWNLOAD_LOCAL"
    [[ "${OWNS_SESSION:-0}" == "1" ]] && \
        curl -sk "${BASE}" --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true
}
trap cleanup EXIT

# ── Step 1: list shares ───────────────────────────────────────────────────────
echo ""; echo "  Step 1 — FileStation.list_share"
R=$(api "api=SYNO.FileStation.List&version=2&method=list_share")
check_ok "FileStation.list_share" "$R"
ok=$LAST_OK
COUNT=$(echo "$R" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('shares',[])))" 2>/dev/null || echo "?")
[[ "$ok" == "1" ]] && echo "       ${COUNT} shares visible"

# ── Step 2: mkdir ─────────────────────────────────────────────────────────────
echo ""; echo "  Step 2 — mkdir: ${TEST_PATH}"
PARENT=$(python3 -c "import urllib.parse; print(urllib.parse.quote('/${FS_BASE_SHARE}'))")
R=$(api "api=SYNO.FileStation.CreateFolder&version=2&method=create&folder_path=${PARENT}&name=${TEST_FOLDER}&force_parent=true")
check_ok "FileStation.CreateFolder mkdir" "$R"

# ── Step 3: ensure present (verify mkdir) ────────────────────────────────────
echo ""; echo "  Step 3 — ensure present: verify folder ${TEST_FOLDER} exists"
PARENT_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('/${FS_BASE_SHARE}'))")
R=$(api "api=SYNO.FileStation.List&version=2&method=list&folder_path=${PARENT_ENC}")
FOUND=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
files=[f['name'] for f in d.get('data',{}).get('files',[])]
print('1' if '${TEST_FOLDER}' in files else '0')" 2>/dev/null || echo "0")
[[ "$FOUND" == "1" ]] \
    && step 1 "ensure present — ${TEST_FOLDER} visible in parent listing" \
    || step 0 "ensure present — ${TEST_FOLDER} NOT found in ${FS_BASE_SHARE}"

# ── Step 4: upload ────────────────────────────────────────────────────────────
echo ""; echo "  Step 4 — upload: ${UPLOAD_FILENAME} → ${TEST_PATH}"
echo "lib-synology-dsm FileStation curl validation test" > "$UPLOAD_LOCAL"

# IMPORTANT: Upload uses multipart form — SynoToken in URL, session as Cookie
R=$(curl -sk "${BASE}?SynoToken=${TOKEN}" \
    -H "Cookie: id=${SID}" \
    -F "api=SYNO.FileStation.Upload" \
    -F "version=2" \
    -F "method=upload" \
    -F "path=${TEST_PATH}" \
    -F "create_parents=true" \
    -F "overwrite=true" \
    -F "file=@${UPLOAD_LOCAL};filename=${UPLOAD_FILENAME}")
check_ok "FileStation.Upload" "$R"

# ── Step 5: list folder (verify file visible) ─────────────────────────────────
echo ""; echo "  Step 5 — list folder: verify ${UPLOAD_FILENAME} visible"
FOLDER_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${TEST_PATH}'))")
R=$(api "api=SYNO.FileStation.List&version=2&method=list&folder_path=${FOLDER_ENC}")
FOUND=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
files=[f['name'] for f in d.get('data',{}).get('files',[])]
print('1' if '${UPLOAD_FILENAME}' in files else '0')" 2>/dev/null || echo "0")
[[ "$FOUND" == "1" ]] \
    && step 1 "FileStation.List — ${UPLOAD_FILENAME} visible in folder" \
    || step 0 "FileStation.List — ${UPLOAD_FILENAME} NOT found in folder"

# ── Step 6: download + verify content ─────────────────────────────────────────
echo ""; echo "  Step 6 — download: ${UPLOAD_FILENAME} → verify content"
FILE_PATH_JSON=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_PATH}/${UPLOAD_FILENAME}'])))")
curl -sk \
    -H "X-SYNO-TOKEN: ${TOKEN}" \
    "${BASE}?api=SYNO.FileStation.Download&version=2&method=download&path=${FILE_PATH_JSON}&mode=open&_sid=${SID}" \
    -o "$DOWNLOAD_LOCAL"

if grep -q "lib-synology-dsm" "$DOWNLOAD_LOCAL" 2>/dev/null; then
    BYTES=$(wc -c < "$DOWNLOAD_LOCAL" 2>/dev/null || echo "?")
    step 1 "FileStation.Download — ${BYTES} bytes, content verified"
else
    CONTENT=$(cat "$DOWNLOAD_LOCAL" 2>/dev/null | head -c 100)
    step 0 "FileStation.Download — content mismatch: ${CONTENT}"
fi

# ── Step 7: delete folder ─────────────────────────────────────────────────────
echo ""; echo "  Step 7 — delete folder: ${TEST_PATH}"
DEL_PATH=$(python3 -c "import json,urllib.parse; print(urllib.parse.quote(json.dumps(['${TEST_PATH}'])))")
R=$(api "api=SYNO.FileStation.Delete&version=2&method=start&path=${DEL_PATH}&recursive=true")
check_ok "FileStation.Delete start" "$R"

# ── Step 8: ensure absent ─────────────────────────────────────────────────────
echo ""; echo "  Step 8 — ensure absent: verify ${TEST_FOLDER} is gone"
R=$(api "api=SYNO.FileStation.List&version=2&method=list&folder_path=${PARENT_ENC}")
GONE=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
files=[f['name'] for f in d.get('data',{}).get('files',[])]
print('1' if '${TEST_FOLDER}' not in files else '0')" 2>/dev/null || echo "0")
[[ "$GONE" == "1" ]] \
    && step 1 "ensure absent — ${TEST_FOLDER} no longer in parent listing" \
    || step 0 "ensure absent — ${TEST_FOLDER} still present after delete"

echo ""
echo "────────────────────────────────────────────────────────────"
echo "  TOTAL: $((PASS+FAIL+WARN))   ${PASS_SYM} ${PASS}   ${WARN_SYM} ${WARN}   ${FAIL_SYM} ${FAIL}"
echo "────────────────────────────────────────────────────────────"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
