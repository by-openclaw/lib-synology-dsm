# SPDX-License-Identifier: MIT
"""SYNO.FileStation — file and folder operations.

Primary API: SYNO.FileStation.List v2
Additional APIs (via direct client calls):
    SYNO.FileStation.CreateFolder v2
    SYNO.FileStation.Delete v2
    SYNO.FileStation.Upload v3 (multipart — custom HTTP handling)
    SYNO.FileStation.Download v2

Public methods: list(), get(), ensure()
Internal ops: _mkdir(), _delete_path(), _upload(), _download(), _build_multipart()

DECISION (2026-03-31): Use self._client.request() directly for non-primary APIs.
Do NOT override _request(). BaseManager ABC contract preserved.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import PurePosixPath
from typing import Any

from synology_dsm_v2.base import Action, BaseManager, ClientProtocol, EnsureResult, State
from synology_dsm_v2.exceptions import DSMConnectionError

_BOUNDARY = b"----DSMUploadBoundary1234567890"  # pragma: allowlist secret — multipart boundary, not a credential


class FileStationManager(BaseManager):
    """SYNO.FileStation — folder ensure + file upload/download.

    Uses multiple FileStation APIs. The primary API (SYNO.FileStation.List)
    is used via self._request(). All other APIs use self._client.request()
    directly, each documented with a comment.

    Usage::

        fs = FileStationManager(client)

        # Ensure folder exists
        result = fs.ensure("/my-share/subfolder", state=State.PRESENT)

        # Upload a file (not via ensure — use _upload directly or wrap)
        fs._upload("/local/file.txt", "/my-share/subfolder")

        # Download a file
        fs._download("/my-share/subfolder/file.txt", "/local/file.txt")
    """

    def __init__(self, client: ClientProtocol) -> None:
        super().__init__(client, api="SYNO.FileStation.List", version=2)

    # -- Public: read --

    def list(self, folder_path: str | None = None) -> list[dict[str, Any]]:
        """List files/folders inside folder_path.

        Args:
            folder_path: Absolute NAS path. If None, lists shared folders.
        """
        if folder_path is None:
            data = self._request("list_share")
            return data.get("shares", [])
        data = self._request("list", folder_path=folder_path, offset=0, limit=1000)
        return data.get("files", [])

    def get(self, name: str) -> dict[str, Any] | None:
        """Check if a file/folder exists at path. Returns item dict or None.

        Args:
            name: Absolute NAS path (e.g. "/my-share/subfolder").
        """
        p = PurePosixPath(name)
        parent = str(p.parent)
        target_name = p.name
        try:
            items = self.list(folder_path=parent)
            for item in items:
                if item.get("name") == target_name:
                    return item
        except Exception:
            pass
        return None

    # -- Public: write (only ensure) --

    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs: Any,
    ) -> EnsureResult:
        """Idempotent folder management.

        state=PRESENT: create folder if missing, noop if exists.
        state=ABSENT: delete if exists, noop if already gone.
        dry_run=True: preview without API calls.

        Args:
            name: Absolute NAS path (e.g. "/my-share/subfolder").
        """
        current = self.get(name)

        if state == State.PRESENT:
            return self._ensure_present(name, current, dry_run, **kwargs)
        elif state == State.ABSENT:
            return self._ensure_absent(name, current, dry_run)
        else:
            raise ValueError(f"Invalid state: {state!r} — use State.PRESENT or State.ABSENT")

    # -- Private: operations --

    def _mkdir(self, parent: str, folder_name: str) -> dict[str, Any]:
        """Create a folder."""
        # Multi-API: direct client call — BaseManager contract preserved
        data = self._client.request(
            api="SYNO.FileStation.CreateFolder",
            method="create",
            version=2,
            folder_path=json.dumps([parent]),
            name=json.dumps([folder_name]),
            force_parent="true",
        )
        folders = data.get("folders", [])
        return folders[0] if folders else data

    def _delete_path(self, path: str) -> dict[str, Any]:
        """Delete a file or folder."""
        # Multi-API: direct client call — BaseManager contract preserved
        return self._client.request(
            api="SYNO.FileStation.Delete",
            method="start",
            version=2,
            path=path,
            accurate_progress="false",
        )

    def _build_multipart(
        self, fields: dict[str, str], file_name: str, file_content: bytes
    ) -> bytes:
        """Build a multipart/form-data body for FileStation upload."""
        body = b""
        for key, val in fields.items():
            body += b"--" + _BOUNDARY + b"\r\n"
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            body += val.encode() + b"\r\n"
        body += b"--" + _BOUNDARY + b"\r\n"
        body += (
            f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        body += file_content + b"\r\n"
        body += b"--" + _BOUNDARY + b"--\r\n"
        return body

    def _upload(
        self,
        local_path: str,
        dest_folder: str,
        overwrite: bool = True,
        dry_run: bool = False,
    ) -> EnsureResult:
        """Upload a local file to dest_folder on the NAS.

        Uses custom multipart HTTP — SynoToken in URL query, session as cookie.
        """
        p = PurePosixPath(local_path)

        if dry_run:
            exists = self.get(f"{dest_folder}/{p.name}") is not None
            if exists and not overwrite:
                return EnsureResult(changed=False, action=Action.NOOP, dry_run=True)
            action = Action.WOULD_UPLOAD
            return EnsureResult(changed=False, action=action, dry_run=True)

        with open(local_path, "rb") as fh:
            content = fh.read()

        # Auth pattern: SynoToken in URL query, session as cookie id=
        url = (
            f"{self._client.base_url}/entry.cgi"
            f"?api=SYNO.FileStation.Upload&method=upload&version=3"
            f"&SynoToken={urllib.parse.quote(self._client.synotoken)}"
        )
        body = self._build_multipart(
            fields={
                "path": dest_folder,
                "create_parents": "true",
                "overwrite": "true" if overwrite else "false",
            },
            file_name=p.name,
            file_content=content,
        )
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={_BOUNDARY.decode()}")
        req.add_header("X-Syno-Token", self._client.synotoken)
        req.add_header("Cookie", f"id={self._client.sid}")

        ssl_ctx = getattr(self._client, "_ssl_ctx", None)
        timeout = getattr(self._client, "_timeout", 60)

        try:
            with urllib.request.urlopen(  # nosec B310 — URL built from self._client._host (trusted config, not user input)
                req, context=ssl_ctx, timeout=max(timeout, 60)
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise DSMConnectionError(
                f"FileStation upload failed — cannot reach NAS: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise DSMConnectionError(f"FileStation upload network error: {exc}") from exc

        if not data.get("success"):
            raise RuntimeError(f"Upload failed: {data.get('error')}")

        result_data = data.get("data", {})
        skipped = bool(result_data.get("blSkip", False))
        action = Action.NOOP if skipped else Action.UPLOADED
        return EnsureResult(
            changed=not skipped,
            action=action,
            after={"file": result_data.get("file", p.name), "pid": result_data.get("pid")},
        )

    def _download(self, remote_path: str, local_path: str) -> EnsureResult:
        """Download a single file from the NAS."""
        params = urllib.parse.urlencode(
            {
                "_sid": self._client.sid,
                "api": "SYNO.FileStation.Download",
                "version": "2",
                "method": "download",
                "path": remote_path,
                "mode": "download",
            }
        )
        url = f"{self._client.base_url}/entry.cgi?{params}"
        req = urllib.request.Request(url, method="GET")
        req.add_header("X-SYNO-TOKEN", self._client.synotoken)

        ssl_ctx = getattr(self._client, "_ssl_ctx", None)
        timeout = getattr(self._client, "_timeout", 60)

        try:
            with urllib.request.urlopen(  # nosec B310 — URL built from self._client.base_url (trusted config, not user input)
                req, context=ssl_ctx, timeout=max(timeout, 60)
            ) as resp:
                with open(local_path, "wb") as fh:
                    fh.write(resp.read())
        except urllib.error.URLError as exc:
            raise DSMConnectionError(
                f"FileStation download failed — cannot reach NAS: {exc.reason}"
            ) from exc
        except OSError as exc:
            raise DSMConnectionError(f"FileStation download network error: {exc}") from exc

        return EnsureResult(
            changed=True,
            action=Action.DOWNLOADED,
            after={"file": PurePosixPath(remote_path).name, "local_path": local_path},
        )

    # -- Private: ensure logic --

    def _ensure_present(
        self,
        path: str,
        current: dict[str, Any] | None,
        dry_run: bool,
        **kwargs: Any,
    ) -> EnsureResult:
        """Create folder if missing, noop if exists."""
        if current is not None:
            return EnsureResult(changed=False, action=Action.NOOP, before=current)

        if dry_run:
            return EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True)

        p = PurePosixPath(path)
        self._mkdir(str(p.parent), p.name)
        after = self.get(path)
        return EnsureResult(changed=True, action=Action.CREATED, after=after)

    def _ensure_absent(
        self,
        path: str,
        current: dict[str, Any] | None,
        dry_run: bool,
    ) -> EnsureResult:
        """Delete if exists, noop if already gone."""
        if current is None:
            return EnsureResult(changed=False, action=Action.NOOP)

        if dry_run:
            return EnsureResult(
                changed=False, action=Action.WOULD_DELETE, before=current, dry_run=True
            )

        self._delete_path(path)
        return EnsureResult(changed=True, action=Action.DELETED, before=current)
