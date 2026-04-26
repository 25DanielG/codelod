"""extractor interface — all backends implement this."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codelod_context.models import Symbol

@dataclass
class ExtractorResult:
    """symbols + metadata returned by extractor backend."""

    symbols: list[Symbol]
    backend: str
    detail: str = ""

class Extractor:
    """base class. subclass and implement supports() + extract()."""

    name = "extractor"

    def supports(self, language: str, path: Path) -> bool:
        """return true if extractor can handle this language/path combo."""

        raise NotImplementedError

    def extract(self, path: Path, language: str, content: str) -> ExtractorResult | None:
        """extract symbols. return none if nothing usable found."""

        raise NotImplementedError
