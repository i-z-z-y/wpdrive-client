from __future__ import annotations
import os
import platform
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .api import WPDriveAPI, APIConfig, APIError
from .state import StateDB
from .scan import scan_files
from .util import crc32_file, ensure_dir
from .conflicts import conflict_name

@dataclass
class LocalFileInfo:
    abs_path: Path
    size: int
    mtime: int
    crc32: int = 0

class SyncEngine:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.root = Path(cfg["root"]).expanduser().resolve()
        self.ignore = cfg.get("ignore") or [".wpdrive/**"]
        self.chunk_size_mb = int(cfg.get("chunk_size_mb", 32))
        self.min_chunk_size_mb = int(cfg.get("min_chunk_size_mb", 4))
        self.timeout = int(cfg.get("timeout_seconds", 60))
        self.device_label = cfg.get("device_label") or platform.node() or "device"

        self.db = StateDB(self.root)
        self.db.initialize()
        self.device_id = self.db.get_device_id()

        api_cfg = APIConfig(
            url=cfg["url"],
            user=cfg["user"],
            app_password=cfg["app_password"],
            timeout=self.timeout,
        )
        self.api = WPDriveAPI(api_cfg)

        self.tmp_dir = self.root / ".wpdrive" / "tmp"
        ensure_dir(self.tmp_dir)

    def run_daemon(self, interval: int = 10) -> None:
        interval = max(3, int(interval))
        print(f"[wpdrive] daemon mode: interval={interval}s root={self.root}")
        while True:
            try:
                self.sync_once()
            except Exception as e:
                print(f"[wpdrive] ERROR: {e}")
            time.sleep(interval)

    def sync_once(self) -> None:
        if not self.root.exists():
            raise RuntimeError(f"Root does not exist: {self.root}")

        print(f"[wpdrive] sync: root={self.root}")
        self.pull_changes()
        self.push_local_changes()
        print("[wpdrive] sync complete")

    # ----------------------------
    # Pull phase
    # ----------------------------
    def pull_changes(self) -> None:
        since = self.db.get_last_change_id()
        next_since = since
        print(f"[wpdrive] pulling changes since {since}")

        while True:
            payload = self.api.changes(since=next_since, limit=500)
            changes = payload.get("changes", [])
            if not changes:
                break

            for ch in changes:
                cid = int(ch["change_id"])
                if cid > next_since:
                    next_since = cid

                # Skip our own changes to reduce churn
                if ch.get("device_id") and ch["device_id"] == self.device_id:
                    continue

                action = ch.get("action")
                rel_path = ch.get("rel_path")
                if not rel_path:
                    continue

                if action == "upsert":
                    self.apply_remote_upsert(ch)
                elif action == "delete":
                    self.apply_remote_delete(ch)

            self.db.set_last_change_id(next_since)

        if next_since != since:
            print(f"[wpdrive] pulled up to change_id {next_since}")

    def apply_remote_upsert(self, ch: dict) -> None:
        rel = ch["rel_path"]
        rev = int(ch.get("rev") or 0)
        size = int(ch.get("size") or 0)
        mtime = int(ch.get("mtime") or 0)
        crc32_remote = int(ch.get("crc32") or 0)

        abs_path = self.root / rel
        ensure_dir(abs_path.parent)

        # If local has unpushed modification, preserve as conflict copy before overwriting.
        state = self.db.get_file(rel)
        if abs_path.exists() and state is not None:
            st_size, st_mtime, st_crc32, st_rev = state
            cur_stat = abs_path.stat()
            cur_size = int(cur_stat.st_size)
            cur_mtime = int(cur_stat.st_mtime)
            if cur_size != st_size or cur_mtime != st_mtime:
                cur_crc = crc32_file(abs_path)
                if cur_crc != st_crc32:
                    conflict_rel = conflict_name(rel, self.device_label)
                    conflict_abs = self.root / conflict_rel
                    ensure_dir(conflict_abs.parent)
                    print(f"[wpdrive] local modified vs state; stashing conflict: {conflict_rel}")
                    shutil.move(str(abs_path), str(conflict_abs))

        tmp_path = self.tmp_dir / (abs_path.name + ".download.part")
        if tmp_path.exists():
            tmp_path.unlink()

        print(f"[wpdrive] downloading {rel} (rev {rev})")
        with open(tmp_path, "wb") as f:
            for chunk in self.api.download_stream(rel):
                f.write(chunk)

        got_crc = crc32_file(tmp_path)
        if crc32_remote and got_crc != crc32_remote:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError(f"CRC mismatch downloading {rel}: expected {crc32_remote} got {got_crc}")

        if abs_path.exists():
            abs_path.unlink()
        tmp_path.replace(abs_path)

        try:
            os.utime(abs_path, (mtime, mtime))
        except Exception:
            pass

        self.db.upsert_file(rel, size=size, mtime=mtime, crc32=got_crc, server_rev=rev)

    def apply_remote_delete(self, ch: dict) -> None:
        rel = ch["rel_path"]
        deleted_size = ch.get("deleted_size")
        deleted_crc32 = ch.get("deleted_crc32")
        deleted_crc32 = int(deleted_crc32) if deleted_crc32 is not None else None
        deleted_size = int(deleted_size) if deleted_size is not None else None

        abs_path = self.root / rel
        if not abs_path.exists():
            self.db.delete_file(rel)
            return

        local_crc = crc32_file(abs_path)
        local_size = abs_path.stat().st_size

        if deleted_crc32 is not None and deleted_size is not None and local_crc == deleted_crc32 and local_size == deleted_size:
            print(f"[wpdrive] deleting (matched tombstone): {rel}")
            abs_path.unlink()
        else:
            conflict_rel = conflict_name(rel, self.device_label)
            conflict_abs = self.root / conflict_rel
            ensure_dir(conflict_abs.parent)
            print(f"[wpdrive] delete mismatch; preserving as conflict: {conflict_rel}")
            shutil.move(str(abs_path), str(conflict_abs))

        self.db.delete_file(rel)

    # ----------------------------
    # Push phase
    # ----------------------------
    def push_local_changes(self) -> None:
        files = scan_files(self.root, self.ignore)

        current: Dict[str, LocalFileInfo] = {}
        for rel, absp in files.items():
            st = absp.stat()
            current[rel] = LocalFileInfo(
                abs_path=absp,
                size=int(st.st_size),
                mtime=int(st.st_mtime),
                crc32=0,
            )

        to_upload: List[str] = []
        for rel, info in current.items():
            state = self.db.get_file(rel)
            if state is None:
                to_upload.append(rel)
                continue
            st_size, st_mtime, st_crc, st_rev = state
            if info.size != st_size or info.mtime != st_mtime:
                info.crc32 = crc32_file(info.abs_path)
                if info.crc32 != st_crc:
                    to_upload.append(rel)

        to_delete: List[str] = []
        for rel, *_ in self.db.iter_files():
            if rel not in current:
                to_delete.append(rel)

        if not to_upload and not to_delete:
            print("[wpdrive] no local changes to push")
            return

        for rel in sorted(to_upload):
            self.push_one_file(rel, current[rel])

        for rel in sorted(to_delete):
            self.push_one_delete(rel)

    def push_one_file(self, rel: str, info: LocalFileInfo) -> None:
        if info.crc32 == 0:
            info.crc32 = crc32_file(info.abs_path)

        state = self.db.get_file(rel)
        base_rev = state[3] if state else 0

        print(f"[wpdrive] uploading {rel} (base_rev={base_rev})")
        init = self.api.upload_init(
            rel_path=rel,
            size=info.size,
            mtime=info.mtime,
            crc32=info.crc32,
            base_rev=base_rev,
            device_id=self.device_id,
            device_label=self.device_label,
        )
        upload_id = init["upload_id"]
        decided_path = init["decided_path"]

        chunk_mb = self.chunk_size_mb
        min_mb = self.min_chunk_size_mb
        offset = 0

        with open(info.abs_path, "rb") as f:
            while offset < info.size:
                f.seek(offset)
                want = min(info.size - offset, chunk_mb * 1024 * 1024)
                data = f.read(want)
                if not data:
                    break
                try:
                    self.api.upload_chunk(upload_id=upload_id, offset=offset, data=data)
                    offset += len(data)
                except APIError as e:
                    if e.status_code in (413, 408, 504, 500, 502, 503):
                        new_mb = max(min_mb, max(1, chunk_mb // 2))
                        if new_mb < chunk_mb:
                            print(f"[wpdrive] chunk failed ({e.status_code}); backing off {chunk_mb}MB -> {new_mb}MB")
                            chunk_mb = new_mb
                            continue
                    raise

        fin = self.api.upload_finalize(upload_id)
        server_rel = fin["rel_path"]
        rev = int(fin["rev"])

        # If server renamed to conflict path, rename locally to match
        if server_rel != rel:
            src = self.root / rel
            dst = self.root / server_rel
            ensure_dir(dst.parent)
            if src.exists():
                print(f"[wpdrive] server conflict rename; renaming local to {server_rel}")
                if dst.exists():
                    alt_rel = conflict_name(server_rel, self.device_label)
                    dst = self.root / alt_rel
                shutil.move(str(src), str(dst))
            rel = server_rel
            info = LocalFileInfo(abs_path=dst, size=info.size, mtime=info.mtime, crc32=info.crc32)

        st = (self.root / rel).stat()
        size = int(st.st_size)
        mtime = int(st.st_mtime)
        crc = crc32_file(self.root / rel)
        self.db.upsert_file(rel, size=size, mtime=mtime, crc32=crc, server_rev=rev)

    def push_one_delete(self, rel: str) -> None:
        print(f"[wpdrive] deleting remote {rel}")
        self.api.delete(rel_path=rel, device_id=self.device_id)
        self.db.delete_file(rel)
