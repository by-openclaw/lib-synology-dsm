#!/usr/bin/env python3
"""One-shot: update svc-rune description + email on NAS."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from synology_dsm.client import DSMClient
from synology_dsm.users import UserManager

creds = json.loads(
    Path("/home/by-systems/.openclaw/workspace/infra/secrets/infra-synology-nas.json").read_text()
)["fields"]

c = DSMClient(creds["host"], port=int(creds["port"]), verify_ssl=False)
c.login(creds["svc_rune_username"], creds["svc_rune_password"])
u = UserManager(c)

print("Before:", u.get("svc-rune"))

result = u.update(
    "svc-rune",
    email="github-bot+rune@by-systems.be",
    description="BY-SYSTEMS automation agent — executor, infra ops",
)
print("Update:", result)
print("After: ", u.get("svc-rune"))

print("---")
print("svc-opus:", u.get("svc-opus"))
