"""Unit tests — StorageManager."""

from synology_dsm.storage import StorageManager


def _mgr(mock_client):
    return StorageManager(mock_client)


_VOLUME_1 = {
    "id": "/volume1",
    "status": "normal",
    "device_type": "raid_6",
    "size_total_byte": 10_000_000_000,
    "size_used_byte": 3_000_000_000,
    "fs_type": "btrfs",
}

_VOLUME_2 = {
    "id": "/volume2",
    "status": "normal",
    "device_type": "shr",
    "size_total_byte": 5_000_000_000,
    "size_used_byte": 1_000_000_000,
    "fs_type": "ext4",
}


class TestListVolumes:
    def test_returns_volume_list(self, mock_client):
        mock_client.request.return_value = {"volumes": [_VOLUME_1, _VOLUME_2]}
        mgr = _mgr(mock_client)
        result = mgr.list_volumes()
        assert len(result) == 2
        assert result[0]["id"] == "/volume1"

    def test_returns_empty_when_no_volumes(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.list_volumes()
        assert result == []

    def test_calls_correct_api(self, mock_client):
        mock_client.request.return_value = {"volumes": []}
        mgr = _mgr(mock_client)
        mgr.list_volumes()
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.Core.Storage.Volume"
        assert call.args[1] == "list"
        assert call.kwargs.get("version") == 1

    def test_include_cold_storage_adds_option_param(self, mock_client):
        mock_client.request.return_value = {"volumes": []}
        mgr = _mgr(mock_client)
        mgr.list_volumes(include_cold_storage=True)
        call = mock_client.request.call_args
        assert call.kwargs.get("option") == "include_cold_storage"

    def test_no_cold_storage_omits_option_param(self, mock_client):
        mock_client.request.return_value = {"volumes": []}
        mgr = _mgr(mock_client)
        mgr.list_volumes(include_cold_storage=False)
        call = mock_client.request.call_args
        assert "option" not in call.kwargs

    def test_default_params_match_devtools_payload(self, mock_client):
        """Default params must match payload observed in F12 DevTools."""
        mock_client.request.return_value = {"volumes": []}
        mgr = _mgr(mock_client)
        mgr.list_volumes()
        call = mock_client.request.call_args
        assert call.kwargs.get("offset") == 0
        assert call.kwargs.get("limit") == -1
        assert call.kwargs.get("location") == "internal"
        assert call.kwargs.get("option") == "include_cold_storage"

    def test_custom_limit_and_offset(self, mock_client):
        mock_client.request.return_value = {"volumes": [_VOLUME_1]}
        mgr = _mgr(mock_client)
        mgr.list_volumes(offset=1, limit=5)
        call = mock_client.request.call_args
        assert call.kwargs.get("offset") == 1
        assert call.kwargs.get("limit") == 5


class TestGetVolume:
    def test_returns_matching_volume(self, mock_client):
        mock_client.request.return_value = {"volumes": [_VOLUME_1, _VOLUME_2]}
        mgr = _mgr(mock_client)
        vol = mgr.get_volume("/volume1")
        assert vol is not None
        assert vol["id"] == "/volume1"
        assert vol["fs_type"] == "btrfs"

    def test_returns_none_when_not_found(self, mock_client):
        mock_client.request.return_value = {"volumes": [_VOLUME_1]}
        mgr = _mgr(mock_client)
        vol = mgr.get_volume("/volume99")
        assert vol is None

    def test_returns_none_on_empty_list(self, mock_client):
        mock_client.request.return_value = {"volumes": []}
        mgr = _mgr(mock_client)
        vol = mgr.get_volume("/volume1")
        assert vol is None

    def test_returns_second_volume(self, mock_client):
        mock_client.request.return_value = {"volumes": [_VOLUME_1, _VOLUME_2]}
        mgr = _mgr(mock_client)
        vol = mgr.get_volume("/volume2")
        assert vol is not None
        assert vol["device_type"] == "shr"
