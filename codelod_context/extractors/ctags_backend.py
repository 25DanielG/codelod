"""universal ctags extractor — repo-wide fallback when native backends miss a language."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from codelod_context.models import Symbol

class UniversalCtagsIndex:
    """lazy repo-wide tag index. built once on first access, reused after."""

    def __init__(self, root: Path, files: list[Path]) -> None:
        self.root = root
        self.files = files
        self._loaded = False
        self._available = False
        self._detail = ""
        self._symbols_by_path: dict[str, list[Symbol]] = {}

    @property
    def available(self) -> bool:
        """true when universal ctags binary found and ran successfully."""

        self._ensure_loaded()
        return self._available

    @property
    def detail(self) -> str:
        """backend status string — used in extractor attempt logs."""

        self._ensure_loaded()
        return self._detail

    def symbols_for(self, relative_path: Path) -> list[Symbol]:
        """return symbols for repo-relative path. empty list if none found."""

        self._ensure_loaded()
        return list(self._symbols_by_path.get(relative_path.as_posix(), []))

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True

        binary = shutil.which("ctags")
        if not binary:
            self._detail = "ctags not installed"
            return

        version_result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            cwd=self.root,
            check=False,
        )
        version_text = (version_result.stdout or version_result.stderr or "").strip()
        if version_result.returncode != 0 or "Universal Ctags" not in version_text:
            # exuberant ctags or something else — json output not supported
            self._detail = "universal ctags unavailable"
            return

        # feed file list via stdin to avoid arg length limits on big repos
        file_list = "\n".join(path.as_posix() for path in self.files) + "\n"
        command = [binary, "--output-format=json", "--fields=+ne", "-L", "-"]
        result = subprocess.run(
            command,
            input=file_list,
            capture_output=True,
            text=True,
            cwd=self.root,
            check=False,
        )
        if result.returncode != 0:
            self._detail = (result.stderr or "ctags failed").strip()
            return

        symbols_by_path: dict[str, list[Symbol]] = {}
        for line in result.stdout.splitlines():
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("_type") != "tag":
                continue
            path = record.get("path")
            if not isinstance(path, str):
                continue
            symbol = _symbol_from_tag(record)
            if symbol is None:
                continue
            symbols_by_path.setdefault(path, []).append(symbol)

        self._symbols_by_path = symbols_by_path
        self._available = True
        self._detail = "universal ctags"

def _symbol_from_tag(record: dict[str, object]) -> Symbol | None:
    """convert ctags json record to symbol. return none if record malformed."""

    name = record.get("name")
    kind = record.get("kind")
    if not isinstance(name, str) or not isinstance(kind, str):
        return None

    scope = record.get("scope")
    scope_name = scope if isinstance(scope, str) else ""
    line_start = int(record.get("line", 0) or 0)
    line_end = int(record.get("end", line_start) or line_start)
    signature = name
    if scope_name:
        signature = f"{scope_name}.{name}"

    return Symbol(
        kind=kind,
        name=name if not scope_name else f"{scope_name}.{name}",
        signature=signature,
        docstring="",
        line_start=line_start,
        line_end=line_end,
        container=scope_name,
        source="ctags",
    )
