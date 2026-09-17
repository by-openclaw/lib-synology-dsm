# SPDX-License-Identifier: MIT
"""Tests for exception hierarchy, error code mapping, and repr."""

from __future__ import annotations

import pytest
from synology_dsm_v2.exceptions import (
    ERROR_DESCRIPTIONS,
    ERROR_MAP,
    DSMAPIError,
    DSMAuthError,
    DSMConnectionError,
    DSMError,
    DSMInvalidOperationError,
    DSMInvalidParameterError,
    DSMNotFoundError,
    DSMPermissionError,
    DSMResourceNotFoundError,
    DSMSessionError,
)


class TestDSMErrorBase:
    def test_message_and_code(self) -> None:
        err = DSMError("something broke", code=100)
        assert str(err) == "[100] something broke"
        assert err.code == 100

    def test_message_without_code(self) -> None:
        err = DSMError("network issue")
        assert str(err) == "network issue"
        assert err.code is None

    def test_repr(self) -> None:
        err = DSMError("test", code=42)
        assert "DSMError" in repr(err)
        assert "42" in repr(err)
        assert "test" in repr(err)

    def test_is_exception(self) -> None:
        assert issubclass(DSMError, Exception)


class TestExceptionHierarchy:
    """Every exception is a subclass of DSMError."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            DSMAuthError,
            DSMPermissionError,
            DSMNotFoundError,
            DSMSessionError,
            DSMInvalidParameterError,
            DSMInvalidOperationError,
            DSMAPIError,
            DSMResourceNotFoundError,
            DSMConnectionError,
        ],
    )
    def test_subclass_of_dsm_error(self, exc_class: type[DSMError]) -> None:
        assert issubclass(exc_class, DSMError)

    @pytest.mark.parametrize(
        "exc_class",
        [
            DSMAuthError,
            DSMPermissionError,
            DSMNotFoundError,
            DSMSessionError,
            DSMInvalidParameterError,
            DSMInvalidOperationError,
            DSMAPIError,
        ],
    )
    def test_subclass_accepts_code(self, exc_class: type[DSMError]) -> None:
        err = exc_class("test", code=999)
        assert err.code == 999
        assert "999" in repr(err)

    def test_resource_not_found_has_no_code(self) -> None:
        err = DSMResourceNotFoundError("User 'bob' not found")
        assert err.code is None
        assert "bob" in str(err)

    def test_connection_error_has_no_code(self) -> None:
        err = DSMConnectionError("NAS unreachable")
        assert err.code is None
        assert "NAS unreachable" in str(err)


class TestErrorCodeMapping:
    """Every known DSM error code maps to the correct exception type."""

    @pytest.mark.parametrize(
        "code,expected_type",
        [
            # Auth
            (400, DSMAuthError),
            (401, DSMAuthError),
            (402, DSMPermissionError),
            (403, DSMAuthError),
            (407, DSMAuthError),
            (411, DSMAuthError),
            # Permission
            (105, DSMPermissionError),
            (115, DSMPermissionError),
            (160, DSMPermissionError),
            # Session
            (106, DSMSessionError),
            (107, DSMSessionError),
            (119, DSMSessionError),
            # Not found
            (102, DSMNotFoundError),
            (104, DSMNotFoundError),
            # Invalid parameter
            (100, DSMInvalidParameterError),
            (101, DSMInvalidParameterError),
            (103, DSMInvalidParameterError),
            (114, DSMInvalidParameterError),
            (1001, DSMInvalidParameterError),
            # Invalid operation
            (117, DSMInvalidOperationError),
            # IP mismatch
            (150, DSMAuthError),
        ],
    )
    def test_error_code_maps_correctly(self, code: int, expected_type: type[DSMError]) -> None:
        assert ERROR_MAP[code] is expected_type

    def test_unknown_code_not_in_map(self) -> None:
        """Unknown codes should NOT be in ERROR_MAP — they fall back to DSMAPIError."""
        assert 12345 not in ERROR_MAP

    def test_every_mapped_code_has_description(self) -> None:
        """Every code in ERROR_MAP should also have a description."""
        for code in ERROR_MAP:
            assert (
                code in ERROR_DESCRIPTIONS
            ), f"Code {code} in ERROR_MAP but missing from ERROR_DESCRIPTIONS"


class TestErrorDescriptions:
    def test_success_code(self) -> None:
        assert ERROR_DESCRIPTIONS[0] == "Success"

    def test_auth_error_description(self) -> None:
        assert "incorrect password" in ERROR_DESCRIPTIONS[400]

    def test_session_timeout_description(self) -> None:
        assert "timeout" in ERROR_DESCRIPTIONS[106].lower()

    def test_share_name_hint(self) -> None:
        """Error 2301 should hint about the share_name vs sharename gotcha."""
        assert "share_name" in ERROR_DESCRIPTIONS[2301]


class TestExceptionCatchPatterns:
    """Callers should be able to catch exceptions at different levels."""

    def test_catch_all_dsm_errors(self) -> None:
        with pytest.raises(DSMError):
            raise DSMAuthError("bad password", code=400)

    def test_catch_specific_error(self) -> None:
        with pytest.raises(DSMAuthError):
            raise DSMAuthError("bad password", code=400)

    def test_auth_not_caught_by_session(self) -> None:
        """DSMAuthError should NOT be caught by except DSMSessionError."""
        with pytest.raises(DSMAuthError):
            try:
                raise DSMAuthError("bad password", code=400)
            except DSMSessionError:
                pass  # Should not catch this

    def test_connection_error_caught_by_base(self) -> None:
        with pytest.raises(DSMError):
            raise DSMConnectionError("NAS unreachable")
