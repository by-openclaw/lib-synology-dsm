"""Unit tests — exception hierarchy and client.request() error mapping."""

import pytest
from unittest.mock import MagicMock, patch
from synology_dsm import DSMClient
from synology_dsm.exceptions import (
    DSMAuthError,
    DSMPermissionError,
    DSMSessionError,
    DSMAPIError,
    DSMError,
)


def _make_client_with_sid():
    """Return a DSMClient with a fake SID already set."""
    client = DSMClient("10.0.0.1")
    client._sid = "fake-sid"
    client._synotoken = "fake-token"
    return client


def _mock_response(data: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


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


class TestClientRequestErrorMapping:
    def test_code_400_raises_auth_error(self):
        client = _make_client_with_sid()
        mock_resp = _mock_response({"success": False, "error": {"code": 400}})
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(DSMAuthError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 400

    def test_code_402_raises_auth_error(self):
        client = _make_client_with_sid()
        mock_resp = _mock_response({"success": False, "error": {"code": 402}})
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(DSMAuthError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 402

    def test_code_403_raises_permission_error(self):
        client = _make_client_with_sid()
        mock_resp = _mock_response({"success": False, "error": {"code": 403}})
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(DSMPermissionError) as exc_info:
                client.request("SYNO.Core.Share", "create")
        assert exc_info.value.code == 403

    def test_code_119_raises_session_error(self):
        client = _make_client_with_sid()
        mock_resp = _mock_response({"success": False, "error": {"code": 119}})
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(DSMSessionError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 119

    def test_unknown_code_raises_api_error(self):
        client = _make_client_with_sid()
        mock_resp = _mock_response({"success": False, "error": {"code": 999}})
        with patch.object(client._client, "post", return_value=mock_resp):
            with pytest.raises(DSMAPIError) as exc_info:
                client.request("SYNO.Core.User", "list")
        assert exc_info.value.code == 999

    def test_success_returns_data(self):
        client = _make_client_with_sid()
        mock_resp = _mock_response({"success": True, "data": {"users": [{"name": "admin"}]}})
        with patch.object(client._client, "post", return_value=mock_resp):
            result = client.request("SYNO.Core.User", "list")
        assert result == {"users": [{"name": "admin"}]}

    def test_no_sid_raises_runtime_error(self):
        client = DSMClient("10.0.0.1")
        with pytest.raises(RuntimeError, match="Not logged in"):
            client.request("SYNO.Core.User", "list")
