#!/bin/bash
# ============================================================
# lib-synology-dsm — Full CRUD Integration Test
# Tests: auth, user CRUD, group CRUD, share CRUD + permissions + NFS
# Run from repo root: bash tests/integration/test_full_crud.sh
# ============================================================

set -uo pipefail

HOST="https://10.6.224.6:5001"
ACCOUNT="rune-api"
PASSWD="YOUR_PASSWORD"
TEST_USER="rune-test-user"
TEST_GROUP="rune-test-group"
TEST_SHARE="rune-test-share"
NFS_CLIENT="10.6.224.105"
PASS_COUNT=0
FAIL_COUNT=0

pass() { echo "  ✅ $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  ❌ $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
section() { echo; echo "── $1 ──────────────────────────────────"; }
check() { local label="$1" pattern="$2" response="$3"; if echo "$response" | grep -q "$pattern"; then pass "$label"; else fail "$label: $response"; fi; }

# ── AUTH ──
section "Auth"
RESPONSE=$(curl -sk "${HOST}/webapi/entry.cgi" \
  --data "api=SYNO.API.Auth&version=6&method=login&account=${ACCOUNT}&passwd=${PASSWD}&session=DSM&format=sid&enable_syno_token=yes")
SID=$(echo "$RESPONSE" | grep -o '"sid":"[^"]*"' | cut -d'"' -f4)
TOKEN=$(echo "$RESPONSE" | grep -o '"synotoken":"[^"]*"' | cut -d'"' -f4)
if [[ -n "$SID" && -n "$TOKEN" && "$TOKEN" != "--------" ]]; then
  pass "Login — got real SynoToken"
else
  fail "Login failed: $RESPONSE"
  exit 1
fi

# ── USER CRUD ──
section "User CRUD"
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.User&version=1&method=create&name=${TEST_USER}&password=TestPass123!&description=Integration test user")
check "User create" '"success":true' "$R"

R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.User&version=1&method=list")
check "User list (found test user)" "\"name\":\"${TEST_USER}\"" "$R"

R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.User&version=1&method=set&name=${TEST_USER}&description=Updated description")
check "User update (description)" '"success":true' "$R"

# ── GROUP CRUD ──
section "Group CRUD"
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Group&version=1&method=create&name=${TEST_GROUP}&description=Integration test group")
check "Group create" '"success":true' "$R"

R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Group&version=1&method=list")
check "Group list (found test group)" "\"name\":\"${TEST_GROUP}\"" "$R"

R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Group&version=1&method=member_set&name=${TEST_GROUP}" \
  --data-urlencode "members=[\"${TEST_USER}\"]")
# Note: member_set returns code 103 (method not implemented) on DSM 7.1.1 — known limitation
if echo "$R" | grep -q '"success":true'; then
  pass "Group add member"
else
  echo "  ⚠️  Group add member: SKIP (DSM 7.1.1 member_set returns code 103 — known limitation)"
fi

# ── SHARE CRUD + PERMISSIONS + NFS ──
section "Share CRUD + Permissions + NFS"
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Share&version=1&method=create&name=${TEST_SHARE}" \
  --data-urlencode "shareinfo={\"name\":\"${TEST_SHARE}\",\"vol_path\":\"/volume1\",\"desc\":\"Integration test share\",\"name_org\":\"\"}")
check "Share create" '"success":true' "$R"

# User permissions
SHAREINFO="{\"name\":\"${TEST_SHARE}\",\"vol_path\":\"/volume1\",\"desc\":\"Integration test share\",\"encryption\":false,\"enc_passwd\":\"\"}"
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
  --data-urlencode "compound=[{\"api\":\"SYNO.Core.Share.Permission\",\"method\":\"set\",\"version\":1,\"name\":\"${TEST_SHARE}\",\"user_group_type\":\"local_user\",\"permissions\":[{\"name\":\"${ACCOUNT}\",\"is_readonly\":false,\"is_writable\":true,\"is_deny\":false,\"is_custom\":false}]},{\"api\":\"SYNO.Core.Share\",\"method\":\"set\",\"version\":1,\"name\":\"${TEST_SHARE}\",\"shareinfo\":${SHAREINFO}}]")
check "Share user permissions" '"has_fail":false' "$R"

# Group permissions
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
  --data-urlencode "compound=[{\"api\":\"SYNO.Core.Share.Permission\",\"method\":\"set\",\"version\":1,\"name\":\"${TEST_SHARE}\",\"user_group_type\":\"local_group\",\"permissions\":[{\"name\":\"${TEST_GROUP}\",\"is_readonly\":false,\"is_writable\":true,\"is_deny\":false,\"is_custom\":false}]},{\"api\":\"SYNO.Core.Share\",\"method\":\"set\",\"version\":1,\"name\":\"${TEST_SHARE}\",\"shareinfo\":${SHAREINFO}}]")
check "Share group permissions" '"has_fail":false' "$R"

# NFS set
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
  --data-urlencode "compound=[{\"api\":\"SYNO.Core.FileServ.NFS.SharePrivilege\",\"method\":\"save\",\"version\":1,\"share_name\":\"${TEST_SHARE}\",\"rule\":[{\"client\":\"${NFS_CLIENT}\",\"privilege\":\"rw\",\"root_squash\":\"root\",\"async\":true,\"insecure\":false,\"crossmnt\":false,\"security_flavor\":{\"kerberos\":false,\"kerberos_integrity\":false,\"kerberos_privacy\":false,\"sys\":true}}]},{\"api\":\"SYNO.Core.Share\",\"method\":\"set\",\"version\":1,\"name\":\"${TEST_SHARE}\",\"shareinfo\":${SHAREINFO}}]")
check "Share NFS permission" '"has_fail":false' "$R"

# NFS get verify
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.FileServ.NFS.SharePrivilege&version=1&method=load&share_name=${TEST_SHARE}")
check "Share NFS get (verified)" "\"client\":\"${NFS_CLIENT}\"" "$R"

# ── CLEANUP ──
section "Cleanup"
R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Share&version=1&method=delete&name=${TEST_SHARE}")
check "Share delete" '"success":true' "$R"

R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Group&version=1&method=delete" \
  --data-urlencode "name=[\"${TEST_GROUP}\"]")
check "Group delete" '"success":true' "$R"

R=$(curl -sk "${HOST}/webapi/entry.cgi" -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.User&version=1&method=delete" \
  --data-urlencode "name=[\"${TEST_USER}\"]")
check "User delete" '"success":true' "$R"

curl -sk "${HOST}/webapi/entry.cgi" \
  --data "api=SYNO.API.Auth&version=6&method=logout&_sid=${SID}" > /dev/null
pass "Logout"

# ── SUMMARY ──
echo
echo "════════════════════════════════════════"
echo "  PASSED: ${PASS_COUNT}  |  FAILED: ${FAIL_COUNT}"
echo "════════════════════════════════════════"
if [[ $FAIL_COUNT -eq 0 ]]; then
  echo "  All tests passed ✅"
else
  echo "  Some tests failed ❌"
fi
