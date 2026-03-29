#!/usr/bin/env bash
# 05-storage.sh — Validate SYNO.Core.Storage.Volume API (lib: StorageManager)
#
# Tests:
#   - list volumes (include_cold_storage, location=internal)
#   - verify at least one volume present
#   - verify expected fields: id, status, size_total_byte, fs_type
#
# Payload confirmed via Chrome DevTools F12 on DSM 7.1.1-42962 Update 9.
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=BySyst3ms_
#   bash tests/integration/curl/05-storage.sh

set -euo pipefail

export NAS_HOST="${NAS_HOST:?NAS_HOST not set}"
export NAS_PORT="${NAS_PORT:-5001}"
export API_USER="${API_USER:?API_USER not set}"
export API_PASS="${API_PASS:?API_PASS not set}"
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
        --data "X-SYNO-TOKEN=${TOKEN}" \
        --data "$1"
}

echo "════════════════════════════════════════════════════════════"
echo "  05-storage.sh — SYNO.Core.Storage.Volume"
echo "  Target: ${BASE}"
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

# ── Step 1: list volumes ───────────────────────────────────────────────────────
echo ""
echo "  Step 1 — list volumes (include_cold_storage, location=internal)"
R=$(api "api=SYNO.Core.Storage.Volume&version=1&method=list&offset=0&limit=-1&option=include_cold_storage&location=internal")
OK=$(echo "$R" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
COUNT=$(echo "$R" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('volumes',[])))" 2>/dev/null || echo "0")
step "$OK" "SYNO.Core.Storage.Volume list" "success=${OK}, volumes=${COUNT}"

# ── Step 2: verify at least one volume ────────────────────────────────────────
echo ""
echo "  Step 2 — verify volume count > 0"
[[ "$COUNT" -gt 0 ]] && step 1 "Volume count ${COUNT} > 0" || step 0 "No volumes returned"

# ── Step 3: verify expected fields ────────────────────────────────────────────
echo ""
echo "  Step 3 — verify fields: id, status, size_total_byte, fs_type"
FIELDS_OK=$(echo "$R" | python3 -c "
import sys, json
d = json.load(sys.stdin)
vols = d.get('data', {}).get('volumes', [])
if not vols:
    print('0')
    sys.exit()
v = vols[0]
required = ['id', 'status', 'size_total_byte', 'fs_type']
missing = [f for f in required if f not in v]
print('0' if missing else '1')
print(','.join(missing) if missing else 'all present')
" 2>/dev/null | head -1 || echo "0")
MISSING=$(echo "$R" | python3 -c "
import sys, json
d = json.load(sys.stdin)
vols = d.get('data', {}).get('volumes', [])
if not vols: print('no volumes'); sys.exit()
v = vols[0]
required = ['id', 'status', 'size_total_byte', 'fs_type']
missing = [f for f in required if f not in v]
print(','.join(missing) if missing else 'all present')
" 2>/dev/null || echo "")
step "$FIELDS_OK" "Volume fields" "${MISSING}"

# ── Step 4: display volumes ────────────────────────────────────────────────────
echo ""
echo "  Step 4 — volume summary"
echo "$R" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for v in d.get('data', {}).get('volumes', []):
    total_gb = v.get('size_total_byte', 0) / 1024**3
    used_gb  = v.get('size_used_byte', 0)  / 1024**3
    print(f\"    {v.get('id','?'):12s}  {v.get('status','?'):10s}  {used_gb:.1f}/{total_gb:.1f} GB  {v.get('fs_type','?')}\")
" 2>/dev/null || true
step 1 "Volume summary displayed"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────"
echo "  Total: $((PASS+FAIL))  |  ${PASS_SYM} ${PASS}  |  ${FAIL_SYM} ${FAIL}"

# Logout
curl -sk -X POST "${BASE}" \
    --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true

[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
