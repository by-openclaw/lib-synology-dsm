"""Live NAS integration tests — TrafficControlManager."""

from __future__ import annotations

import os
import uuid

import pytest

# ── Config ────────────────────────────────────────────────────────────────────
NAS_HOST = os.environ.get("NAS_HOST", "")
NAS_PORT = int(os.environ.get("NAS_PORT") or "5001")
ADMIN_USER = os.environ.get("API_USER", "")
ADMIN_PASS = os.environ.get("API_PASS", "")

# Skip entire module when NAS not configured
pytestmark = pytest.mark.integration
nas_required = pytest.mark.skipif(
    not NAS_HOST or not ADMIN_USER or not ADMIN_PASS,
    reason="NAS_HOST / API_USER / API_PASS not set — skipping live NAS tests",
)


@pytest.fixture(scope="module")
def run_id() -> str:
    """Unique 8-char hex ID for this test run — scopes all test resources."""
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="module")
def client():
    """Authenticated DSMClient for the entire test module."""
    from synology_dsm import DSMClient

    if not NAS_HOST or not ADMIN_USER or not ADMIN_PASS:
        pytest.skip("NAS_HOST / API_USER / API_PASS not set")

    c = DSMClient(NAS_HOST, port=NAS_PORT, verify_ssl=False)
    c.login(ADMIN_USER, ADMIN_PASS)
    yield c
    try:
        c.logout()
    except Exception:
        pass


@nas_required
class TestTrafficControlManager:
    """TrafficControl rules — full lifecycle on ovs_bond0 adapter."""

    ADAPTER = "ovs_bond0"

    @pytest.fixture(autouse=True)
    def setup(self, client) -> None:  # noqa: ANN001
        from synology_dsm.trafficcontrol import TrafficControlManager

        self.tc = TrafficControlManager(client)
        yield
        try:
            self.tc.clear_rules(self.ADAPTER)
        except Exception:
            pass

    def test_load_returns_list(self) -> None:
        """load() returns a list (may be empty)."""
        result = self.tc.load(self.ADAPTER)
        assert isinstance(result, list)

    def test_clear_rules(self) -> None:
        """clear_rules() — empties rule list, returns changed."""
        r = self.tc.clear_rules(self.ADAPTER)
        assert isinstance(r["changed"], bool)
        assert "action" in r
        assert self.tc.load(self.ADAPTER) == []

    def test_add_and_remove_rule(self) -> None:
        """add_rule() then remove_rule() — full round-trip."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "nfs",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 500,
            "maxrate": 1000,
            "source": "all",
            "ip_direction": "dest",
        }
        r_add = self.tc.add_rule(self.ADAPTER, rule)
        assert r_add["changed"] is True
        rules = self.tc.load(self.ADAPTER)
        assert len(rules) == 1

        rule_id = rules[0]["id"]
        r_remove = self.tc.remove_rule(self.ADAPTER, rule_id)
        assert r_remove["changed"] is True
        assert self.tc.load(self.ADAPTER) == []

    def test_ensure_rule_creates(self) -> None:
        """ensure_rule() — creates rule when absent."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "ssh",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 100,
            "maxrate": 500,
            "source": "all",
            "ip_direction": "dest",
        }
        r = self.tc.ensure_rule(self.ADAPTER, rule)
        assert r["changed"] is True
        assert r["action"] == "added"

    def test_ensure_rule_noop(self) -> None:
        """ensure_rule() — noop when identical rule already present."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "ftp",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 200,
            "maxrate": 800,
            "source": "all",
            "ip_direction": "dest",
        }
        self.tc.ensure_rule(self.ADAPTER, rule)
        r = self.tc.ensure_rule(self.ADAPTER, rule)
        assert r["changed"] is False
        assert r["action"] == "none"

    def test_dry_run_does_not_change(self) -> None:
        """dry_run=True must not write rules."""
        self.tc.clear_rules(self.ADAPTER)
        rule = {
            "enabled": True,
            "port_type": "SYS",
            "port_num": "snmp",
            "port_direction": "src",
            "protocol": "all",
            "minrate": 50,
            "maxrate": 200,
            "source": "all",
            "ip_direction": "dest",
        }
        r = self.tc.add_rule(self.ADAPTER, rule, dry_run=True)
        assert r["dry_run"] is True
        assert self.tc.load(self.ADAPTER) == []
