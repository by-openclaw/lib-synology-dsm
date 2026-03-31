# SPDX-License-Identifier: MIT
"""Tests for FileStationManager — list(), get(), ensure() (the only public methods)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from synology_dsm_v2.base import Action, EnsureResult, State
from synology_dsm_v2.filestation import FileStationManager, _BOUNDARY


# -- Fixtures --


def _mock_client() -> MagicMock:
    client = MagicMock()
    client.base_url = "https://10.6.224.6:5001/webapi"
    client.synotoken = "test-syno-token"
    client.sid = "test-sid"
    client._ssl_ctx = None
    client._timeout = 30
    return client


def _file_dict(name: str = "subfolder", isdir: bool = True, **kw) -> dict:
    d = {"name": name, "isdir": isdir, "path": f"/my-share/{name}"}
    d.update(kw)
    return d


# -- Instantiation & repr --


class TestFileStationManagerInit:
    def test_instantiation(self) -> None:
        mgr = FileStationManager(_mock_client())
        assert mgr is not None

    def test_repr(self) -> None:
        mgr = FileStationManager(_mock_client())
        r = repr(mgr)
        assert "FileStationManager" in r
        assert "SYNO.FileStation.List" in r

    def test_api_property(self) -> None:
        mgr = FileStationManager(_mock_client())
        assert mgr.api == "SYNO.FileStation.List"
        assert mgr.version == 2


# -- list() --


class TestFileStationManagerList:
    def test_list_shares(self) -> None:
        client = _mock_client()
        client.request.return_value = {"shares": [{"name": "share-a"}, {"name": "share-b"}]}
        mgr = FileStationManager(client)

        result = mgr.list()
        assert len(result) == 2
        assert result[0]["name"] == "share-a"

    def test_list_folder_contents(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": [_file_dict("file.txt", isdir=False)]}
        mgr = FileStationManager(client)

        result = mgr.list("/my-share")
        assert len(result) == 1
        assert result[0]["name"] == "file.txt"

    def test_list_empty(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": []}
        mgr = FileStationManager(client)

        result = mgr.list("/empty-share")
        assert result == []


# -- get() --


class TestFileStationManagerGet:
    def test_get_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": [_file_dict("subfolder")]}
        mgr = FileStationManager(client)

        result = mgr.get("/my-share/subfolder")
        assert result is not None
        assert result["name"] == "subfolder"

    def test_get_not_found(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": [_file_dict("other")]}
        mgr = FileStationManager(client)

        result = mgr.get("/my-share/nonexistent")
        assert result is None

    def test_get_handles_error_gracefully(self) -> None:
        client = _mock_client()
        client.request.side_effect = Exception("API error")
        mgr = FileStationManager(client)

        result = mgr.get("/my-share/subfolder")
        assert result is None


# -- ensure(state=PRESENT) --


class TestEnsurePresent:
    def test_create_folder_when_missing(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"files": []},                                  # list() inside get() → not found
            {"folders": [_file_dict("subfolder")]},         # _mkdir() via client.request
            {"files": [_file_dict("subfolder")]},           # list() inside get() for after
        ]
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.PRESENT)
        assert isinstance(result, EnsureResult)
        assert result.changed is True
        assert result.action == Action.CREATED

    def test_noop_when_exists(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": [_file_dict("subfolder")]}
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.PRESENT)
        assert result.changed is False
        assert result.action == Action.NOOP

    def test_mkdir_uses_correct_api(self) -> None:
        """Verify _mkdir calls SYNO.FileStation.CreateFolder via direct client call."""
        client = _mock_client()
        client.request.side_effect = [
            {"files": []},                                  # get()
            {"folders": [_file_dict("subfolder")]},         # _mkdir()
            {"files": [_file_dict("subfolder")]},           # get() for after
        ]
        mgr = FileStationManager(client)

        mgr.ensure("/my-share/subfolder", state=State.PRESENT)
        # Second call should be to CreateFolder
        mkdir_call = client.request.call_args_list[1]
        assert mkdir_call.kwargs.get("api") == "SYNO.FileStation.CreateFolder"


# -- ensure(state=ABSENT) --


class TestEnsureAbsent:
    def test_delete_when_exists(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"files": [_file_dict("subfolder")]},   # get()
            {},                                      # _delete_path() via client.request
        ]
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.ABSENT)
        assert result.changed is True
        assert result.action == Action.DELETED
        assert result.before is not None

    def test_noop_when_already_absent(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": []}
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.ABSENT)
        assert result.changed is False
        assert result.action == Action.NOOP

    def test_delete_uses_correct_api(self) -> None:
        client = _mock_client()
        client.request.side_effect = [
            {"files": [_file_dict("subfolder")]},
            {},
        ]
        mgr = FileStationManager(client)

        mgr.ensure("/my-share/subfolder", state=State.ABSENT)
        delete_call = client.request.call_args_list[1]
        assert delete_call.kwargs.get("api") == "SYNO.FileStation.Delete"


# -- ensure(dry_run=True) --


class TestEnsureDryRun:
    def test_dry_run_would_create(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": []}
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.PRESENT, dry_run=True)
        assert result.changed is False
        assert result.action == Action.WOULD_CREATE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_would_delete(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": [_file_dict("subfolder")]}
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.ABSENT, dry_run=True)
        assert result.action == Action.WOULD_DELETE
        assert result.dry_run is True
        assert client.request.call_count == 1

    def test_dry_run_noop(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": [_file_dict("subfolder")]}
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.PRESENT, dry_run=True)
        assert result.action == Action.NOOP
        assert result.changed is False


# -- ensure() returns EnsureResult --


class TestEnsureResultType:
    def test_returns_ensure_result_not_dict(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": []}
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.ABSENT)
        assert isinstance(result, EnsureResult)
        assert not isinstance(result, dict)

    def test_to_dict_produces_v1_compatible_format(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": []}
        mgr = FileStationManager(client)

        result = mgr.ensure("/my-share/subfolder", state=State.ABSENT)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "changed" in d
        assert "action" in d


# -- Invalid state --


class TestEnsureInvalidState:
    def test_invalid_state_raises(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": []}
        mgr = FileStationManager(client)

        with pytest.raises(ValueError, match="Invalid state"):
            mgr.ensure("/my-share/subfolder", state="invalid")  # type: ignore[arg-type]


# -- Multipart body building --


class TestMultipart:
    def test_build_multipart_structure(self) -> None:
        mgr = FileStationManager(_mock_client())
        body = mgr._build_multipart(
            fields={"path": "/my-share", "overwrite": "true"},
            file_name="test.txt",
            file_content=b"hello world",
        )
        assert b"--" + _BOUNDARY in body
        assert b"--" + _BOUNDARY + b"--" in body
        assert b'name="path"' in body
        assert b'name="file"' in body
        assert b'filename="test.txt"' in body
        assert b"hello world" in body


# -- Upload --


class TestUpload:
    def test_upload_dry_run(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": []}
        mgr = FileStationManager(client)

        result = mgr._upload("/local/file.txt", "/my-share", dry_run=True)
        assert result.action == Action.WOULD_UPLOAD
        assert result.dry_run is True

    def test_upload_dry_run_noop_no_overwrite(self) -> None:
        client = _mock_client()
        client.request.return_value = {"files": [_file_dict("file.txt", isdir=False)]}
        mgr = FileStationManager(client)

        result = mgr._upload("/local/file.txt", "/my-share", overwrite=False, dry_run=True)
        assert result.action == Action.NOOP
        assert result.dry_run is True

    @patch("urllib.request.urlopen")
    @patch("builtins.open", mock_open(read_data=b"file content"))
    def test_upload_success(self, mock_urlopen: MagicMock) -> None:
        client = _mock_client()
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"success": True, "data": {"file": "test.txt", "pid": 123}}
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        mgr = FileStationManager(client)
        result = mgr._upload("/local/test.txt", "/my-share")
        assert result.changed is True
        assert result.action == Action.UPLOADED

    @patch("urllib.request.urlopen")
    @patch("builtins.open", mock_open(read_data=b"file content"))
    def test_upload_skipped(self, mock_urlopen: MagicMock) -> None:
        client = _mock_client()
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"success": True, "data": {"blSkip": True, "file": "test.txt"}}
        ).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        mgr = FileStationManager(client)
        result = mgr._upload("/local/test.txt", "/my-share", overwrite=False)
        assert result.changed is False
        assert result.action == Action.NOOP


# -- Download --


class TestDownload:
    @patch("urllib.request.urlopen")
    @patch("builtins.open", mock_open())
    def test_download_success(self, mock_urlopen: MagicMock) -> None:
        client = _mock_client()
        mock_response = MagicMock()
        mock_response.read.return_value = b"file data"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        mgr = FileStationManager(client)
        result = mgr._download("/my-share/test.txt", "/local/test.txt")
        assert result.changed is True
        assert result.action == Action.DOWNLOADED
        assert result.after["file"] == "test.txt"


# -- No public CRUD methods --


class TestNoCRUDExposed:
    def test_no_public_create(self) -> None:
        mgr = FileStationManager(_mock_client())
        assert not hasattr(mgr, "create")

    def test_no_public_update(self) -> None:
        mgr = FileStationManager(_mock_client())
        assert not hasattr(mgr, "update")

    def test_no_public_delete(self) -> None:
        mgr = FileStationManager(_mock_client())
        assert not hasattr(mgr, "delete")

    def test_private_ops_exist(self) -> None:
        mgr = FileStationManager(_mock_client())
        assert hasattr(mgr, "_mkdir")
        assert hasattr(mgr, "_delete_path")
        assert hasattr(mgr, "_upload")
        assert hasattr(mgr, "_download")
        assert hasattr(mgr, "_build_multipart")
