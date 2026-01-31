from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Optional

from .sync_engine import SyncEngine
from .state import StateDB
from .util import load_config, save_config, default_config, ensure_dir

def _find_config(start: Path) -> dict:
    cur = start.expanduser().resolve()
    while True:
        cfg_path = cur / ".wpdrive" / "config.json"
        if cfg_path.exists():
            return load_config(cfg_path)
        if cur.parent == cur:
            break
        cur = cur.parent
    print("ERROR: Could not find .wpdrive/config.json. Run `wpdrive init` first.", file=sys.stderr)
    raise SystemExit(2)

def cmd_init(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    ensure_dir(root)
    cfg_dir = root / ".wpdrive"
    ensure_dir(cfg_dir)
    cfg_path = cfg_dir / "config.json"

    cfg = default_config()
    cfg["root"] = str(root)
    cfg["url"] = args.url.rstrip("/")
    cfg["user"] = args.user
    cfg["app_password"] = args.app_password
    if args.chunk_size_mb is not None:
        cfg["chunk_size_mb"] = int(args.chunk_size_mb)

    save_config(cfg_path, cfg)
    db = StateDB(root)
    db.initialize()
    print(f"Initialized WPDrive in {root}")
    print(f"Config written to {cfg_path}")

def cmd_sync(args: argparse.Namespace) -> None:
    start = Path(args.root).expanduser().resolve() if args.root else Path.cwd()
    cfg = _find_config(start)
    engine = SyncEngine(cfg)
    engine.sync_once()

def cmd_daemon(args: argparse.Namespace) -> None:
    start = Path(args.root).expanduser().resolve() if args.root else Path.cwd()
    cfg = _find_config(start)
    engine = SyncEngine(cfg)
    engine.run_daemon(interval=args.interval)

def main() -> int:
    p = argparse.ArgumentParser(prog="wpdrive", description="WPDrive sync client")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize a sync root and write config")
    p_init.add_argument("--root", required=True, help="Local sync root directory")
    p_init.add_argument("--url", required=True, help="WordPress site base URL (e.g. https://example.com)")
    p_init.add_argument("--user", required=True, help="WordPress username for sync (role WPDrive Sync recommended)")
    p_init.add_argument("--app-password", required=True, help="WordPress Application Password")
    p_init.add_argument("--chunk-size-mb", type=int, default=None, help="Preferred chunk size in MB (default 32)")
    p_init.set_defaults(func=cmd_init)

    p_sync = sub.add_parser("sync", help="Run a one-shot sync")
    p_sync.add_argument("--root", default=None, help="Optional root path if not running inside the sync folder")
    p_sync.set_defaults(func=cmd_sync)

    p_daemon = sub.add_parser("daemon", help="Run continuous sync (polling)")
    p_daemon.add_argument("--root", default=None, help="Optional root path if not running inside the sync folder")
    p_daemon.add_argument("--interval", type=int, default=10, help="Polling interval seconds (default 10)")
    p_daemon.set_defaults(func=cmd_daemon)

    args = p.parse_args()
    args.func(args)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
