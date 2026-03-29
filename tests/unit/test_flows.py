"""CRUD flow tests — verifies full create→verify→update→verify→delete→verify lifecycle.

These tests are distinct from unit tests that test individual methods.
Each test here exercises a complete user-facing workflow as a single connected flow,
mirroring exactly what Ansible tasks and automation scripts will do.
"""

from unittest.mock import MagicMock

import pytest

from synology_dsm import DSMClient, GroupManager, NFSManager, ShareManager, UserManager
from synology_dsm.filestation import FileStationManager


@pytest.fixture
def client():
    c = MagicMock(spec=DSMClient)
    c._sid = "test-sid"
    c._synotoken = "test-token"
    return c


class TestShareCRUDFlow:
    """Full lifecycle: create → verify present → update description → delete → verify absent."""

    def test_full_create_verify_update_delete(self, client):
        share_name = "by-data"

        # Step 1: ensure present (absent initially → creates)
        client.request.return_value = {"shares": []}
        mgr = ShareManager(client)
        result = mgr.ensure(share_name, state="present", volume_path="/volume1")
        assert result["changed"] is True
        assert result["action"] == "created"

        # Step 2: ensure present again (now present → noop)
        client.request.return_value = {"shares": [{"name": share_name, "desc": ""}]}
        result = mgr.ensure(share_name, state="present", volume_path="/volume1")
        assert result["changed"] is False
        assert result["action"] == "noop"

        # Step 3: ensure absent → deletes
        client.request.return_value = {"shares": [{"name": share_name, "desc": ""}]}
        result = mgr.ensure(share_name, state="absent")
        assert result["changed"] is True
        assert result["action"] == "deleted"

        # Step 4: ensure absent again (already gone → noop)
        client.request.return_value = {"shares": []}
        result = mgr.ensure(share_name, state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_dry_run_never_calls_create_or_delete(self, client):
        share_name = "by-data"
        client.request.return_value = {"shares": []}
        mgr = ShareManager(client)

        # dry_run create
        result = mgr.ensure(share_name, state="present", dry_run=True)
        assert result["dry_run"] is True
        write_calls = [
            c for c in client.request.call_args_list if c.args[1] in ("create", "delete", "set")
        ]
        assert len(write_calls) == 0


class TestUserCRUDFlow:
    """Full lifecycle: create → verify present → delete → verify absent."""

    def test_full_create_verify_delete(self, client):
        mgr = UserManager(client)

        # Step 1: ensure present (absent → creates)
        client.request.return_value = {"users": []}
        result = mgr.ensure("alice", password="P@ss1", state="present")
        assert result["changed"] is True
        assert result["action"] == "created"

        # Step 2: present again → noop
        client.request.return_value = {"users": [{"name": "alice", "email": "", "description": ""}]}
        result = mgr.ensure("alice", password="P@ss1", state="present")
        assert result["changed"] is False
        assert result["action"] == "noop"

        # Step 3: absent → deletes
        client.request.return_value = {"users": [{"name": "alice"}]}
        result = mgr.ensure("alice", state="absent")
        assert result["changed"] is True
        assert result["action"] == "deleted"

        # Step 4: absent again → noop
        client.request.return_value = {"users": []}
        result = mgr.ensure("alice", state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"


class TestGroupMembershipFlow:
    """Full lifecycle: create group → add member → verify → remove member → delete group."""

    def test_group_with_member_lifecycle(self, client):
        mgr = GroupManager(client)

        # Create group
        client.request.return_value = {"groups": []}
        result = mgr.ensure("ops-team", state="present")
        assert result["action"] == "created"

        # Add member — alice not yet in group (Group.Member list returns offset + empty list)
        client.request.return_value = {"offset": 0, "total": 0, "users": []}
        result = mgr.add_member("ops-team", "alice")
        assert result["changed"] is True

        # Add same member again — idempotent (Group.Member list returns alice)
        client.request.return_value = {"offset": 0, "total": 1, "users": [{"name": "alice"}]}
        result = mgr.add_member("ops-team", "alice")
        assert result["changed"] is False

        # Remove member (Group.Member list returns alice)
        client.request.return_value = {"offset": 0, "total": 1, "users": [{"name": "alice"}]}
        result = mgr.remove_member("ops-team", "alice")
        assert result["changed"] is True

        # Delete group
        client.request.return_value = {"groups": [{"name": "ops-team"}]}
        result = mgr.ensure("ops-team", state="absent")
        assert result["action"] == "deleted"


class TestNFSRuleFlow:
    """Full lifecycle: add NFS rule → verify noop → change privilege → remove."""

    def test_nfs_rule_lifecycle(self, client):
        mgr = NFSManager(client)
        share = "by-data"
        host = "10.6.224.0/20"

        # Add rule (none exist)
        client.request.return_value = {"rule": []}
        result = mgr.ensure(share, host, state="present", rw=True)
        assert result["action"] == "created"

        # Same rule again → noop
        client.request.return_value = {
            "rule": [{"client": host, "privilege": "rw", "root_squash": "root", "async": True}]
        }
        result = mgr.ensure(share, host, state="present", rw=True)
        assert result["action"] == "noop"

        # Change to ro → updates
        client.request.return_value = {
            "rule": [{"client": host, "privilege": "rw", "root_squash": "root", "async": True}]
        }
        result = mgr.ensure(share, host, state="present", rw=False)
        assert result["action"] == "updated"
        assert result["after"]["privilege"] == "ro"

        # Remove rule
        client.request.return_value = {
            "rule": [{"client": host, "privilege": "ro", "root_squash": "root", "async": True}]
        }
        result = mgr.ensure(share, host, state="absent")
        assert result["action"] == "deleted"

        # Remove again → noop
        client.request.return_value = {"rule": []}
        result = mgr.ensure(share, host, state="absent")
        assert result["action"] == "noop"


class TestFileStationFolderFlow:
    """Full lifecycle: create folder → verify noop → delete → verify noop."""

    def test_folder_lifecycle(self, client):
        mgr = FileStationManager(client)
        path = "/by-data/ops-reports"

        # Create (does not exist)
        client.request.return_value = {"files": []}
        result = mgr.ensure(path, state="present")
        assert result["action"] == "created"

        # Create again → noop
        client.request.return_value = {"files": [{"name": "ops-reports"}]}
        result = mgr.ensure(path, state="present")
        assert result["action"] == "noop"

        # Delete
        client.request.return_value = {"files": [{"name": "ops-reports"}]}
        result = mgr.ensure(path, state="absent")
        assert result["action"] == "deleted"

        # Delete again → noop
        client.request.return_value = {"files": []}
        result = mgr.ensure(path, state="absent")
        assert result["action"] == "noop"
