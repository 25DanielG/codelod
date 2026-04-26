"""disk cache for file analysis — keyed by path + content digest."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from codelod_context import __version__

@dataclass
class AnalysisCache:
    """analysis cache. skips re-extracting unchanged files."""

    path: Path
    data: dict[str, object] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "AnalysisCache":
        """load from disk. wipe and reset on version mismatch or corrupt json."""

        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                raw = {}
        else:
            raw = {}

        if raw.get("version") != __version__:
            # version bump — old cache useless, start fresh
            raw = {"version": __version__, "files": {}}

        if "files" not in raw or not isinstance(raw["files"], dict):
            raw["files"] = {}

        return cls(path=path, data=raw)

    def get(self, relative_path: str, digest: str) -> dict[str, object] | None:
        """return cached record if digest matches. none if stale or missing."""

        files = self.data.setdefault("files", {})
        record = files.get(relative_path)
        if not isinstance(record, dict):
            return None
        if record.get("digest") != digest:
            return None
        return record

    def set(self, relative_path: str, digest: str, payload: dict[str, object]) -> None:
        """write record into cache. overwrites existing entry for same path."""

        files = self.data.setdefault("files", {})
        files[relative_path] = {"digest": digest, "payload": payload}

    def save(self) -> None:
        """flush cache to disk."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2) + "\n", encoding="utf-8")
