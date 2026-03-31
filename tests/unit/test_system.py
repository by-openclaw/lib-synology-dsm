"""Unit tests — SystemManager."""

from synology_dsm.exceptions import DSMAPIError
from synology_dsm.system import SystemManager


def _mgr(mock_client):
    return SystemManager(mock_client)


_DSM_INFO_RESPONSE = {
    "model": "DS1513+",
    "serial": "1234567890ABC",
    "hostname": "nas-prod-01",
    "version_string": "DSM 7.2.1-69057 Update 7",
    "version": 69057,
    "up_time": 123456,
    "ram": 8192,
}

_CORE_SYSTEM_RESPONSE = {
    "model": "DS1513+",
    "serial": "1234567890ABC",
    "server_name": "nas-prod-01",
    "firmware_ver": "DSM 7.2.1-69057 Update 7",
    "firmware_build": 69057,
    "uptime": 123456,
    "physical_mem": 8192,
}


class TestGetInfo:
    def test_returns_info_from_dsm_info(self, mock_client):
        mock_client.request.return_value = _DSM_INFO_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.get_info()
        assert result["model"] == "DS1513+"
        assert result["serial"] == "1234567890ABC"
        assert result["hostname"] == "nas-prod-01"
        assert result["dsm_version"] == "DSM 7.2.1-69057 Update 7"
        assert result["dsm_build"] == 69057
        assert result["uptime_seconds"] == 123456
        assert result["ram_mb"] == 8192

    def test_calls_dsm_info_api_first(self, mock_client):
        mock_client.request.return_value = _DSM_INFO_RESPONSE
        mgr = _mgr(mock_client)
        mgr.get_info()
        call = mock_client.request.call_args
        assert call.args[0] == "SYNO.DSM.Info"
        assert call.args[1] == "getinfo"
        assert call.kwargs.get("version") == 2

    def test_falls_back_to_core_system(self, mock_client):
        mock_client.request.side_effect = [
            DSMAPIError("not available", code=102),
            _CORE_SYSTEM_RESPONSE,
        ]
        mgr = _mgr(mock_client)
        result = mgr.get_info()
        assert result["model"] == "DS1513+"
        assert result["hostname"] == "nas-prod-01"
        assert result["dsm_version"] == "DSM 7.2.1-69057 Update 7"
        assert result["dsm_build"] == 69057
        assert result["uptime_seconds"] == 123456
        assert result["ram_mb"] == 8192

    def test_fallback_calls_core_system_api(self, mock_client):
        mock_client.request.side_effect = [
            DSMAPIError("not available", code=102),
            _CORE_SYSTEM_RESPONSE,
        ]
        mgr = _mgr(mock_client)
        mgr.get_info()
        calls = mock_client.request.call_args_list
        assert len(calls) == 2
        assert calls[0].args[0] == "SYNO.DSM.Info"
        assert calls[1].args[0] == "SYNO.Core.System"
        assert calls[1].args[1] == "info"
        assert calls[1].kwargs.get("version") == 1

    def test_returns_none_for_missing_fields(self, mock_client):
        mock_client.request.return_value = {}
        mgr = _mgr(mock_client)
        result = mgr.get_info()
        assert result["model"] is None
        assert result["serial"] is None
        assert result["hostname"] is None
        assert result["dsm_version"] is None
        assert result["dsm_build"] is None
        assert result["uptime_seconds"] is None
        assert result["ram_mb"] is None

    def test_uses_server_name_when_hostname_missing(self, mock_client):
        mock_client.request.return_value = {"server_name": "fallback-host"}
        mgr = _mgr(mock_client)
        result = mgr.get_info()
        assert result["hostname"] == "fallback-host"

    def test_uses_firmware_ver_when_version_string_missing(self, mock_client):
        mock_client.request.return_value = {"firmware_ver": "DSM 7.1.1"}
        mgr = _mgr(mock_client)
        result = mgr.get_info()
        assert result["dsm_version"] == "DSM 7.1.1"


class TestEnsure:
    def test_ensure_returns_noop(self, mock_client):
        mock_client.request.return_value = _DSM_INFO_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.ensure()
        assert result["changed"] is False
        assert result["action"] == "noop"
        assert result["info"]["model"] == "DS1513+"

    def test_ensure_dry_run(self, mock_client):
        mock_client.request.return_value = _DSM_INFO_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.ensure(dry_run=True)
        assert result["changed"] is False
        assert result["action"] == "noop"
        assert result["info"]["model"] == "DS1513+"

    def test_ensure_state_present(self, mock_client):
        mock_client.request.return_value = _DSM_INFO_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.ensure(state="present")
        assert result["changed"] is False
        assert "info" in result

    def test_ensure_state_absent(self, mock_client):
        mock_client.request.return_value = _DSM_INFO_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.ensure(state="absent")
        assert result["changed"] is False
        assert result["action"] == "noop"

    def test_ensure_includes_all_info_fields(self, mock_client):
        mock_client.request.return_value = _DSM_INFO_RESPONSE
        mgr = _mgr(mock_client)
        result = mgr.ensure()
        info = result["info"]
        assert "model" in info
        assert "serial" in info
        assert "hostname" in info
        assert "dsm_version" in info
        assert "dsm_build" in info
        assert "uptime_seconds" in info
        assert "ram_mb" in info
