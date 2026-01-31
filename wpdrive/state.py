from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterator, Optional, Tuple

from .util import ensure_dir

class StateDB:
    def __init__(self, root: Path):
        self.root = root
        self.dir = root / ".wpdrive"
        self.path = self.dir / "state.db"

    def connect(self) -> sqlite3.Connection:
        ensure_dir(self.dir)
        con = sqlite3.connect(self.path)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def initialize(self) -> None:
        con = self.connect()
        try:
            con.executescript(
                "CREATE TABLE IF NOT EXISTS meta ("
                " key TEXT PRIMARY KEY,"
                " value TEXT"
                ");"
                "CREATE TABLE IF NOT EXISTS files ("
                " rel_path TEXT PRIMARY KEY,"
                " size INTEGER NOT NULL,"
                " mtime INTEGER NOT NULL,"
                " crc32 INTEGER NOT NULL,"
                " server_rev INTEGER NOT NULL DEFAULT 0"
                ");"
            )
            con.commit()
        finally:
            con.close()

    def get_meta(self, key: str) -> Optional[str]:
        con = self.connect()
        try:
            cur = con.execute("SELECT value FROM meta WHERE key=?", (key,))
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            con.close()

    def set_meta(self, key: str, value: str) -> None:
        con = self.connect()
        try:
            con.execute(
                "INSERT INTO meta(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            con.commit()
        finally:
            con.close()

    def get_last_change_id(self) -> int:
        v = self.get_meta("last_change_id")
        return int(v) if v else 0

    def set_last_change_id(self, cid: int) -> None:
        self.set_meta("last_change_id", str(int(cid)))

    def get_device_id(self) -> str:
        v = self.get_meta("device_id")
        if v:
            return v
        import secrets
        v = secrets.token_hex(16)
        self.set_meta("device_id", v)
        return v

    def upsert_file(self, rel_path: str, size: int, mtime: int, crc32: int, server_rev: int) -> None:
        con = self.connect()
        try:
            con.execute(
                "INSERT INTO files(rel_path,size,mtime,crc32,server_rev) VALUES(?,?,?,?,?) "
                "ON CONFLICT(rel_path) DO UPDATE SET "
                "size=excluded.size, mtime=excluded.mtime, crc32=excluded.crc32, server_rev=excluded.server_rev",
                (rel_path, int(size), int(mtime), int(crc32), int(server_rev)),
            )
            con.commit()
        finally:
            con.close()

    def delete_file(self, rel_path: str) -> None:
        con = self.connect()
        try:
            con.execute("DELETE FROM files WHERE rel_path=?", (rel_path,))
            con.commit()
        finally:
            con.close()

    def get_file(self, rel_path: str) -> Optional[Tuple[int, int, int, int]]:
        con = self.connect()
        try:
            cur = con.execute("SELECT size,mtime,crc32,server_rev FROM files WHERE rel_path=?", (rel_path,))
            row = cur.fetchone()
            return (int(row[0]), int(row[1]), int(row[2]), int(row[3])) if row else None
        finally:
            con.close()

    def iter_files(self) -> Iterator[Tuple[str, int, int, int, int]]:
        con = self.connect()
        try:
            cur = con.execute("SELECT rel_path,size,mtime,crc32,server_rev FROM files")
            for row in cur:
                yield (row[0], int(row[1]), int(row[2]), int(row[3]), int(row[4]))
        finally:
            con.close()
