from __future__ import annotations
import fnmatch
import os
from pathlib import Path
from typing import Dict, List

from .util import to_rel_posix

def _matches_any(path_posix: str, patterns: List[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(path_posix, pat):
            return True
    return False

def scan_files(root: Path, ignore: List[str]) -> Dict[str, Path]:
    files: Dict[str, Path] = {}
    root = root.resolve()

    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)

        # prune ignored directories
        pruned = []
        for d in list(dirnames):
            absd = dp / d
            rel = to_rel_posix(root, absd)
            if _matches_any(rel + "/", ignore) or _matches_any(rel, ignore):
                pruned.append(d)
        for d in pruned:
            dirnames.remove(d)

        for fn in filenames:
            absp = dp / fn
            rel = to_rel_posix(root, absp)
            if _matches_any(rel, ignore):
                continue
            files[rel] = absp

    return files
