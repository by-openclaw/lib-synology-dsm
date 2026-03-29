"""Unit tests — ShareManager."""

import pytest
import json
from synology_dsm.shares import ShareManager


def _mgr(mock_client):
    return ShareManager(mock_client)


class TestShareCreate:
    def test_create_sends_shareinfo_json(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        mgr.create("by-data", volume_path="/volume1", description="Data share")
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Share"
        assert call.args[1] == "create"
        shareinfo = json.loads(call.kwargs["shareinfo"])
        assert shareinfo["name"] == "by-data"
        assert shareinfo["vol_path"] == "/volume1"
        assert shareinfo["desc"] == "Data share"
        assert "name_org" in shareinfo


class TestShareEnsure:
    def test_ensure_present_creates_when_absent(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("newshare", state="present")
        assert result["changed"] is True
        assert result["action"] == "created"

    def test_ensure_present_noop_when_same(self, mock_client):
        mock_client.request.return_value = {"shares": [{"name": "data", "desc": "same"}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("data", state="present", description="same")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_absent_deletes(self, mock_client):
        mock_client.request.return_value = {"shares": [{"name": "old", "desc": ""}]}
        mgr = _mgr(mock_client)
        result = mgr.ensure("old", state="absent")
        assert result["changed"] is True
        assert result["action"] == "deleted"

    def test_ensure_absent_noop_when_gone(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("ghost", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_dry_run_no_create(self, mock_client):
        mock_client.request.return_value = {"shares": []}
        mgr = _mgr(mock_client)
        result = mgr.ensure("newshare", state="present", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_create"
        create_calls = [c for c in mock_client.request.call_args_list if c.args[1] == "create"]
        assert len(create_calls) == 0
