from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional
import requests

@dataclass
class APIConfig:
    url: str
    user: str
    app_password: str
    timeout: int = 60

class APIError(RuntimeError):
    def __init__(self, status_code: int, payload: Dict[str, Any]):
        self.status_code = status_code
        self.payload = payload
        msg = payload.get("message") if isinstance(payload, dict) else str(payload)
        super().__init__(f"APIError {status_code}: {msg}")

class WPDriveAPI:
    def __init__(self, cfg: APIConfig):
        self.cfg = cfg
        self.base = cfg.url.rstrip("/") + "/wp-json/wpdrive/v1"
        self.session = requests.Session()
        self.session.auth = (cfg.user, cfg.app_password)

    def _req(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self.base + path
        timeout = kwargs.pop("timeout", self.cfg.timeout)
        r = self.session.request(method, url, timeout=timeout, **kwargs)
        if r.status_code >= 400:
            try:
                data = r.json()
            except Exception:
                data = {"message": r.text[:2000]}
            raise APIError(r.status_code, data)
        return r

    def changes(self, since: int, limit: int = 500) -> Dict[str, Any]:
        r = self._req("GET", "/changes", params={"since": int(since), "limit": int(limit)})
        return r.json()

    def upload_init(self, rel_path: str, size: int, mtime: int, crc32: int, base_rev: int, device_id: str, device_label: str) -> Dict[str, Any]:
        payload = {
            "rel_path": rel_path,
            "size": int(size),
            "mtime": int(mtime),
            "crc32": str(int(crc32)),
            "base_rev": int(base_rev),
            "device_id": device_id,
            "device_label": device_label,
        }
        r = self._req("POST", "/upload/init", json=payload)
        return r.json()

    def upload_chunk(self, upload_id: str, offset: int, data: bytes) -> Dict[str, Any]:
        r = self._req(
            "POST",
            "/upload/chunk",
            params={"upload_id": upload_id, "offset": int(offset)},
            data=data,
            headers={"Content-Type": "application/octet-stream"},
        )
        return r.json()

    def upload_finalize(self, upload_id: str) -> Dict[str, Any]:
        r = self._req("POST", "/upload/finalize", json={"upload_id": upload_id})
        return r.json()

    def delete(self, rel_path: str, device_id: str) -> Dict[str, Any]:
        r = self._req("POST", "/delete", json={"rel_path": rel_path, "device_id": device_id})
        return r.json()

    def download_stream(self, rel_path: str, chunk: int = 1024 * 1024) -> Iterator[bytes]:
        url = self.base + "/download"
        r = self.session.get(url, params={"path": rel_path}, stream=True, timeout=self.cfg.timeout)
        if r.status_code >= 400:
            try:
                data = r.json()
            except Exception:
                data = {"message": r.text[:2000]}
            raise APIError(r.status_code, data)
        for part in r.iter_content(chunk_size=chunk):
            if part:
                yield part
