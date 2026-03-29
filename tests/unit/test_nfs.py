"""Unit tests — NFSManager."""

from synology_dsm.nfs import NFSManager


def _mgr(mock_client):
    return NFSManager(mock_client)


class TestNFSManager:
    def test_get_rules_returns_rule_list(self, mock_client):
        mock_client.request.return_value = {
            "rule": [{"hostname": "192.168.1.0/24", "privilege": "rw"}]
        }
        mgr = _mgr(mock_client)
        rules = mgr.get_rules("my-share")
        assert len(rules) == 1
        assert rules[0]["privilege"] == "rw"

    def test_get_rules_empty_when_no_rules(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        rules = mgr.get_rules("my-share")
        assert rules == []

    def test_get_rules_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"rule": []}
        mgr = _mgr(mock_client)
        mgr.get_rules("test-share")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.FileServ.NFS.SharePrivilege"
        assert call.args[1] == "load"
        assert call.kwargs.get("share_name") == "test-share"
