"""fs helpers — walk repo, read files, hash content, write artifacts."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable

from codelod_context.config import EXCLUDED_DIRS, TEXT_EXTENSIONS

def iter_source_files(root: Path) -> Iterable[Path]:
    """yield source files relative to root. skip noise dirs and binary files."""

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS and not d.startswith("."))
        current_path = Path(current_root)
        for filename in sorted(filenames):
            path = current_path / filename
            rel = path.relative_to(root)
            if should_skip_file(root, rel):
                continue
            yield rel

def should_skip_file(root: Path, relative_path: Path) -> bool:
    """true if file should be skipped — excluded dir, dotfile, bad extension, or binary."""

    if any(part in EXCLUDED_DIRS for part in relative_path.parts):
        return True
    if relative_path.name.startswith("."):
        return True
    if relative_path.suffix.lower() not in TEXT_EXTENSIONS and relative_path.name != "Dockerfile":
        return True
    try:
        chunk = (root / relative_path).read_bytes()[:1024]
    except OSError:
        return True
    return b"\0" in chunk  # null byte = binary

def safe_read_text(path: Path) -> str:
    """read utf-8. fall back to replace-on-error for malformed bytes."""

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")

def sha256_text(content: str) -> str:
    """sha256 of content string — used as cache key."""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def write_text(path: Path, content: str) -> None:
    """write utf-8 text. mkdir parents if missing."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
