"""FileStation module — file and folder operations via SYNO.FileStation APIs."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import DSMClient


class FileStationManager:
    """SYNO.FileStation operations: upload, download, list, mkdir, delete."""

    def __init__(self, client: "DSMClient") -> None:
        self._c = client

    # ── Folder ops ──────────────────────────────────────────────────────────

    def list_shares(self) -> list[dict]:
        """List all accessible shared folders."""
        resp = self._c.request("SYNO.FileStation.List", "list_share", version=2)
        return resp.get("shares", [])

    def list(
        self,
        folder_path: str,
        offset: int = 0,
        limit: int = 1000,
        additional: list[str] | None = None,
    ) -> list[dict]:
        """List files/folders inside *folder_path*.

        Args:
            folder_path: Absolute NAS path to list.
            offset:      Pagination offset.
            limit:       Max items to return.
            additional:  Extra properties to fetch per item. Available:
                         ``real_path``, ``size``, ``owner``, ``time``,
                         ``perm``, ``type``, ``mount_point_type``.

        Returns:
            List of file/folder dicts. When *additional* is set, each item
            contains an ``additional`` sub-dict with the requested fields.

        Example::

            files = fs.list("/my-share", additional=["size", "time", "owner"])
            for f in files:
                print(f["name"], f["additional"]["size"])
        """
        import json as _json

        params: dict = dict(folder_path=folder_path, offset=offset, limit=limit)
        if additional:
            params["additional"] = _json.dumps(additional)

        resp = self._c.request("SYNO.FileStation.List", "list", version=2, **params)
        return resp.get("files", [])

    def mkdir(self, parent: str, name: str, force_parent: bool = True) -> dict:
        """Create a folder *name* inside *parent*.

        Args:
            parent: Absolute path of the parent folder (e.g. '/by-terraform-state').
            name:   New folder name (e.g. 'poc').
            force_parent: Create intermediate parents if missing.

        Returns:
            Dict with created folder info.
        """
        import json

        resp = self._c.request(
            "SYNO.FileStation.CreateFolder",
            "create",
            version=2,
            folder_path=json.dumps([parent]),
            name=json.dumps([name]),
            force_parent="true" if force_parent else "false",
        )
        folders = resp.get("folders", [])
        return folders[0] if folders else resp

    # ── File ops ─────────────────────────────────────────────────────────────

    def _file_exists(self, dest_folder: str, filename: str) -> bool:
        """Check if a file exists in dest_folder on the NAS."""
        try:
            files = self.list(dest_folder)
            names = [f.get("name", "") for f in files]
            return filename in names
        except Exception:
            return False

    def upload(self, local_path: str, dest_folder: str, overwrite: bool = True,
               dry_run: bool = False) -> dict:
        """Upload a local file to *dest_folder* on the NAS.

        Args:
            local_path:  Path to the local file to upload.
            dest_folder: Absolute NAS folder path (e.g. '/by-terraform-state/poc').
            overwrite:   If True, overwrite existing file. If False, skip upload
                         and return ``{"success": True, "skipped": True}`` when
                         the file already exists (``blSkip`` in raw response).
            dry_run:     If True, check if file exists and return what would happen,
                         without actually uploading.

        Returns:
            Dict with keys:
              - ``success`` (bool)
              - ``skipped`` (bool) — True when file existed and overwrite=False
              - ``file`` (str) — filename on NAS
              - ``pid`` (int) — DSM task pid
              - ``dry_run`` (bool) — True when dry_run=True

        Raises:
            RuntimeError: On API or HTTP error.
        """
        p = PurePosixPath(local_path)

        if dry_run:
            exists = self._file_exists(dest_folder, p.name)
            if exists and not overwrite:
                return {
                    "success": True,
                    "skipped": True,
                    "dry_run": True,
                    "action": "noop",
                    "file": p.name,
                }
            return {
                "success": True,
                "skipped": False,
                "dry_run": True,
                "action": "would_upload" if not exists else "would_overwrite",
                "file": p.name,
            }

        with open(local_path, "rb") as fh:
            content = fh.read()

        # Auth pattern discovered via DevTools:
        # - SynoToken must be in URL query string
        # - Session passed as cookie id= (not _sid form field)
        # - X-Syno-Token header also required
        # - field name is "path" not "dest_folder_path"
        resp = self._c._client.post(
            f"{self._c.base_url}/entry.cgi"
            f"?api=SYNO.FileStation.Upload&method=upload&version=2&SynoToken={self._c._synotoken}",
            headers={"X-Syno-Token": self._c._synotoken},
            cookies={"id": self._c._sid},
            data={
                "path": dest_folder,
                "create_parents": "true",
                "overwrite": "true" if overwrite else "false",
            },
            files={"file": (p.name, content, "application/octet-stream")},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Upload failed: {data.get('error')}")

        # Normalise response: expose blSkip as skipped
        result = data.get("data", {})
        return {
            "success": True,
            "skipped": bool(result.get("blSkip", False)),
            "file": result.get("file", p.name),
            "pid": result.get("pid"),
        }

    def download(self, remote_path: str, local_path: str) -> None:
        """Download a single file from the NAS.

        Args:
            remote_path: Absolute NAS file path (e.g. '/by-terraform-state/poc/terraform.tfstate').
            local_path:  Local destination path.
        """
        resp = self._c._client.get(
            f"{self._c.base_url}/entry.cgi",
            headers={"X-SYNO-TOKEN": self._c._synotoken},
            params={
                "_sid": self._c._sid,
                "api": "SYNO.FileStation.Download",
                "version": "2",
                "method": "download",
                "path": remote_path,
                "mode": "download",
            },
        )
        resp.raise_for_status()
        with open(local_path, "wb") as fh:
            fh.write(resp.content)

    def delete(self, path: str, dry_run: bool = False) -> dict:
        """Delete a file or folder at *path*.

        Args:
            path: Absolute NAS path to delete.
            dry_run: If True, return what would be deleted without making changes.

        Returns:
            API response dict (or dry_run info dict).
        """
        if dry_run:
            return {
                "changed": True,
                "dry_run": True,
                "action": "would_delete",
                "target": path,
            }
        resp = self._c.request(
            "SYNO.FileStation.Delete",
            "start",
            version=2,
            path=path,
            accurate_progress="false",
        )
        return resp
