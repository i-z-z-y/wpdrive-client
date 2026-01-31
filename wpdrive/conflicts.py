from __future__ import annotations
from datetime import datetime, timezone
import platform
from pathlib import Path
from typing import Optional

def conflict_name(rel_path: str, device_label: Optional[str] = None, when: Optional[datetime] = None) -> str:
    if not device_label:
        device_label = platform.node() or "device"
    device_label = "".join(ch if (ch.isalnum() or ch in " _.-") else "_" for ch in device_label).strip() or "device"

    when = when or datetime.now(timezone.utc)
    ts = when.strftime("%Y-%m-%d_%H-%M-%S")
    info = f"conflict from {device_label} {ts}"

    p = Path(rel_path)
    if p.suffix:
        return str(p.with_name(f"{p.stem} ({info}){p.suffix}"))
    return f"{rel_path} ({info})"
