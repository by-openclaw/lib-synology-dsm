#!/bin/bash
# ==============================================================================
# dsm-share-reference.sh — Canonical share lifecycle reference script
#
# Source: yboujraf — validated working 2026-03-28 on DS1513+ DSM 7.1.1
# This is the reference implementation for share create → permissions →
# NFS → delete. The Python lib (shares.py) mirrors this exact pattern.
#
# Key patterns validated here:
#   - shareinfo JSON object for create (not flat params)
#   - X-SYNO-TOKEN header on all write ops
#   - SYNO.Entry.Request compound for permissions + Share.set finalize
#   - SYNO.Core.FileServ.NFS.SharePrivilege.save for NFS rules
# ==============================================================================

# ─── CONFIG ───────────────────────────────────────────
SHARE="${TEST_SHARE:-your-test-share}"
USER="${API_USER:-}"
GROUP="svc-automation"
NFS_CLIENT="${NFS_CLIENT:-your-nfs-client}"
HOST="https://${NAS_HOST:-your-nas-host}:5001"

# ─── 1. LOGIN ─────────────────────────────────────────
RESPONSE=$(curl -sk "${HOST}/webapi/entry.cgi" \
  --data "api=SYNO.API.Auth&version=6&method=login\
&account=${API_USER:-your-dsm-user}&passwd=${API_PASS:-YOUR_PASSWORD}\
&session=DSM&format=sid&enable_syno_token=yes")

SID=$(echo $RESPONSE | grep -o '"sid":"[^"]*"' | cut -d'"' -f4)
TOKEN=$(echo $RESPONSE | grep -o '"synotoken":"[^"]*"' | cut -d'"' -f4)
echo "✅ Login — SID: $SID"

# ─── 2. CREATE SHARE ──────────────────────────────────
curl -sk "${HOST}/webapi/entry.cgi" \
  -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Share&version=1&method=create&name=${SHARE}" \
  --data-urlencode "shareinfo={\"name\":\"${SHARE}\",\"vol_path\":\"/volume1\",\"desc\":\"\",\"name_org\":\"\"}"
echo "✅ Share created"

# ─── 3. ASSIGN USER + FINALIZE SHARE ──────────────────
curl -sk "${HOST}/webapi/entry.cgi" \
  -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
  --data-urlencode "compound=[
    {\"api\":\"SYNO.Core.Share.Permission\",\"method\":\"set\",\"version\":1,\"name\":\"${SHARE}\",\"user_group_type\":\"local_user\",\"permissions\":[{\"name\":\"${USER}\",\"is_readonly\":false,\"is_writable\":true,\"is_deny\":false,\"is_custom\":false}]},
    {\"api\":\"SYNO.Core.Share\",\"method\":\"set\",\"version\":1,\"name\":\"${SHARE}\",\"shareinfo\":{\"name\":\"${SHARE}\",\"vol_path\":\"/volume1\",\"desc\":\"\",\"encryption\":false,\"enc_passwd\":\"\"}}
  ]"
echo "✅ User permissions set"

# ─── 4. ASSIGN GROUP PERMISSIONS ──────────────────────
curl -sk "${HOST}/webapi/entry.cgi" \
  -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
  --data-urlencode "compound=[
    {\"api\":\"SYNO.Core.Share.Permission\",\"method\":\"set\",\"version\":1,\"name\":\"${SHARE}\",\"user_group_type\":\"local_group\",\"permissions\":[{\"name\":\"${GROUP}\",\"is_readonly\":false,\"is_writable\":true,\"is_deny\":false,\"is_custom\":false}]},
    {\"api\":\"SYNO.Core.Share\",\"method\":\"set\",\"version\":1,\"name\":\"${SHARE}\",\"shareinfo\":{\"name\":\"${SHARE}\",\"vol_path\":\"/volume1\",\"desc\":\"\",\"encryption\":false,\"enc_passwd\":\"\"}}
  ]"
echo "✅ Group permissions set"

# ─── 5. SET NFS ───────────────────────────────────────
curl -sk "${HOST}/webapi/entry.cgi" \
  -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Entry.Request&method=request&version=1&stop_when_error=true&mode=sequential" \
  --data-urlencode "compound=[
    {\"api\":\"SYNO.Core.FileServ.NFS.SharePrivilege\",\"method\":\"save\",\"version\":1,\"share_name\":\"${SHARE}\",\"rule\":[{\"client\":\"${NFS_CLIENT}\",\"privilege\":\"rw\",\"root_squash\":\"root\",\"async\":true,\"insecure\":false,\"crossmnt\":false,\"security_flavor\":{\"kerberos\":false,\"kerberos_integrity\":false,\"kerberos_privacy\":false,\"sys\":true}}]},
    {\"api\":\"SYNO.Core.Share\",\"method\":\"set\",\"version\":1,\"name\":\"${SHARE}\",\"shareinfo\":{\"name\":\"${SHARE}\",\"vol_path\":\"/volume1\",\"desc\":\"\",\"encryption\":false,\"enc_passwd\":\"\"}}
  ]"
echo "✅ NFS permissions set"

# ─── 6. DELETE SHARE ──────────────────────────────────
curl -sk "${HOST}/webapi/entry.cgi" \
  -H "X-SYNO-TOKEN: ${TOKEN}" \
  --data "_sid=${SID}&api=SYNO.Core.Share&version=1&method=delete&name=${SHARE}"
echo "✅ Share deleted"

# ─── 7. LOGOUT ────────────────────────────────────────
curl -sk "${HOST}/webapi/entry.cgi" \
  --data "api=SYNO.API.Auth&version=6&method=logout&_sid=${SID}"
echo "✅ Logged out"
