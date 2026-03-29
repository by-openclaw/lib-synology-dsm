"""Unit tests — NFSManager."""

import pytest
from unittest.mock import patch, MagicMock
from synology_dsm.nfs import NFSManager
from synology_dsm import DSMClient


def _make_nfs():
    client = DSMClient("your-nas-host")
    client._sid = "fake-sid"
    client._synotoken = "fake-token"
    return NFSManager(client)


class TestNFSManager:
    def test_get_rules_returns_rule_list(self):
        mgr = _make_nfs()
        payload = {"rule": [{"hostname": "192.168.1.0/24", "privilege": "rw"}]}
        with patch.object(mgr._c, "_post", return_value={"success": True, "data": payload}):
            rules = mgr.get_rules("my-share")
        assert len(rules) == 1
        assert rules[0]["privilege"] == "rw"

    def test_get_rules_empty_when_no_rules(self):
        mgr = _make_nfs()
        with patch.object(mgr._c, "_post", return_value={"success": True, "data": {}}):
            rules = mgr.get_rules("my-share")
        assert rules == []

    def test_get_rules_calls_correct_api(self):
        mgr = _make_nfs()
        captured = {}

        def capture(url, data, headers=None):
            captured.update(data)
            return {"success": True, "data": {"rule": []}}

        with patch.object(mgr._c, "_post", side_effect=capture):
            mgr.get_rules("test-share")

        assert captured["api"] == "SYNO.Core.FileServ.NFS.SharePrivilege"
        assert captured["method"] == "load"
        assert captured["share_name"] == "test-share"
