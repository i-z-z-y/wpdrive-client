from __future__ import annotations
import json
import time
import zlib
from pathlib import Path
from typing import Any, Dict, List

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def default_config() -> Dict[str, Any]:
    return {
        "root": "",
        "url": "",
        "user": "",
        "app_password": "",
        "chunk_size_mb": 32,
        "min_chunk_size_mb": 4,
        "timeout_seconds": 60,
        "ignore": [".wpdrive/**"],
        "device_label": None,
    }

def load_config(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    base = default_config()
    base.update(cfg)
    return base

def save_config(path: Path, cfg: Dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, sort_keys=True)

def to_rel_posix(root: Path, abs_path: Path) -> str:
    rel = abs_path.relative_to(root).as_posix()
    return rel.lstrip("/")

def crc32_file(path: Path, chunk_size: int = 4 * 1024 * 1024) -> int:
    crc = 0
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            crc = zlib.crc32(data, crc)
    return crc & 0xFFFFFFFF

def now_utc_ts() -> int:
    return int(time.time())
