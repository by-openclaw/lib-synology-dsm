"""Tests for DSM client session management."""

import pytest
from unittest.mock import patch, MagicMock
from synology_dsm import DSMClient
from synology_dsm.exceptions import DSMAuthError


def test_login_success():
    client = DSMClient("10.6.224.6")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": True, "data": {"sid": "test-session-123"}}
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._client, "post", return_value=mock_resp):
        sid = client.login("admin", "password")
    assert sid == "test-session-123"
    assert client._sid == "test-session-123"


def test_login_failure():
    client = DSMClient("10.6.224.6")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": False, "error": {"code": 400}}
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._client, "post", return_value=mock_resp):
        with pytest.raises(DSMAuthError, match="Login failed"):
            client.login("admin", "wrong")
