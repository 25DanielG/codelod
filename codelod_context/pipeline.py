"""main analysis pipeline — coordinates extractors, cache, and artifact writing."""

from __future__ import annotations

import json
from pathlib import Path

from codelod_context.cache import AnalysisCache
from codelod_context.config import infer_language
from codelod_context.fs import iter_source_files, safe_read_text, sha256_text, write_text
from codelod_context.models import ExtractorAttempt, FileContext, Symbol
from codelod_context.render import render_tree
from codelod_context.summarize import summarize_file
from codelod_context.extractors.base import Extractor
from codelod_context.extractors.ctags_backend import UniversalCtagsIndex
from codelod_context.extractors.heuristics import HeuristicExtractor
from codelod_context.extractors.native import JavaScriptRegexExtractor, PythonAstExtractor
from codelod_context.extractors.tree_sitter_backend import TreeSitterExtractor

class RepositoryContextBuilder:
    """build .context/ artifacts for repo. l0 tree, l1 summaries, l2 symbol json."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.context_dir = root / ".context"
        self.l2_dir = self.context_dir / "L2"
        self.cache = AnalysisCache.load(self.context_dir / ".cache" / "analysis.json")
        self.files = list(iter_source_files(root))
        self.ctags_index = UniversalCtagsIndex(root, self.files)
        # ordered by priority — first extractor that returns symbols wins
        self.extractors: list[Extractor] = [
            PythonAstExtractor(),
            TreeSitterExtractor(),
            JavaScriptRegexExtractor(),
        ]
        self.heuristic_extractor = HeuristicExtractor()

    def build(self) -> None:
        """write l0, l1, l2 artifacts. uses cache to skip unchanged files."""

        self.context_dir.mkdir(exist_ok=True)
        self.l2_dir.mkdir(parents=True, exist_ok=True)
        write_text(self.context_dir / "L0.md", render_tree(self.files))

        summaries: list[str] = []
        for relative_path in self.files:
            file_context = self.analyze_file(relative_path)
            summaries.append(f"- `{relative_path.as_posix()}`: {file_context.summary}")
            self.write_l2_file(relative_path, file_context)

        write_text(self.context_dir / "L1.md", "# L1 File Summaries\n\n" + "\n".join(summaries) + "\n")
        self.cache.save()

    def analyze_file(self, relative_path: Path) -> FileContext:
        """analyze single file. return cached result if content unchanged."""

        full_path = self.root / relative_path
        content = safe_read_text(full_path)
        digest = sha256_text(content)
        cached = self.cache.get(relative_path.as_posix(), digest)
        if cached:
            payload = cached.get("payload")
            if isinstance(payload, dict):
                return self._file_context_from_cache(payload, cache_hit=True)

        language = infer_language(relative_path)
        attempts: list[ExtractorAttempt] = []
        symbols: list[Symbol] = []
        extractor_name = "summary-only"

        for extractor in self.extractors:
            if not extractor.supports(language, relative_path):
                attempts.append(ExtractorAttempt(extractor.name, "skipped", "unsupported language"))
                continue
            result = extractor.extract(full_path, language, content)
            if result is None:
                attempts.append(ExtractorAttempt(extractor.name, "empty", "no symbols"))
                continue
            if result.symbols:
                symbols = result.symbols
                extractor_name = result.backend
                attempts.append(ExtractorAttempt(extractor.name, "selected", result.detail))
                break
            attempts.append(ExtractorAttempt(extractor.name, "empty", result.detail))

        if not symbols and self.ctags_index.available:
            ctags_symbols = self.ctags_index.symbols_for(relative_path)
            if ctags_symbols:
                symbols = ctags_symbols
                extractor_name = "universal-ctags"
                attempts.append(ExtractorAttempt("universal-ctags", "selected", self.ctags_index.detail))
            else:
                attempts.append(ExtractorAttempt("universal-ctags", "empty", self.ctags_index.detail))
        elif symbols:
            attempts.append(ExtractorAttempt("universal-ctags", "skipped", "higher-priority extractor selected"))
        elif not self.ctags_index.available:
            attempts.append(ExtractorAttempt("universal-ctags", "skipped", self.ctags_index.detail))

        if not symbols:
            if self.heuristic_extractor.supports(language, relative_path):
                result = self.heuristic_extractor.extract(full_path, language, content)
                if result is not None and result.symbols:
                    symbols = result.symbols
                    extractor_name = result.backend
                    attempts.append(ExtractorAttempt(result.backend, "selected", result.detail))
                else:
                    attempts.append(ExtractorAttempt(self.heuristic_extractor.name, "empty", "no symbols"))
            else:
                attempts.append(ExtractorAttempt(self.heuristic_extractor.name, "skipped", "unsupported language"))

        summary = summarize_file(relative_path, language, symbols)
        file_context = FileContext(
            path=relative_path.as_posix(),
            language=language,
            summary=summary,
            symbols=symbols,
            extractor=extractor_name,
            attempts=attempts,
            cache_hit=False,
        )
        self.cache.set(relative_path.as_posix(), digest, file_context.to_dict())
        return file_context

    def write_l2_file(self, relative_path: Path, file_context: FileContext) -> None:
        """write per-file symbol json under .context/l2/."""

        target = self.l2_dir / Path(str(relative_path) + ".json")
        write_text(target, json.dumps(file_context.to_dict(), indent=2) + "\n")

    def _file_context_from_cache(self, payload: dict[str, object], cache_hit: bool) -> FileContext:
        """reconstruct filecontext from cached dict. coerce types defensively."""

        symbols = [
            Symbol(
                kind=str(item.get("kind", "")),
                name=str(item.get("name", "")),
                signature=str(item.get("signature", "")),
                docstring=str(item.get("docstring", "")),
                line_start=int(item.get("line_start", 0)),
                line_end=int(item.get("line_end", 0)),
                container=str(item.get("container", "")),
                source=str(item.get("source", "")),
            )
            for item in payload.get("symbols", [])
            if isinstance(item, dict)
        ]
        attempts = [
            ExtractorAttempt(
                backend=str(item.get("backend", "")),
                status=str(item.get("status", "")),
                detail=str(item.get("detail", "")),
            )
            for item in payload.get("attempts", [])
            if isinstance(item, dict)
        ]
        return FileContext(
            path=str(payload.get("path", "")),
            language=str(payload.get("language", "")),
            summary=str(payload.get("summary", "")),
            symbols=symbols,
            extractor=str(payload.get("extractor", "summary-only")),
            attempts=attempts,
            cache_hit=cache_hit,
        )
