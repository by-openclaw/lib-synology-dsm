#!/usr/bin/env bash
# 08-trafficcontrol.sh — Validate SYNO.Core.Network.TrafficControl.Rules
#                          (lib: TrafficControlManager)
#
# Tests:
#   - Load rules (adapter: ovs_bond0)
#   - Clear rules
#   - Verify empty after clear
#   - Add one NFS rule
#   - Verify rule count = 1
#   - Clear rules (cleanup)
#   - Verify empty after cleanup
#
# Payloads confirmed via Chrome DevTools F12 on DSM 7.1.1-42962 Update 9.
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=<REDACTED:password>
#   bash tests/integration/curl/08-trafficcontrol.sh

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
echo "  08-trafficcontrol.sh — SYNO.Core.Network.TrafficControl.Rules"
echo "  Target: ${BASE}"
echo "════════════════════════════════════════════════════════════"

ADAPTER="ovs_bond0"

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

# ── Step 1: Load rules ───────────────────────────────────────────────────────
echo ""
echo "  Step 1 — TrafficControl.Rule load (adapter: ${ADAPTER})"
R=$(api "api=SYNO.Core.Network.TrafficControl.Rules&version=1&method=load&adapter=${ADAPTER}")
check "load rules" "$R"
INITIAL_COUNT=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',{}).get('rules',[])))" 2>/dev/null || echo "?")
echo "    (initial rule count: ${INITIAL_COUNT})"

# ── Step 2: Clear rules ──────────────────────────────────────────────────────
echo ""
echo "  Step 2 — TrafficControl.Rule save (clear all, adapter: ${ADAPTER})"
R=$(api "api=SYNO.Core.Network.TrafficControl.Rules&version=1&method=save&adapter=${ADAPTER}&rules=[]")
check "clear rules" "$R"

# ── Step 3: Verify empty after clear ──────────────────────────────────────────
echo ""
echo "  Step 3 — Verify empty after clear"
R=$(api "api=SYNO.Core.Network.TrafficControl.Rules&version=1&method=load&adapter=${ADAPTER}")
COUNT=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',{}).get('rules',[])))" 2>/dev/null || echo "?")
[[ "$COUNT" == "0" ]] && step 1 "rule count = 0 after clear" || step 0 "rule count = 0 after clear" "got ${COUNT}"

# ── Step 4: Add one NFS rule ─────────────────────────────────────────────────
echo ""
echo "  Step 4 — TrafficControl.Rule save (add NFS rule)"
RULE='[{"enabled":true,"port_type":"SYS","port_num":"nfs","port_direction":"src","protocol":"all","minrate":500,"maxrate":1000,"source":"all","ip_direction":"dest"}]'
R=$(api "api=SYNO.Core.Network.TrafficControl.Rules&version=1&method=save&adapter=${ADAPTER}&rules=${RULE}")
check "add NFS rule" "$R"

# ── Step 5: Verify rule count = 1 ────────────────────────────────────────────
echo ""
echo "  Step 5 — Verify rule count = 1 after add"
R=$(api "api=SYNO.Core.Network.TrafficControl.Rules&version=1&method=load&adapter=${ADAPTER}")
COUNT=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',{}).get('rules',[])))" 2>/dev/null || echo "?")
[[ "$COUNT" == "1" ]] && step 1 "rule count = 1 after add" || step 0 "rule count = 1 after add" "got ${COUNT}"

# ── Step 6: Clear rules (cleanup) ────────────────────────────────────────────
echo ""
echo "  Step 6 — TrafficControl.Rule save (cleanup)"
R=$(api "api=SYNO.Core.Network.TrafficControl.Rules&version=1&method=save&adapter=${ADAPTER}&rules=[]")
check "cleanup rules" "$R"

# ── Step 7: Verify empty after cleanup ────────────────────────────────────────
echo ""
echo "  Step 7 — Verify empty after cleanup"
R=$(api "api=SYNO.Core.Network.TrafficControl.Rules&version=1&method=load&adapter=${ADAPTER}")
COUNT=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',{}).get('rules',[])))" 2>/dev/null || echo "?")
[[ "$COUNT" == "0" ]] && step 1 "rule count = 0 after cleanup" || step 0 "rule count = 0 after cleanup" "got ${COUNT}"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "  ────────────────────────────────────────"
echo "  Total: $((PASS+FAIL+WARN))  |  ${PASS_SYM} ${PASS}  |  ${WARN_SYM} ${WARN}  |  ${FAIL_SYM} ${FAIL}"

curl -sk -X POST "${BASE}" \
    --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true

[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
