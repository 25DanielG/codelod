"""regex fallback extractors for 8 languages. fires when native ast and ctags both fail."""

from __future__ import annotations

import re
from pathlib import Path

from codelod_context.config import COMMENT_PREFIXES
from codelod_context.models import Symbol

from .base import Extractor, ExtractorResult

LANGUAGE_PATTERNS = {
    "csharp": [
        ("class", re.compile(r"^\s*(?:public|internal|private|protected|abstract|sealed|static|\s)+class\s+([A-Za-z_]\w*)")),
        ("interface", re.compile(r"^\s*(?:public|internal|private|protected|\s)+interface\s+([A-Za-z_]\w*)")),
        ("method", re.compile(r"^\s*(?:public|private|protected|internal|static|virtual|override|async|\s)+[\w<>\[\],?.]+\s+([A-Za-z_]\w*)\s*\((.*?)\)")),
    ],
    "go": [
        ("type", re.compile(r"^\s*type\s+([A-Za-z_]\w*)\s+(?:struct|interface|map|\[\])")),
        ("function", re.compile(r"^\s*func\s+([A-Za-z_]\w*)\s*\((.*?)\)")),
        ("method", re.compile(r"^\s*func\s*\((.*?)\)\s*([A-Za-z_]\w*)\s*\((.*?)\)")),
    ],
    "java": [
        ("class", re.compile(r"^\s*(?:public|private|protected|abstract|final|\s)+class\s+([A-Za-z_]\w*)")),
        ("interface", re.compile(r"^\s*(?:public|private|protected|abstract|\s)+interface\s+([A-Za-z_]\w*)")),
        ("method", re.compile(r"^\s*(?:public|private|protected|static|final|abstract|synchronized|\s)+[\w<>\[\], ?]+\s+([A-Za-z_]\w*)\s*\((.*?)\)")),
    ],
    "kotlin": [
        ("class", re.compile(r"^\s*(?:sealed\s+|data\s+|open\s+)?class\s+([A-Za-z_]\w*)")),
        ("interface", re.compile(r"^\s*interface\s+([A-Za-z_]\w*)")),
        ("function", re.compile(r"^\s*(?:suspend\s+)?fun\s+([A-Za-z_]\w*)\s*\((.*?)\)")),
    ],
    "php": [
        ("class", re.compile(r"^\s*(?:abstract\s+|final\s+)?class\s+([A-Za-z_]\w*)")),
        ("function", re.compile(r"^\s*function\s+([A-Za-z_]\w*)\s*\((.*?)\)")),
    ],
    "ruby": [
        ("class", re.compile(r"^\s*class\s+([A-Za-z_:]\w*)")),
        ("module", re.compile(r"^\s*module\s+([A-Za-z_:]\w*)")),
        ("method", re.compile(r"^\s*def\s+(?:self\.)?([A-Za-z_]\w*[!?=]?)")),
    ],
    "rust": [
        ("struct", re.compile(r"^\s*(?:pub\s+)?struct\s+([A-Za-z_]\w*)")),
        ("enum", re.compile(r"^\s*(?:pub\s+)?enum\s+([A-Za-z_]\w*)")),
        ("trait", re.compile(r"^\s*(?:pub\s+)?trait\s+([A-Za-z_]\w*)")),
        ("function", re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)\s*\((.*?)\)")),
    ],
    "swift": [
        ("class", re.compile(r"^\s*(?:public|private|internal|open|final|\s)+class\s+([A-Za-z_]\w*)")),
        ("struct", re.compile(r"^\s*(?:public|private|internal|\s)+struct\s+([A-Za-z_]\w*)")),
        ("protocol", re.compile(r"^\s*(?:public|private|internal|\s)+protocol\s+([A-Za-z_]\w*)")),
        ("function", re.compile(r"^\s*func\s+([A-Za-z_]\w*)\s*\((.*?)\)")),
    ],
}

class HeuristicExtractor(Extractor):
    """line-by-line regex matching. first pattern wins per line."""

    name = "heuristic"

    def supports(self, language: str, path: Path) -> bool:
        return language in LANGUAGE_PATTERNS

    def extract(self, path: Path, language: str, content: str) -> ExtractorResult | None:
        patterns = LANGUAGE_PATTERNS.get(language, [])
        if not patterns:
            return None

        lines = content.splitlines()
        symbols: list[Symbol] = []
        for index, line in enumerate(lines):
            for kind, pattern in patterns:
                match = pattern.match(line)
                if not match:
                    continue
                name = match.group(1) if match.groups() else line.strip()
                signature = line.strip().rstrip("{").rstrip()
                if not signature:
                    signature = f"{kind} {name}"
                symbols.append(
                    Symbol(
                        kind=kind,
                        name=name,
                        signature=signature,
                        docstring=_find_comment_block(lines, index, language),
                        line_start=index + 1,
                        line_end=index + 1,
                        source="heuristic",
                    )
                )
                break  # first matching pattern wins, skip rest for this line
        if not symbols:
            return None
        return ExtractorResult(symbols=symbols, backend=self.name, detail="language heuristics")

def _find_comment_block(lines: list[str], index: int, language: str) -> str:
    """scan backward from definition line, collect comment lines above it."""

    prefix = COMMENT_PREFIXES.get(language)
    if not prefix:
        return ""
    doc_lines: list[str] = []
    cursor = index - 1
    while cursor >= 0:
        stripped = lines[cursor].strip()
        if not stripped:
            cursor -= 1
            continue
        if stripped.startswith(prefix):
            doc_lines.append(stripped[len(prefix):].strip())
            cursor -= 1
            continue
        break
    return " ".join(reversed([line for line in doc_lines if line])).strip()
