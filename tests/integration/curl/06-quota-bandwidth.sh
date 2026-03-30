#!/usr/bin/env bash
# 06-quota-bandwidth.sh — Validate SYNO.Core.Quota + SYNO.Core.BandwidthControl
#                          (lib: QuotaManager + BandwidthManager)
#
# Tests:
#   Quota:
#     - get group quota (administrators)
#     - get user quota  (API_USER)
#   Bandwidth:
#     - get group limit (administrators)
#     - get user limit  (API_USER)
#
# Payloads confirmed via Chrome DevTools F12 on DSM 7.1.1-42962 Update 9.
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=BySyst3ms_
#   bash tests/integration/curl/06-quota-bandwidth.sh

set -euo pipefail

export NAS_HOST="${NAS_HOST:?NAS_HOST not set}"
export NAS_PORT="${NAS_PORT:-5001}"
export API_USER="${API_USER:?API_USER not set}"
export API_PASS="${API_PASS:?API_PASS not set}"
export BASE="https://${NAS_HOST}:${NAS_PORT}/webapi/entry.cgi"

PASS_SYM="✅"; FAIL_SYM="❌"; WARN_SYM="⚠️"
PASS=0; FAIL=0; WARN=0

step() { local ok="$1" label="$2" detail="${3:-}"
    if [[ "$ok" == "1" ]]; then echo "  ${PASS_SYM}  ${label}${detail:+ — $detail}"; PASS=$((PASS+1))
    elif [[ "$ok" == "warn" ]]; then echo "  ${WARN_SYM}  ${label}${detail:+ — $detail}"; WARN=$((WARN+1))
    else                              echo "  ${FAIL_SYM}  ${label}${detail:+ — $detail}"; FAIL=$((FAIL+1)); fi
}

api() {
    curl -sk -X POST "${BASE}" \
        --data "_sid=${SID}" \
        --data "$1" \
        -H "X-SYNO-TOKEN: ${TOKEN}"
}

check() { local label="$1" resp="$2"
    OK=$(echo "$resp" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
    step "$OK" "$label"
}

echo "════════════════════════════════════════════════════════════"
echo "  06-quota-bandwidth.sh — SYNO.Core.Quota + BandwidthControl"
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

# ── Section 1: Quota ──────────────────────────────────────────────────────────
echo ""
echo "  ── Quota ────────────────────────────────────────────────"

# Step 1: group quota
echo ""
echo "  Step 1 — SYNO.Core.Quota get (group: administrators)"
R=$(api "api=SYNO.Core.Quota&version=1&method=get&name=administrators&subject_type=group&support_share_quota=true")
OK=$(echo "$R" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
USAGE=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('usage','?'))" 2>/dev/null || echo "?")
QUOTA=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('quota','?'))" 2>/dev/null || echo "?")
step "$OK" "SYNO.Core.Quota get (group)" "usage=${USAGE} MB, quota=${QUOTA} MB (0=unlimited)"

# Step 2: user quota
echo ""
echo "  Step 2 — SYNO.Core.Quota get (user: ${API_USER})"
R=$(api "api=SYNO.Core.Quota&version=1&method=get&name=${API_USER}&subject_type=user&support_share_quota=true")
OK=$(echo "$R" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
USAGE=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('usage','?'))" 2>/dev/null || echo "?")
step "$OK" "SYNO.Core.Quota get (user)" "usage=${USAGE} MB"

# ── Section 2: Bandwidth ──────────────────────────────────────────────────────
echo ""
echo "  ── Bandwidth Control ────────────────────────────────────"

# Step 3: group bandwidth
echo ""
echo "  Step 3 — SYNO.Core.BandwidthControl get (group: administrators)"
R=$(api "api=SYNO.Core.BandwidthControl&version=2&method=get&name=administrators&owner_type=local_group")
OK=$(echo "$R" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
UP=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('upload_limit','?'))" 2>/dev/null || echo "?")
DN=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('download_limit','?'))" 2>/dev/null || echo "?")
step "$OK" "SYNO.Core.BandwidthControl get (group)" "up=${UP} KB/s  down=${DN} KB/s (0=unlimited)"

# Step 4: user bandwidth
echo ""
echo "  Step 4 — SYNO.Core.BandwidthControl get (user: ${API_USER})"
R=$(api "api=SYNO.Core.BandwidthControl&version=2&method=get&name=${API_USER}&owner_type=local_user")
OK=$(echo "$R" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
UP=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('upload_limit','?'))" 2>/dev/null || echo "?")
DN=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('download_limit','?'))" 2>/dev/null || echo "?")
step "$OK" "SYNO.Core.BandwidthControl get (user)" "up=${UP} KB/s  down=${DN} KB/s"

# ── Bandwidth write ───────────────────────────────────────────────────────────
echo ""
echo "  ── Bandwidth write (set + restore) ────────────────────────"

# Step 5: set a limit for API_USER on FileStation
echo ""
echo "  Step 5 — BandwidthControl.Protocol set (user: ${API_USER}, FileStation enabled)"
SET=$(api "api=SYNO.Core.BandwidthControl.Protocol&version=1&method=set&owner_type=local_user&owner=${API_USER}&protocol=FileStation&policy=enabled&upload_limit_1=500&download_limit_1=5000")
check "set_user FileStation enabled" "$SET"

# Step 6: restore to disabled
echo ""
echo "  Step 6 — BandwidthControl.Protocol set (user: ${API_USER}, FileStation restore disabled)"
RESTORE=$(api "api=SYNO.Core.BandwidthControl.Protocol&version=1&method=set&owner_type=local_user&owner=${API_USER}&protocol=FileStation&policy=disabled&upload_limit_1=0&download_limit_1=0")
check "set_user FileStation restore disabled" "$RESTORE"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────"
echo "  Total: $((PASS+FAIL+WARN))  |  ${PASS_SYM} ${PASS}  |  ${WARN_SYM} ${WARN}  |  ${FAIL_SYM} ${FAIL}"

curl -sk -X POST "${BASE}" \
    --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true

[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
