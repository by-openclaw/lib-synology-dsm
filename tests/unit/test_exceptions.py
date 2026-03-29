"""Unit tests — exception hierarchy and client.request() error mapping."""

import pytest
from unittest.mock import patch
from synology_dsm import DSMClient
from synology_dsm.exceptions import (
    DSMAPIError,
    DSMAuthError,
    DSMConnectionError,
    DSMError,
    DSMPermissionError,
    DSMSessionError,
)


def _make_client_with_sid():
    """Return a DSMClient with a fake SID already set."""
    client = DSMClient("your-nas-host")
    client._sid = "fake-sid"
    client._synotoken = "fake-token"
    return client


class TestExceptionHierarchy:
    def test_dsmauth_is_dsmerror(self):
        e = DSMAuthError("bad creds", code=400)
        assert isinstance(e, DSMError)
        assert e.code == 400

    def test_dsmpermission_is_dsmerror(self):
        e = DSMPermissionError("no perms", code=403)
        assert isinstance(e, DSMError)
        assert e.code == 403

    def test_dsmsession_is_dsmerror(self):
        e = DSMSessionError("session expired", code=119)
        assert isinstance(e, DSMError)
        assert e.code == 119

    def test_dsmapi_is_dsmerror(self):
        e = DSMAPIError("something broke", code=999)
        assert isinstance(e, DSMError)
        assert e.code == 999

    def test_code_none_default(self):
        e = DSMError("msg")
        assert e.code is None

    def test_dsmconnection_is_dsmerror(self):
        e = DSMConnectionError("cannot reach NAS")
        assert isinstance(e, DSMError)
        assert e.code is None

    def test_dsmconnection_message(self):
        e = DSMConnectionError("timeout connecting to 10.x.x.x:5001")
        assert "timeout" in str(e)


class TestClientRequestErrorMapping:
    def test_code_400_raises_auth_error(self):
        client = _make_client_with_sid()
        with patch.object(client, "_post", return_value={"success": False, "error": {"code": 400}}):
            with pytest.raises(DSMAuthError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 400

    def test_code_402_raises_auth_error(self):
        client = _make_client_with_sid()
        with patch.object(client, "_post", return_value={"success": False, "error": {"code": 402}}):
            with pytest.raises(DSMAuthError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 402

    def test_code_403_raises_permission_error(self):
        client = _make_client_with_sid()
        with patch.object(client, "_post", return_value={"success": False, "error": {"code": 403}}):
            with pytest.raises(DSMPermissionError) as exc_info:
                client.request("SYNO.Core.Share", "create")
        assert exc_info.value.code == 403

    def test_code_119_raises_session_error(self):
        client = _make_client_with_sid()
        with patch.object(client, "_post", return_value={"success": False, "error": {"code": 119}}):
            with pytest.raises(DSMSessionError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 119

    def test_unknown_code_raises_api_error(self):
        client = _make_client_with_sid()
        with patch.object(client, "_post", return_value={"success": False, "error": {"code": 999}}):
            with pytest.raises(DSMAPIError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 999

    def test_success_returns_data(self):
        client = _make_client_with_sid()
        with patch.object(
            client, "_post", return_value={"success": True, "data": {"users": [{"name": "admin"}]}}
        ):
            result = client.request("SYNO.Core.User", "list")
        assert result == {"users": [{"name": "admin"}]}

    def test_success_empty_data(self):
        """success=True with no data key returns empty dict."""
        client = _make_client_with_sid()
        with patch.object(client, "_post", return_value={"success": True}):
            result = client.request("SYNO.Core.User", "list")
        assert result == {}

    def test_no_sid_raises_runtime_error(self):
        client = DSMClient("your-nas-host")
        with pytest.raises(RuntimeError, match="Not logged in"):
            client.request("SYNO.Core.User", "list")

    def test_request_includes_sid_and_version(self):
        """request() passes _sid and version string in payload."""
        client = _make_client_with_sid()
        captured = {}

        def capture_post(url, data, headers=None):
            captured.update(data)
            return {"success": True, "data": {}}

        with patch.object(client, "_post", side_effect=capture_post):
            client.request("SYNO.Core.User", "list", version=3)

        assert captured["_sid"] == "fake-sid"
        assert captured["version"] == "3"
        assert captured["api"] == "SYNO.Core.User"
        assert captured["method"] == "list"
