#!/usr/bin/env bash
# 00-auth.sh — Validate SYNO.API.Auth login / logout
#
# This is the foundation. Every other script sources this.
# Run standalone to verify credentials work before anything else.
#
# Usage:
#   export NAS_HOST=10.6.224.6
#   export API_USER=rune-api
#   export API_PASS=BySyst3ms_
#   bash tests/integration/curl/00-auth.sh
#
# On success: prints SID and TOKEN, exits 0
# On failure: prints error details, exits 1

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
export NAS_HOST="${NAS_HOST:?NAS_HOST not set (e.g. export NAS_HOST=10.6.224.6)}"
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

echo "════════════════════════════════════════════════════════════"
echo "  00-auth.sh — SYNO.API.Auth"
echo "  Target: ${BASE}"
echo "════════════════════════════════════════════════════════════"

# ── Step 1: Login ─────────────────────────────────────────────────────────────
echo ""
echo "  1. Login"
RESP=$(curl -sk "${BASE}" \
    --data "api=SYNO.API.Auth&version=6&method=login" \
    --data-urlencode "account=${API_USER}" \
    --data-urlencode "passwd=${API_PASS}" \
    --data "session=DSM&format=sid&enable_syno_token=yes")

SUCCESS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success','false'))" 2>/dev/null || echo "false")

if [[ "$SUCCESS" == "True" ]] || [[ "$SUCCESS" == "true" ]]; then
    export SID=$(echo "$RESP"   | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['sid'])")
    export TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('synotoken',''))")
    step 1 "Login" "SID=${SID:0:12}… Token=${TOKEN:0:8}…"
else
    ERR=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error','unknown'))" 2>/dev/null || echo "$RESP")
    step 0 "Login FAILED" "$ERR"
    echo ""
    echo "  Common causes:"
    echo "    code 400 = wrong password"
    echo "    code 402 = account disabled in DSM"
    echo "    code 403 = 2FA required"
    exit 1
fi

# ── Step 2: Logout ────────────────────────────────────────────────────────────
echo ""
echo "  2. Logout"
RESP=$(curl -sk "${BASE}" \
    --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}")
OK=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success','false'))" 2>/dev/null || echo "false")
[[ "$OK" == "True" ]] || [[ "$OK" == "true" ]] && step 1 "Logout" || step 0 "Logout" "$RESP"

# ── Step 3: Re-login for use by other scripts ─────────────────────────────────
echo ""
echo "  3. Re-login (for subsequent use)"
RESP=$(curl -sk "${BASE}" \
    --data "api=SYNO.API.Auth&version=6&method=login" \
    --data-urlencode "account=${API_USER}" \
    --data-urlencode "passwd=${API_PASS}" \
    --data "session=DSM&format=sid&enable_syno_token=yes")
export SID=$(echo "$RESP"   | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['sid'])")
export TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('synotoken',''))")
step 1 "Re-login" "SID=${SID:0:12}… Token=${TOKEN:0:8}…"

echo ""
echo "────────────────────────────────────────────────────────────"
echo "  TOTAL: $((PASS+FAIL))   ${PASS_SYM} ${PASS}   ${FAIL_SYM} ${FAIL}"
echo "────────────────────────────────────────────────────────────"
echo ""
echo "  Exported: SID TOKEN BASE (available when sourced)"
echo "  Source this file to reuse the session:"
echo "    source tests/integration/curl/00-auth.sh"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
