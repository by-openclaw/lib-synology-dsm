#!/usr/bin/env bash
# 03-shares.sh — Validate SYNO.Core.Share + NFS API (lib: ShareManager + NFSManager)
#
# Tests:
#   - Share: list / create / ensure present / set user permission /
#             set group permission / delete / ensure absent
#   - NFS:   set rule (rw) / verify present / update (ro) / delete / verify absent
#
# Usage:
#   export NAS_HOST=10.6.224.6 API_USER=rune-api API_PASS=<REDACTED:password>
#   export NFS_CLIENT=10.6.224.0/20     # CIDR for NFS rule
#   export SHARE_USER=rune-api          # DSM user to assign to share
#   export SHARE_GROUP=svc-automation   # DSM group to assign to share
#   bash tests/integration/curl/03-shares.sh

set -euo pipefail

export NAS_HOST="${NAS_HOST:?NAS_HOST not set}"
export NAS_PORT="${NAS_PORT:-5001}"
export API_USER="${API_USER:?API_USER not set}"
export API_PASS="${API_PASS:?API_PASS not set}"
export NFS_CLIENT="${NFS_CLIENT:-10.6.224.0/20}"
export SHARE_USER="${SHARE_USER:-${API_USER}}"
export SHARE_GROUP="${SHARE_GROUP:-svc-automation}"
export BASE="https://${NAS_HOST}:${NAS_PORT}/webapi/entry.cgi"

RUN_ID=$(head -c4 /dev/urandom | xxd -p)
TEST_SHARE="rune-s-${RUN_ID}"

PASS_SYM="✅"; FAIL_SYM="❌"; WARN_SYM="⚠️"
PASS=0; FAIL=0; WARN=0

step()  { local ok="$1" label="$2" detail="${3:-}"
    if [[ "$ok" == "1" ]]; then echo "  ${PASS_SYM}  ${label}${detail:+ — $detail}"; PASS=$((PASS+1))
    else                         echo "  ${FAIL_SYM}  ${label}${detail:+ — $detail}"; FAIL=$((FAIL+1)); fi; }
warn()  { echo "  ${WARN_SYM}  $1${2:+ — $2}"; WARN=$((WARN+1)); }
api()   { curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" --data "_sid=${SID}&$*"; }
compound() {
    curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
        --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
        --data-urlencode "compound=$1"
}
LAST_OK=0
check_ok() { local label="$1" resp="$2"
    LAST_OK=$(echo "$resp" | python3 -c "import sys,json; print('1' if json.load(sys.stdin).get('success') else '0')" 2>/dev/null || echo "0")
    local detail; detail=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','') or '')" 2>/dev/null || echo "")
    [[ "$LAST_OK" == "1" ]] && step 1 "$label" || step 0 "$label" "$detail"; }
check_compound() { local label="$1" resp="$2"
    local ok=$(echo "$resp" | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('1' if d.get('success') and not d.get('data',{}).get('has_fail') else '0')" 2>/dev/null || echo "0")
    local detail=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','') or d.get('data',{}).get('result',''))" 2>/dev/null || echo "$resp")
    [[ "$ok" == "1" ]] && step 1 "$label" || step 0 "$label" "$detail"; }

echo "════════════════════════════════════════════════════════════"
echo "  03-shares.sh — SYNO.Core.Share + NFS (ShareManager + NFSManager)"
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
    api "api=SYNO.Core.Share&version=1&method=delete&name=${TEST_SHARE}" > /dev/null 2>&1 || true
    [[ "${OWNS_SESSION:-0}" == "1" ]] && \
        curl -sk "${BASE}" --data "api=SYNO.API.Auth&version=1&method=logout&_sid=${SID}" > /dev/null 2>&1 || true
}
trap cleanup EXIT

SHAREINFO_BASE='{"name":"'"${TEST_SHARE}"'","vol_path":"/volume1","desc":"","encryption":false,"enc_passwd":""}'

# ── Step 1: list shares ───────────────────────────────────────────────────────
echo ""; echo "  Step 1 — list all shares"
R=$(api "api=SYNO.Core.Share&version=1&method=list")
COUNT=$(echo "$R" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',{}).get('shares',[])))" 2>/dev/null || echo "?")
check_ok "SYNO.Core.Share list" "$R"
[[ "$COUNT" != "?" ]] && echo "       ${COUNT} shares found"

# ── Step 2: create share ──────────────────────────────────────────────────────
echo ""; echo "  Step 2 — create share: ${TEST_SHARE}"
R=$(curl -sk "${BASE}" -H "X-SYNO-TOKEN: ${TOKEN}" \
    --data "_sid=${SID}&api=SYNO.Core.Share&version=1&method=create&name=${TEST_SHARE}" \
    --data-urlencode "shareinfo={\"name\":\"${TEST_SHARE}\",\"vol_path\":\"/volume1\",\"desc\":\"\",\"name_org\":\"\"}")
check_ok "SYNO.Core.Share create" "$R"

# ── Step 3: ensure present ────────────────────────────────────────────────────
echo ""; echo "  Step 3 — ensure present: verify ${TEST_SHARE} in list"
R=$(api "api=SYNO.Core.Share&version=1&method=list")
FOUND=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
shares=[s['name'] for s in d.get('data',{}).get('shares',[])]
print('1' if '${TEST_SHARE}' in shares else '0')" 2>/dev/null || echo "0")
[[ "$FOUND" == "1" ]] \
    && step 1 "ensure present — ${TEST_SHARE} in share list" \
    || step 0 "ensure present — ${TEST_SHARE} NOT found in list"

# ── Step 4: set user permission ───────────────────────────────────────────────
echo ""; echo "  Step 4 — set user permission: ${SHARE_USER} rw on ${TEST_SHARE}"
R=$(compound '[
  {"api":"SYNO.Core.Share.Permission","method":"set","version":1,"name":"'"${TEST_SHARE}"'","user_group_type":"local_user","permissions":[{"name":"'"${SHARE_USER}"'","is_readonly":false,"is_writable":true,"is_deny":false,"is_custom":false}]},
  {"api":"SYNO.Core.Share","method":"set","version":1,"name":"'"${TEST_SHARE}"'","shareinfo":'"${SHAREINFO_BASE}"'}
]')
check_compound "SYNO.Core.Share.Permission set (user ${SHARE_USER} rw)" "$R"

# ── Step 5: set group permission ──────────────────────────────────────────────
echo ""; echo "  Step 5 — set group permission: ${SHARE_GROUP} rw on ${TEST_SHARE}"
R=$(compound '[
  {"api":"SYNO.Core.Share.Permission","method":"set","version":1,"name":"'"${TEST_SHARE}"'","user_group_type":"local_group","permissions":[{"name":"'"${SHARE_GROUP}"'","is_readonly":false,"is_writable":true,"is_deny":false,"is_custom":false}]},
  {"api":"SYNO.Core.Share","method":"set","version":1,"name":"'"${TEST_SHARE}"'","shareinfo":'"${SHAREINFO_BASE}"'}
]')
check_compound "SYNO.Core.Share.Permission set (group ${SHARE_GROUP} rw)" "$R"

# ── Step 6: NFS rule — add rw ─────────────────────────────────────────────────
echo ""; echo "  Step 6 — NFS rule: add ${NFS_CLIENT} rw → ${TEST_SHARE}"
R=$(compound '[
  {"api":"SYNO.Core.FileServ.NFS.SharePrivilege","method":"save","version":1,"share_name":"'"${TEST_SHARE}"'","rule":[{"client":"'"${NFS_CLIENT}"'","privilege":"rw","root_squash":"root","async":true,"insecure":false,"crossmnt":false,"security_flavor":{"kerberos":false,"kerberos_integrity":false,"kerberos_privacy":false,"sys":true}}]},
  {"api":"SYNO.Core.Share","method":"set","version":1,"name":"'"${TEST_SHARE}"'","shareinfo":'"${SHAREINFO_BASE}"'}
]')
check_compound "NFS rule add (${NFS_CLIENT} rw)" "$R"

# ── Step 7: NFS rule — verify present ─────────────────────────────────────────
echo ""; echo "  Step 7 — NFS rule ensure present: verify ${NFS_CLIENT} in rules"
R=$(api "api=SYNO.Core.FileServ.NFS.SharePrivilege&version=1&method=load&share_name=${TEST_SHARE}")
FOUND=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
rules=d.get('data',{}).get('rule',[])
print('1' if any(r.get('client')=='${NFS_CLIENT}' for r in rules) else '0')" 2>/dev/null || echo "0")
[[ "$FOUND" == "1" ]] \
    && step 1 "NFS ensure present — ${NFS_CLIENT} in rules" \
    || step 0 "NFS ensure present — ${NFS_CLIENT} NOT found in rules"

# ── Step 8: NFS rule — update rw → ro ─────────────────────────────────────────
echo ""; echo "  Step 8 — NFS rule update: ${NFS_CLIENT} rw → ro"
R=$(compound '[
  {"api":"SYNO.Core.FileServ.NFS.SharePrivilege","method":"save","version":1,"share_name":"'"${TEST_SHARE}"'","rule":[{"client":"'"${NFS_CLIENT}"'","privilege":"ro","root_squash":"root","async":true,"insecure":false,"crossmnt":false,"security_flavor":{"kerberos":false,"kerberos_integrity":false,"kerberos_privacy":false,"sys":true}}]},
  {"api":"SYNO.Core.Share","method":"set","version":1,"name":"'"${TEST_SHARE}"'","shareinfo":'"${SHAREINFO_BASE}"'}
]')
check_compound "NFS rule update (${NFS_CLIENT} rw → ro)" "$R"

R=$(api "api=SYNO.Core.FileServ.NFS.SharePrivilege&version=1&method=load&share_name=${TEST_SHARE}")
PRIV=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
rules=d.get('data',{}).get('rule',[])
match=[r for r in rules if r.get('client')=='${NFS_CLIENT}']
print(match[0].get('privilege','?') if match else 'NOT_FOUND')" 2>/dev/null || echo "?")
[[ "$PRIV" == "ro" ]] \
    && step 1 "NFS verify update — privilege is now ro" \
    || step 0 "NFS verify update — expected ro, got ${PRIV}"

# ── Step 9: NFS rule — remove ─────────────────────────────────────────────────
echo ""; echo "  Step 9 — NFS rule remove: ${NFS_CLIENT}"
R=$(compound '[
  {"api":"SYNO.Core.FileServ.NFS.SharePrivilege","method":"save","version":1,"share_name":"'"${TEST_SHARE}"'","rule":[]},
  {"api":"SYNO.Core.Share","method":"set","version":1,"name":"'"${TEST_SHARE}"'","shareinfo":'"${SHAREINFO_BASE}"'}
]')
check_compound "NFS rule remove" "$R"

R=$(api "api=SYNO.Core.FileServ.NFS.SharePrivilege&version=1&method=load&share_name=${TEST_SHARE}")
GONE=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
rules=d.get('data',{}).get('rule',[])
print('1' if not any(r.get('client')=='${NFS_CLIENT}' for r in rules) else '0')" 2>/dev/null || echo "0")
[[ "$GONE" == "1" ]] \
    && step 1 "NFS ensure absent — ${NFS_CLIENT} rule removed" \
    || step 0 "NFS ensure absent — ${NFS_CLIENT} still present"

# ── Step 10: delete share ─────────────────────────────────────────────────────
echo ""; echo "  Step 10 — delete share: ${TEST_SHARE}"
R=$(api "api=SYNO.Core.Share&version=1&method=delete&name=${TEST_SHARE}")
check_ok "SYNO.Core.Share delete" "$R"

# ── Step 11: ensure absent ────────────────────────────────────────────────────
echo ""; echo "  Step 11 — ensure absent: verify ${TEST_SHARE} is gone"
R=$(api "api=SYNO.Core.Share&version=1&method=list")
GONE=$(echo "$R" | python3 -c "
import sys,json; d=json.load(sys.stdin)
shares=[s['name'] for s in d.get('data',{}).get('shares',[])]
print('1' if '${TEST_SHARE}' not in shares else '0')" 2>/dev/null || echo "0")
[[ "$GONE" == "1" ]] \
    && step 1 "ensure absent — ${TEST_SHARE} no longer in list" \
    || step 0 "ensure absent — ${TEST_SHARE} still present after delete"

echo ""
echo "────────────────────────────────────────────────────────────"
echo "  TOTAL: $((PASS+FAIL+WARN))   ${PASS_SYM} ${PASS}   ${WARN_SYM} ${WARN}   ${FAIL_SYM} ${FAIL}"
echo "────────────────────────────────────────────────────────────"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
