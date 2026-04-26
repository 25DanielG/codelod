"""tree-sitter extractor — optional. needs tree_sitter + language pack installed."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

from codelod_context.config import TREE_SITTER_QUERY_BY_LANGUAGE
from codelod_context.models import Symbol

from .base import Extractor, ExtractorResult

class TreeSitterExtractor(Extractor):
    """tree-sitter backend. only active when bindings and grammars are installed."""

    name = "tree-sitter"

    def __init__(self) -> None:
        self._runtime = _load_runtime()

    def supports(self, language: str, path: Path) -> bool:
        return self._runtime is not None and language in TREE_SITTER_QUERY_BY_LANGUAGE

    def extract(self, path: Path, language: str, content: str) -> ExtractorResult | None:
        runtime = self._runtime
        if runtime is None:
            return None

        parser, language_object = runtime.parser_for(language)
        if parser is None or language_object is None:
            return None

        tree = parser.parse(content.encode("utf-8"))
        root = tree.root_node
        query_source = TREE_SITTER_QUERY_BY_LANGUAGE.get(language)
        if not query_source:
            return None

        try:
            query = language_object.query(query_source)
        except Exception:
            return None

        symbols: list[Symbol] = []
        raw_captures = query.captures(root)
        # tree-sitter <0.22 returns list[(Node, str)]; >=0.22 returns dict[str, list[Node]]
        if isinstance(raw_captures, dict):
            captures = [(node, name) for name, nodes in raw_captures.items() for node in nodes]
            captures.sort(key=lambda pair: pair[0].start_byte)
        else:
            captures = raw_captures

        current_name = ""
        current_node = None
        for node, capture_name in captures:
            if capture_name == "name":
                current_name = content[node.start_byte:node.end_byte].strip()
            elif capture_name == "symbol":
                current_node = node
                if not current_name:
                    continue
                signature = _line_at(content, node.start_point[0]).strip()
                symbols.append(
                    Symbol(
                        kind=_kind_from_node_type(node.type),
                        name=current_name,
                        signature=signature or current_name,
                        docstring="",
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        source="tree-sitter",
                    )
                )
                current_name = ""
                current_node = None

        if not symbols:
            return None
        return ExtractorResult(symbols=symbols, backend=self.name, detail="tree-sitter query")

def _kind_from_node_type(node_type: str) -> str:
    if "class" in node_type or "struct" in node_type:
        return "class"
    if "interface" in node_type or "trait" in node_type:
        return "interface"
    return "function"

def _line_at(content: str, zero_index: int) -> str:
    lines = content.splitlines()
    if 0 <= zero_index < len(lines):
        return lines[zero_index]
    return ""

class _TreeSitterRuntime:
    def __init__(self, tree_sitter_module: object, adapter: object) -> None:
        self.tree_sitter_module = tree_sitter_module
        self.adapter = adapter

    def parser_for(self, language: str) -> tuple[object | None, object | None]:
        try:
            parser = self.tree_sitter_module.Parser()
        except Exception:
            return None, None

        language_object = self.adapter.language_for(language)
        if language_object is None:
            return None, None

        try:
            parser.language = language_object
        except Exception:
            try:
                parser.set_language(language_object)  # older tree-sitter api
            except Exception:
                return None, None
        return parser, language_object

class _LanguagePackAdapter:
    def __init__(self, module: object, mode: str) -> None:
        self.module = module
        self.mode = mode

    def language_for(self, language: str) -> object | None:
        getter = getattr(self.module, "get_language", None)
        if getter is None:
            return None
        try:
            return getter(language)
        except Exception:
            return None

def _load_runtime() -> _TreeSitterRuntime | None:
    """try to find tree-sitter module + language pack. return none if missing."""

    tree_sitter_spec = importlib.util.find_spec("tree_sitter")
    if tree_sitter_spec is None:
        return None
    tree_sitter_module = importlib.import_module("tree_sitter")

    for module_name, mode in (
        ("tree_sitter_languages", "tree_sitter_languages"),
        ("tree_sitter_language_pack", "tree_sitter_language_pack"),
    ):
        if importlib.util.find_spec(module_name) is None:
            continue
        module = importlib.import_module(module_name)
        adapter = _LanguagePackAdapter(module, mode)
        return _TreeSitterRuntime(tree_sitter_module, adapter)
    return None
