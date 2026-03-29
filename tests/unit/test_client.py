"""Tests for DSM client session management."""

import pytest
from unittest.mock import patch
from synology_dsm import DSMClient
from synology_dsm.exceptions import DSMAuthError


def test_login_success():
    client = DSMClient("your-nas-host")
    with patch.object(client, "_post", return_value={"success": True, "data": {"sid": "test-session-123", "synotoken": "tok123"}}):
        sid = client.login("admin", "password")
    assert sid == "test-session-123"
    assert client._sid == "test-session-123"
    assert client._synotoken == "tok123"


def test_login_failure():
    client = DSMClient("your-nas-host")
    with patch.object(client, "_post", return_value={"success": False, "error": {"code": 400}}):
        with pytest.raises(DSMAuthError, match="Login failed"):
            client.login("admin", "wrong")


def test_login_no_synotoken():
    """login() tolerates missing synotoken (older DSM versions)."""
    client = DSMClient("your-nas-host")
    with patch.object(client, "_post", return_value={"success": True, "data": {"sid": "abc"}}):
        sid = client.login("admin", "pass")
    assert sid == "abc"
    assert client._synotoken == ""


def test_logout_clears_sid():
    client = DSMClient("your-nas-host")
    client._sid = "fake-sid"
    with patch.object(client, "_post", return_value={}):
        client.logout()
    assert client._sid is None


def test_logout_noop_when_not_logged_in():
    """logout() does nothing if not logged in."""
    client = DSMClient("your-nas-host")
    client.logout()
    assert client._sid is None


def test_context_manager_calls_logout():
    client = DSMClient("your-nas-host")
    client._sid = "fake-sid"
    with patch.object(client, "_post", return_value={}):
        with client:
            pass
    assert client._sid is None


def test_https_false_no_ssl_ctx():
    client = DSMClient("your-nas-host", https=False)
    assert client._ssl_ctx is None
    assert client.base_url.startswith("http://")


def test_https_verify_ssl_true():
    import ssl
    client = DSMClient("your-nas-host", https=True, verify_ssl=True)
    assert isinstance(client._ssl_ctx, ssl.SSLContext)


def test_custom_port():
    client = DSMClient("your-nas-host", port=5002)
    assert ":5002" in client.base_url
