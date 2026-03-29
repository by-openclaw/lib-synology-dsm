"""Unit tests — FileStationManager."""

from unittest.mock import MagicMock, patch, mock_open
from synology_dsm.filestation import FileStationManager


def _mgr(mock_client):
    return FileStationManager(mock_client)


class TestUpload:
    def test_upload_puts_synotoken_in_url(self, mock_client):
        """SynoToken must appear in URL query string for FileStation upload."""
        mock_client._synotoken = "TEST-TOKEN-123"
        mock_client._sid = "SID-456"
        mock_client.base_url = "https://nas:5001/webapi"

        mock_http_client = MagicMock()
        mock_client._client = mock_http_client

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": True, "data": {"file": "test.txt", "pid": 1}}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.post.return_value = mock_resp

        mgr = _mgr(mock_client)
        with patch("builtins.open", mock_open(read_data=b"data")):
            result = mgr.upload("/tmp/test.txt", "/by-share")

        call_args = mock_http_client.post.call_args
        url = call_args.args[0]
        assert "SynoToken=TEST-TOKEN-123" in url
        assert result["success"] is True

    def test_upload_sends_session_as_cookie(self, mock_client):
        """Session ID must be sent as cookie id=, not form field."""
        mock_client._synotoken = "TOK"
        mock_client._sid = "SID-789"
        mock_client.base_url = "https://nas:5001/webapi"

        mock_http_client = MagicMock()
        mock_client._client = mock_http_client
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": True, "data": {}}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.post.return_value = mock_resp

        mgr = _mgr(mock_client)
        with patch("builtins.open", mock_open(read_data=b"hello")):
            mgr.upload("/tmp/file.txt", "/share")

        call_args = mock_http_client.post.call_args
        cookies = call_args.kwargs.get("cookies", {})
        assert cookies.get("id") == "SID-789"

    def test_upload_uses_path_field(self, mock_client):
        """Form field must be 'path', not 'dest_folder_path'."""
        mock_client._synotoken = "TOK"
        mock_client._sid = "SID"
        mock_client.base_url = "https://nas:5001/webapi"

        mock_http_client = MagicMock()
        mock_client._client = mock_http_client
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": True, "data": {}}
        mock_resp.raise_for_status = MagicMock()
        mock_http_client.post.return_value = mock_resp

        mgr = _mgr(mock_client)
        with patch("builtins.open", mock_open(read_data=b"x")):
            mgr.upload("/tmp/f.txt", "/dest")

        call_args = mock_http_client.post.call_args
        data = call_args.kwargs.get("data", {})
        assert "path" in data
        assert "dest_folder_path" not in data
        assert data["path"] == "/dest"

    def test_upload_dry_run_no_http_call(self, mock_client):
        """dry_run=True must not make any HTTP call."""
        mock_client._synotoken = "TOK"
        mock_client._sid = "SID"
        mock_client.base_url = "https://nas:5001/webapi"

        mock_http_client = MagicMock()
        mock_client._client = mock_http_client

        # _file_exists calls self.list() which calls self._c.request()
        mock_client.request.return_value = {"files": []}

        mgr = _mgr(mock_client)
        result = mgr.upload("/tmp/f.txt", "/dest", dry_run=True)
        assert result["dry_run"] is True
        # No actual HTTP post for upload
        mock_http_client.post.assert_not_called()

    def test_upload_overwrite_false_skips_existing(self, mock_client):
        """overwrite=False when file exists should return skipped=True."""
        mock_client._synotoken = "TOK"
        mock_client._sid = "SID"
        mock_client.base_url = "https://nas:5001/webapi"
        mock_client._client = MagicMock()

        # File exists in the listing
        mock_client.request.return_value = {"files": [{"name": "f.txt"}]}

        mgr = _mgr(mock_client)
        result = mgr.upload("/tmp/f.txt", "/dest", overwrite=False, dry_run=True)
        assert result["skipped"] is True


class TestDelete:
    def test_delete_dry_run_no_api_call(self, mock_client):
        mgr = _mgr(mock_client)
        result = mgr.delete("/share/file.txt", dry_run=True)
        assert result["dry_run"] is True
        assert result["action"] == "would_delete"
        assert result["target"] == "/share/file.txt"
        mock_client.request.assert_not_called()

    def test_delete_calls_api(self, mock_client):
        mock_client.request.return_value = {"taskid": "abc"}
        mgr = _mgr(mock_client)
        mgr.delete("/share/file.txt")
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args.args[0] == "SYNO.FileStation.Delete"
        assert call_args.args[1] == "start"
