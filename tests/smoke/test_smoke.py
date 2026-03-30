"""Smoke tests — verify imports and basic instantiation without network access."""

import pytest

pytestmark = pytest.mark.smoke


class TestImports:
    def test_import_dsm_client(self):
        from synology_dsm import DSMClient

        assert DSMClient is not None

    def test_import_user_manager(self):
        from synology_dsm import UserManager

        assert UserManager is not None

    def test_import_group_manager(self):
        from synology_dsm import GroupManager

        assert GroupManager is not None

    def test_import_share_manager(self):
        from synology_dsm import ShareManager

        assert ShareManager is not None

    def test_import_filestation_manager(self):
        from synology_dsm import FileStationManager

        assert FileStationManager is not None

    def test_import_nfs_manager(self):
        from synology_dsm import NFSManager

        assert NFSManager is not None

    def test_import_quota_manager(self):
        from synology_dsm import QuotaManager

        assert QuotaManager is not None

    def test_import_bandwidth_manager(self):
        from synology_dsm import BandwidthManager

        assert BandwidthManager is not None

    def test_import_storage_manager(self):
        from synology_dsm import StorageManager

        assert StorageManager is not None

    def test_import_traffic_control_manager(self):
        from synology_dsm import TrafficControlManager

        assert TrafficControlManager is not None

    def test_import_exceptions(self):
        from synology_dsm import (
            DSMAPIError,
            DSMAuthError,
            DSMConnectionError,
            DSMError,
            DSMNotFoundError,
            DSMPermissionError,
            DSMSessionError,
        )

        assert all(
            [
                DSMError,
                DSMAPIError,
                DSMAuthError,
                DSMConnectionError,
                DSMNotFoundError,
                DSMPermissionError,
                DSMSessionError,
            ]
        )

    def test_import_credentials(self):
        from synology_dsm import DSMCredentials, EnvCredentialProvider, get_credentials

        assert all([DSMCredentials, EnvCredentialProvider, get_credentials])


class TestInstantiation:
    def test_dsm_client_instantiation(self):
        from synology_dsm import DSMClient

        client = DSMClient("test-host", port=5001, https=True, verify_ssl=False)
        assert client.base_url == "https://test-host:5001/webapi"
        assert client._timeout == 30

    def test_dsm_client_custom_timeout(self):
        from synology_dsm import DSMClient

        client = DSMClient("test-host", timeout=90)
        assert client._timeout == 90

    def test_user_manager_instantiation(self, mock_client):
        from synology_dsm import UserManager

        mgr = UserManager(mock_client)
        assert mgr._c is mock_client

    def test_group_manager_instantiation(self, mock_client):
        from synology_dsm import GroupManager

        mgr = GroupManager(mock_client)
        assert mgr._c is mock_client

    def test_share_manager_instantiation(self, mock_client):
        from synology_dsm import ShareManager

        mgr = ShareManager(mock_client)
        assert mgr._c is mock_client

    def test_filestation_manager_instantiation(self, mock_client):
        from synology_dsm import FileStationManager

        mgr = FileStationManager(mock_client)
        assert mgr._c is mock_client

    def test_nfs_manager_instantiation(self, mock_client):
        from synology_dsm import NFSManager

        mgr = NFSManager(mock_client)
        assert mgr._c is mock_client

    def test_quota_manager_instantiation(self, mock_client):
        from synology_dsm import QuotaManager

        mgr = QuotaManager(mock_client)
        assert mgr._c is mock_client

    def test_bandwidth_manager_instantiation(self, mock_client):
        from synology_dsm import BandwidthManager

        mgr = BandwidthManager(mock_client)
        assert mgr._c is mock_client

    def test_storage_manager_instantiation(self, mock_client):
        from synology_dsm import StorageManager

        mgr = StorageManager(mock_client)
        assert mgr._c is mock_client

    def test_traffic_control_manager_instantiation(self, mock_client):
        from synology_dsm import TrafficControlManager

        mgr = TrafficControlManager(mock_client)
        assert mgr._c is mock_client
