"""data models for l0-l2 artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

@dataclass
class Symbol:
    """one extracted symbol — function, class, method, etc."""

    kind: str
    name: str
    signature: str
    docstring: str
    line_start: int
    line_end: int
    container: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, object]:
        """dump to dict, drop empty fields."""

        payload = asdict(self)
        return {key: value for key, value in payload.items() if value not in {"", None}}

@dataclass
class ExtractorAttempt:
    """log of which extractor tried this file and what happened."""

    backend: str
    status: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        """dump to dict. include detail only if set."""

        payload = {"backend": self.backend, "status": self.status}
        if self.detail:
            payload["detail"] = self.detail
        return payload

@dataclass
class FileContext:
    """everything codelod knows about one file."""

    path: str
    language: str
    summary: str
    symbols: list[Symbol]
    extractor: str
    attempts: list[ExtractorAttempt] = field(default_factory=list)
    cache_hit: bool = False

    def to_dict(self) -> dict[str, object]:
        """dump to l2 contract shape."""

        return {
            "path": self.path,
            "language": self.language,
            "summary": self.summary,
            "extractor": self.extractor,
            "cache_hit": self.cache_hit,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "symbols": [symbol.to_dict() for symbol in self.symbols],
        }
