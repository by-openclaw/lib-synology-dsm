# SPDX-License-Identifier: MIT
"""Tests for DSMClient — properties, context manager, error resolution, validation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from synology_dsm_v2.client import DSMClient
from synology_dsm_v2.exceptions import (
    DSMAPIError,
    DSMAuthError,
    DSMConnectionError,
    DSMSessionError,
)


class TestClientInit:
    def test_default_values(self) -> None:
        c = DSMClient("10.6.224.6")
        assert c._host == "10.6.224.6"
        assert c._port == 5001
        assert c._https is True
        assert c._verify_ssl is False
        assert c.timeout == 30

    def test_custom_values(self) -> None:
        c = DSMClient("nas.local", port=5000, https=False, verify_ssl=True, timeout=60)
        assert c._port == 5000
        assert c._https is False
        assert c.timeout == 60

    def test_empty_host_raises(self) -> None:
        with pytest.raises(ValueError, match="host must not be empty"):
            DSMClient("")

    def test_invalid_port_raises(self) -> None:
        with pytest.raises(ValueError, match="port must be"):
            DSMClient("nas", port=0)
        with pytest.raises(ValueError, match="port must be"):
            DSMClient("nas", port=70000)

    def test_invalid_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout must be"):
            DSMClient("nas", timeout=0)


class TestClientProperties:
    def test_base_url_https(self) -> None:
        c = DSMClient("10.6.224.6", port=5001, https=True)
        assert c.base_url == "https://10.6.224.6:5001/webapi"

    def test_base_url_http(self) -> None:
        c = DSMClient("nas.local", port=5000, https=False)
        assert c.base_url == "http://nas.local:5000/webapi"

    def test_sid_initially_none(self) -> None:
        c = DSMClient("nas")
        assert c.sid is None

    def test_synotoken_initially_empty(self) -> None:
        c = DSMClient("nas")
        assert c.synotoken == ""

    def test_is_authenticated_false_initially(self) -> None:
        c = DSMClient("nas")
        assert c.is_authenticated is False

    def test_timeout_setter(self) -> None:
        c = DSMClient("nas")
        c.timeout = 120
        assert c.timeout == 120

    def test_timeout_setter_invalid(self) -> None:
        c = DSMClient("nas")
        with pytest.raises(ValueError, match="timeout must be"):
            c.timeout = 0


class TestClientRepr:
    def test_repr_unauthenticated(self) -> None:
        c = DSMClient("10.6.224.6")
        r = repr(c)
        assert "10.6.224.6" in r
        assert "5001" in r
        assert "not authenticated" in r

    def test_repr_authenticated(self) -> None:
        c = DSMClient("10.6.224.6")
        c._sid = "fake-session-id"
        r = repr(c)
        assert "authenticated" in r
        assert "not authenticated" not in r


class TestClientContextManager:
    def test_enter_returns_self(self) -> None:
        c = DSMClient("nas")
        assert c.__enter__() is c

    def test_exit_calls_logout(self) -> None:
        c = DSMClient("nas")
        c._sid = "test-sid"
        with patch.object(c, "logout") as mock_logout:
            c.__exit__(None, None, None)
            mock_logout.assert_called_once()


class TestClientErrorResolution:
    def test_auth_error_400(self) -> None:
        c = DSMClient("nas")
        with pytest.raises(DSMAuthError) as exc_info:
            c._resolve_error(400, context="Login failed")
        assert exc_info.value.code == 400
        assert "incorrect password" in str(exc_info.value)

    def test_session_error_119(self) -> None:
        c = DSMClient("nas")
        with pytest.raises(DSMSessionError) as exc_info:
            c._resolve_error(119, context="API call")
        assert exc_info.value.code == 119
        assert "SID not found" in str(exc_info.value)

    def test_unknown_code_falls_back_to_api_error(self) -> None:
        c = DSMClient("nas")
        with pytest.raises(DSMAPIError) as exc_info:
            c._resolve_error(99999, context="Unknown")
        assert exc_info.value.code == 99999

    def test_error_message_includes_description(self) -> None:
        c = DSMClient("nas")
        with pytest.raises(DSMAuthError) as exc_info:
            c._resolve_error(401, context="Login")
        assert "Disabled account" in str(exc_info.value)


class TestClientRequest:
    def test_request_without_login_raises(self) -> None:
        c = DSMClient("nas")
        with pytest.raises(DSMSessionError, match="Not authenticated"):
            c.request("SYNO.Core.User", "list")


class TestClientLogin:
    def _mock_post_success(self, client: DSMClient) -> MagicMock:
        """Patch _post to return a successful login response."""
        return patch.object(
            client,
            "_post",
            return_value={
                "success": True,
                "data": {"sid": "test-sid-123", "synotoken": "test-token-456"},
            },
        )

    def _mock_post_failure(self, client: DSMClient, code: int) -> MagicMock:
        """Patch _post to return a failed login response."""
        return patch.object(
            client,
            "_post",
            return_value={"success": False, "error": {"code": code}},
        )

    def test_login_success(self) -> None:
        c = DSMClient("nas")
        with self._mock_post_success(c):
            sid = c.login("admin", "password")
        assert sid == "test-sid-123"
        assert c.sid == "test-sid-123"
        assert c.synotoken == "test-token-456"
        assert c.is_authenticated is True

    def test_login_wrong_password(self) -> None:
        c = DSMClient("nas")
        with self._mock_post_failure(c, 400):
            with pytest.raises(DSMAuthError) as exc_info:
                c.login("admin", "wrong")
        assert exc_info.value.code == 400

    def test_login_disabled_account(self) -> None:
        c = DSMClient("nas")
        with self._mock_post_failure(c, 401):
            with pytest.raises(DSMAuthError) as exc_info:
                c.login("disabled-user", "pass")
        assert exc_info.value.code == 401

    def test_login_account_locked(self) -> None:
        c = DSMClient("nas")
        with self._mock_post_failure(c, 411):
            with pytest.raises(DSMAuthError) as exc_info:
                c.login("locked-user", "pass")
        assert exc_info.value.code == 411


class TestClientLogout:
    def test_logout_clears_session(self) -> None:
        c = DSMClient("nas")
        c._sid = "test-sid"
        c._synotoken = "test-token"
        with patch.object(c, "_post", return_value={"success": True}):
            c.logout()
        assert c.sid is None
        assert c.synotoken == ""
        assert c.is_authenticated is False

    def test_logout_without_session_is_noop(self) -> None:
        c = DSMClient("nas")
        c.logout()  # Should not raise
        assert c.sid is None


class TestClientConnectionError:
    def test_network_failure_wrapped(self) -> None:
        c = DSMClient("unreachable.host")
        with pytest.raises(DSMConnectionError) as exc_info:
            c._post("https://unreachable.host:5001/webapi/entry.cgi", {"api": "test"})
        assert "unreachable.host" in str(exc_info.value)
        assert exc_info.value.code is None
