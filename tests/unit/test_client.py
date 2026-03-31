"""Tests for DSM client session management."""

import urllib.error
from unittest.mock import patch

import pytest

from synology_dsm import DSMClient, DSMConnectionError
from synology_dsm.exceptions import DSMAuthError


def test_login_success():
    client = DSMClient("your-nas-host")
    with patch.object(
        client,
        "_post",
        return_value={"success": True, "data": {"sid": "test-session-123", "synotoken": "tok123"}},
    ):
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
    with patch.object(client, "_post", return_value={}), client:
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


def test_post_adds_headers():
    """_post adds Content-Type and optional extra headers to the request."""
    import json as _j

    client = DSMClient("your-nas-host", https=False)
    captured_req = {}

    class FakeResp:
        def read(self):
            return _j.dumps({"ok": True}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

    def fake_urlopen(req, context=None, timeout=None):
        captured_req["url"] = req.full_url
        captured_req["ct"] = req.get_header("Content-type")
        captured_req["xsyn"] = req.get_header("X-syno-token")
        return FakeResp()

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = client._post(
            "http://nas/api",
            {"key": "val"},
            headers={"X-SYNO-TOKEN": "tok"},
        )

    assert result == {"ok": True}
    assert captured_req["ct"] == "application/x-www-form-urlencoded"
    assert captured_req["xsyn"] == "tok"


def test_post_raises_connection_error_on_url_error():
    """_post wraps urllib.error.URLError as DSMConnectionError."""
    client = DSMClient("your-nas-host", https=False)
    with (
        patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ),
        pytest.raises(DSMConnectionError, match="Cannot reach DSM"),
    ):
        client._post("http://nas/api", {"key": "val"})


def test_post_raises_connection_error_on_os_error():
    """_post wraps OSError (e.g. socket timeout) as DSMConnectionError."""
    client = DSMClient("your-nas-host", https=False)
    with (
        patch(
            "urllib.request.urlopen",
            side_effect=OSError("timed out"),
        ),
        pytest.raises(DSMConnectionError, match="Network error"),
    ):
        client._post("http://nas/api", {"key": "val"})


def test_logout_suppresses_exception():
    """logout() must not raise even if _post throws."""
    client = DSMClient("your-nas-host")
    client._sid = "fake-sid"

    with patch.object(client, "_post", side_effect=Exception("network error")):
        client.logout()  # should not raise

    assert client._sid is None


class TestTimeout:
    def test_default_timeout_is_30(self):
        client = DSMClient("your-nas-host")
        assert client._timeout == 30

    def test_custom_timeout(self):
        client = DSMClient("your-nas-host", timeout=60)
        assert client._timeout == 60

    def test_timeout_used_in_post(self):
        """_post passes _timeout to urlopen."""
        import json as _j

        client = DSMClient("your-nas-host", https=False, timeout=45)
        captured = {}

        class FakeResp:
            def read(self):
                return _j.dumps({"ok": True}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

        def fake_urlopen(req, context=None, timeout=None):
            captured["timeout"] = timeout
            return FakeResp()

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            client._post("http://nas/api", {"key": "val"})

        assert captured["timeout"] == 45


class TestResolveError:
    def test_resolve_error_maps_code_119_to_session_error(self):
        from synology_dsm.exceptions import DSMSessionError

        client = DSMClient("nas.local")
        with pytest.raises(DSMSessionError) as exc_info:
            client._resolve_error({"code": 119}, context="test")
        assert exc_info.value.code == 119

    def test_resolve_error_maps_code_403_to_permission_error(self):
        from synology_dsm.exceptions import DSMPermissionError

        client = DSMClient("nas.local")
        with pytest.raises(DSMPermissionError) as exc_info:
            client._resolve_error({"code": 403}, context="test")
        assert exc_info.value.code == 403

    def test_resolve_error_uses_fallback_for_unknown_code(self):
        from synology_dsm.exceptions import DSMAPIError

        client = DSMClient("nas.local")
        with pytest.raises(DSMAPIError):
            client._resolve_error({"code": 9999}, context="test")

    def test_resolve_error_handles_non_dict_error(self):
        from synology_dsm.exceptions import DSMAPIError

        client = DSMClient("nas.local")
        with pytest.raises(DSMAPIError):
            client._resolve_error("raw string error", context="test")

    def test_resolve_error_maps_code_400_to_auth_error(self):
        from synology_dsm.exceptions import DSMAuthError

        client = DSMClient("nas.local")
        with pytest.raises(DSMAuthError) as exc_info:
            client._resolve_error({"code": 400}, context="test")
        assert exc_info.value.code == 400

    def test_resolve_error_maps_code_401_to_auth_error(self):
        from synology_dsm.exceptions import DSMAuthError

        client = DSMClient("nas.local")
        with pytest.raises(DSMAuthError) as exc_info:
            client._resolve_error({"code": 401}, context="test")
        assert exc_info.value.code == 401

    def test_resolve_error_maps_code_402_to_auth_error(self):
        from synology_dsm.exceptions import DSMAuthError

        client = DSMClient("nas.local")
        with pytest.raises(DSMAuthError) as exc_info:
            client._resolve_error({"code": 402}, context="test")
        assert exc_info.value.code == 402

    def test_resolve_error_maps_code_103_to_permission_error(self):
        from synology_dsm.exceptions import DSMPermissionError

        client = DSMClient("nas.local")
        with pytest.raises(DSMPermissionError) as exc_info:
            client._resolve_error({"code": 103}, context="test")
        assert exc_info.value.code == 103

    def test_resolve_error_maps_code_404_to_not_found(self):
        from synology_dsm.exceptions import DSMNotFoundError

        client = DSMClient("nas.local")
        with pytest.raises(DSMNotFoundError) as exc_info:
            client._resolve_error({"code": 404}, context="test")
        assert exc_info.value.code == 404

    def test_resolve_error_maps_code_117_to_invalid_operation(self):
        from synology_dsm.exceptions import DSMInvalidOperationError

        client = DSMClient("nas.local")
        with pytest.raises(DSMInvalidOperationError) as exc_info:
            client._resolve_error({"code": 117}, context="test")
        assert exc_info.value.code == 117

    def test_resolve_error_maps_code_102_to_invalid_parameter(self):
        from synology_dsm.exceptions import DSMInvalidParameterError

        client = DSMClient("nas.local")
        with pytest.raises(DSMInvalidParameterError) as exc_info:
            client._resolve_error({"code": 102}, context="test")
        assert exc_info.value.code == 102

    def test_resolve_error_maps_code_120_to_invalid_parameter(self):
        from synology_dsm.exceptions import DSMInvalidParameterError

        client = DSMClient("nas.local")
        with pytest.raises(DSMInvalidParameterError) as exc_info:
            client._resolve_error({"code": 120}, context="test")
        assert exc_info.value.code == 120

    def test_resolve_error_maps_code_1001_to_invalid_parameter(self):
        from synology_dsm.exceptions import DSMInvalidParameterError

        client = DSMClient("nas.local")
        with pytest.raises(DSMInvalidParameterError) as exc_info:
            client._resolve_error({"code": 1001}, context="test")
        assert exc_info.value.code == 1001

    def test_resolve_error_maps_code_105_to_session_error(self):
        from synology_dsm.exceptions import DSMSessionError

        client = DSMClient("nas.local")
        with pytest.raises(DSMSessionError) as exc_info:
            client._resolve_error({"code": 105}, context="test")
        assert exc_info.value.code == 105
