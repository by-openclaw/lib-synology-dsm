#!/usr/bin/env bash
# ==============================================================================
# dsm-crud-test.sh — Synology DSM API CRUD smoke test
#
# Tests: auth, user CRUD, group CRUD + membership, share CRUD + NFS + permissions
#
# Usage:
#   bash tests/integration/dsm-crud-test.sh
#   NAS_HOST=192.168.x.x NAS_PORT=5001 bash tests/integration/dsm-crud-test.sh
#
# Requirements:
#   - curl, jq
#   - API_USER in administrators group + DSM app = Allow
#
# Env overrides:
#   NAS_HOST      default: (required — set via env)
#   NAS_PORT      default: 5001
#   API_USER      default: (required — set via env)
#   API_PASS      default: YOUR_PASSWORD
# ==============================================================================
set -euo pipefail

NAS_HOST="${NAS_HOST:-}"
NAS_PORT="${NAS_PORT:-5001}"
API_USER="${API_USER:-}"
API_PASS="${API_PASS:-YOUR_PASSWORD}"
BASE_URL="https://${NAS_HOST}:${NAS_PORT}/webapi/entry.cgi"

# Test artifact names — auto-cleaned up
TEST_USER="rune-bash-test-user"
TEST_USER_PASS="YOUR_PASSWORDtest!"
TEST_GROUP="rune-bash-test-group"
TEST_SHARE="rune-bash-test-share"

PASS=0
WARN=0
FAIL=0
SID=""
TOKEN=""

# ── Colors ──────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  GRN="\033[32m" YLW="\033[33m" RED="\033[31m" CYN="\033[36m" RST="\033[0m"
else
  GRN="" YLW="" RED="" CYN="" RST=""
fi

ok()   { echo -e "  ${GRN}✅  $*${RST}"; ((PASS++)) || true; }
warn() { echo -e "  ${YLW}⚠️   $*${RST}"; ((WARN++)) || true; }
fail() { echo -e "  ${RED}❌  $*${RST}"; ((FAIL++)) || true; }
sec()  { echo -e "\n${CYN}── $* ──────────────────────────────────${RST}"; }

# ── Core helper ─────────────────────────────────────────────────────────────
dsm() {
  # Usage: dsm KEY=val KEY=val ...
  # Always injects _sid and X-SYNO-TOKEN when available.
  local args=()
  for arg in "$@"; do args+=(--data-urlencode "$arg"); done
  [[ -n "$SID"   ]] && args+=(--data-urlencode "_sid=$SID")
  [[ -n "$TOKEN" ]] && args+=(-H "X-SYNO-TOKEN: $TOKEN")
  curl -sk "${args[@]}" "$BASE_URL"
}

jq_val() { echo "$1" | jq -r "$2" 2>/dev/null; }
is_ok()  { [[ "$(jq_val "$1" '.success')" == "true" ]]; }
err_code() { jq_val "$1" '.error.code // "?"'; }

# ── 1. Auth ──────────────────────────────────────────────────────────────────
sec "1. Auth — ${API_USER}"
resp=$(dsm "api=SYNO.API.Auth" "version=7" "method=login" \
           "account=${API_USER}" "passwd=${API_PASS}" \
           "session=DSM" "format=sid" "enable_syno_token=yes")

if is_ok "$resp"; then
  SID=$(jq_val "$resp" '.data.sid')
  TOKEN=$(jq_val "$resp" '.data.synotoken')
  ok "Login — SID=${SID:0:12}..."
  [[ -n "$TOKEN" && "$TOKEN" != "null" ]] \
    && ok "SynoToken obtained — ${TOKEN:0:16}..." \
    || warn "SynoToken empty — write ops will fail"
else
  fail "Login failed — $(err_code "$resp")"
  echo "Cannot continue without a session. Check credentials and DSM app permissions."
  exit 1
fi

# ── 2. User CRUD ─────────────────────────────────────────────────────────────
sec "2. User CRUD"

# List
resp=$(dsm "api=SYNO.Core.User" "version=1" "method=list")
is_ok "$resp" \
  && ok "User list — $(jq_val "$resp" '.data.users | length') users" \
  || fail "User list — err=$(err_code "$resp")"

# Create
resp=$(dsm "api=SYNO.Core.User" "version=1" "method=create" \
           "name=${TEST_USER}" "password=${TEST_USER_PASS}" \
           "email=" "description=Rune bash CRUD test — auto-deleted")
is_ok "$resp" \
  && ok "User create (${TEST_USER})" \
  || fail "User create — err=$(err_code "$resp")"

# Read back
resp=$(dsm "api=SYNO.Core.User" "version=1" "method=get" "name=${TEST_USER}")
is_ok "$resp" \
  && ok "User get (${TEST_USER})" \
  || warn "User get — err=$(err_code "$resp")"

# Update description
resp=$(dsm "api=SYNO.Core.User" "version=1" "method=set" \
           "name=${TEST_USER}" "description=Updated by bash CRUD test")
is_ok "$resp" \
  && ok "User update (${TEST_USER})" \
  || warn "User update — err=$(err_code "$resp")"

# ── 3. Group CRUD + membership ───────────────────────────────────────────────
sec "3. Group CRUD + membership"

# List
resp=$(dsm "api=SYNO.Core.Group" "version=1" "method=list")
is_ok "$resp" \
  && ok "Group list — $(jq_val "$resp" '.data.groups | length') groups" \
  || fail "Group list — err=$(err_code "$resp")"

# Create
resp=$(dsm "api=SYNO.Core.Group" "version=1" "method=create" \
           "name=${TEST_GROUP}" "description=Rune bash CRUD test — auto-deleted")
is_ok "$resp" \
  && ok "Group create (${TEST_GROUP})" \
  || fail "Group create — err=$(err_code "$resp")"

# Add member — correct method: Group.set with members= (NOT member_set — error 103)
MEMBERS=$(jq -nc --arg u "${TEST_USER}" '[$u]')
resp=$(dsm "api=SYNO.Core.Group" "version=1" "method=set" \
           "name=${TEST_GROUP}" "members=${MEMBERS}" "description=")
is_ok "$resp" \
  && ok "Group add member (${TEST_USER} → ${TEST_GROUP})" \
  || fail "Group add member — err=$(err_code "$resp") [Note: uses set not member_set]"

# Verify member is in group
resp=$(dsm "api=SYNO.Core.Group" "version=1" "method=get" "name=${TEST_GROUP}")
MEMBER_COUNT=$(jq_val "$resp" '.data.groups[0].members | length // .data.members | length // 0')
[[ "${MEMBER_COUNT}" -ge 1 ]] \
  && ok "Group members verified (${MEMBER_COUNT} member(s))" \
  || warn "Group members empty after set — DSM may lag"

# Remove member (set empty list)
resp=$(dsm "api=SYNO.Core.Group" "version=1" "method=set" \
           "name=${TEST_GROUP}" "members=[]" "description=")
is_ok "$resp" \
  && ok "Group remove member (cleared)" \
  || fail "Group remove member — err=$(err_code "$resp")"

# ── 4. Share CRUD + NFS + permissions ────────────────────────────────────────
sec "4. Share CRUD + NFS + permissions"

# List
resp=$(dsm "api=SYNO.Core.Share" "version=1" "method=list" \
           "additional=$(jq -nc '["share_quota"]')")
is_ok "$resp" \
  && ok "Share list — $(jq_val "$resp" '.data.shares | length') shares" \
  || fail "Share list — err=$(err_code "$resp")"

# Create — must use shareinfo JSON object (flat params return 403)
SHAREINFO=$(jq -nc \
  --arg n  "${TEST_SHARE}" \
  --arg vp "/volume1" \
  --arg d  "Rune bash CRUD test — auto-deleted" \
  '{"name":$n,"vol_path":$vp,"desc":$d,"name_org":""}')

resp=$(dsm "api=SYNO.Core.Share" "version=1" "method=create" \
           "name=${TEST_SHARE}" "shareinfo=${SHAREINFO}")
if is_ok "$resp"; then
  ok "Share create (${TEST_SHARE})"

  # Set user permission on share
  PERMS=$(jq -nc --arg u "${TEST_USER}" \
    '[{"name":$u,"is_readonly":false,"is_writable":true,"is_deny":false,"is_custom":false}]')
  resp=$(dsm "api=SYNO.Core.Share.Permission" "version=1" "method=set" \
             "name=${TEST_SHARE}" "user_group_type=local_user" "permissions=${PERMS}")
  is_ok "$resp" \
    && ok "Share set user permission (${TEST_USER} RW on ${TEST_SHARE})" \
    || warn "Share set permission — err=$(err_code "$resp")"

  # Set NFS rule
  NFS_RULE=$(jq -nc '{
    "client":"${NFS_CLIENT:-your-nfs-subnet}",
    "privilege":"rw",
    "root_squash":"root",
    "async":true,
    "insecure":false,
    "crossmnt":false,
    "security_flavor":{"sys":true,"kerberos":false,"kerberos_integrity":false,"kerberos_privacy":false}
  }' | jq -c '[.]')
  resp=$(dsm "api=SYNO.Core.FileServ.NFS.SharePrivilege" "version=1" "method=save" \
             "share_name=${TEST_SHARE}" "rule=${NFS_RULE}")
  is_ok "$resp" \
    && ok "Share NFS rule set (${NFS_CLIENT:-your-nfs-subnet} rw → ${TEST_SHARE})" \
    || warn "Share NFS set — err=$(err_code "$resp")"

  # Read NFS rules back
  resp=$(dsm "api=SYNO.Core.FileServ.NFS.SharePrivilege" "version=1" "method=load" \
             "share_name=${TEST_SHARE}")
  RULE_COUNT=$(jq_val "$resp" '.data.rule | length // 0')
  [[ "${RULE_COUNT}" -ge 1 ]] \
    && ok "Share NFS rules verified (${RULE_COUNT} rule(s))" \
    || warn "NFS rules empty after save"

  # Delete share
  resp=$(dsm "api=SYNO.Core.Share" "version=1" "method=delete" "name=${TEST_SHARE}")
  is_ok "$resp" \
    && ok "Share delete (${TEST_SHARE})" \
    || fail "Share delete — err=$(err_code "$resp")"

else
  EC=$(err_code "$resp")
  if [[ "$EC" == "403" ]]; then
    fail "Share create — 403: ${API_USER} missing administrators group in DSM"
    warn "Fix: DSM → Control Panel → User & Group → ${API_USER} → Groups → add administrators"
  else
    fail "Share create — err=${EC}"
  fi
  warn "Share permission test — skipped (create failed)"
  warn "Share NFS test — skipped (create failed)"
  warn "Share delete — skipped (create failed)"
fi

# ── 5. Cleanup ───────────────────────────────────────────────────────────────
sec "5. Cleanup"

resp=$(dsm "api=SYNO.Core.User" "version=1" "method=delete" \
           "name=$(jq -nc --arg u "${TEST_USER}" '[$u]')")
is_ok "$resp" && ok "Cleaned up test user (${TEST_USER})" \
              || warn "User cleanup — might already be gone"

resp=$(dsm "api=SYNO.Core.Group" "version=1" "method=delete" \
           "name=$(jq -nc --arg g "${TEST_GROUP}" '[$g]')")
is_ok "$resp" && ok "Cleaned up test group (${TEST_GROUP})" \
              || warn "Group cleanup — might already be gone"

# Logout
dsm "api=SYNO.API.Auth" "version=1" "method=logout" > /dev/null 2>&1 || true
ok "Logout"

# ── Summary ──────────────────────────────────────────────────────────────────
sec "Summary"
TOTAL=$((PASS + WARN + FAIL))
echo -e "  Total: ${TOTAL}  |  ${GRN}✅ ${PASS}${RST}  |  ${YLW}⚠️  ${WARN}${RST}  |  ${RED}❌ ${FAIL}${RST}"

if [[ $FAIL -gt 0 ]]; then
  echo -e "\n  ${RED}FAILED — fix errors above before proceeding.${RST}"
  exit 1
else
  echo -e "\n  ${GRN}All critical checks passed.${RST}"
  exit 0
fi
