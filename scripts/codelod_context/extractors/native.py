"""native extractors — python ast and js/ts regex. highest fidelity, run first."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from codelod_context.models import Symbol

from .base import Extractor, ExtractorResult

PYTHON_SIGNATURE_TRIM = re.compile(r"\s+")
JS_DOC_LINE = re.compile(r"^\s*\*\s?")
JS_EXPORT_FUNCTION = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\((.*?)\)"
)
JS_EXPORT_CONST = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>"
)
JS_CLASS = re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)")

class PythonAstExtractor(Extractor):
    """python ast parser. extracts classes, functions, methods with real signatures."""

    name = "python-ast"

    def supports(self, language: str, path: Path) -> bool:
        return language == "python"

    def extract(self, path: Path, language: str, content: str) -> ExtractorResult | None:
        try:
            module = ast.parse(content)
        except SyntaxError as exc:
            return ExtractorResult(symbols=[], backend=self.name, detail=f"syntax error: {exc.msg}")

        symbols: list[Symbol] = []
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(_symbol_from_python_node(node))
            elif isinstance(node, ast.ClassDef):
                symbols.append(_symbol_from_python_node(node))
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        symbols.append(_symbol_from_python_node(child, owner=node.name))
        if not symbols:
            return None
        return ExtractorResult(symbols=symbols, backend=self.name, detail="python ast")

def _symbol_from_python_node(node: ast.AST, owner: str | None = None) -> Symbol:
    kind = "class" if isinstance(node, ast.ClassDef) else "method" if owner else "function"
    name = f"{owner}.{node.name}" if owner else node.name
    signature = _build_python_signature(node, owner)
    docstring = ast.get_docstring(node) or ""
    line_end = getattr(node, "end_lineno", getattr(node, "lineno", 0))
    return Symbol(
        kind=kind,
        name=name,
        signature=signature,
        docstring=docstring,
        line_start=getattr(node, "lineno", 0),
        line_end=line_end,
        container=owner or "",
        source="native",
    )

def _build_python_signature(node: ast.AST, owner: str | None = None) -> str:
    if isinstance(node, ast.ClassDef):
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except Exception:
                continue
        suffix = f"({', '.join(bases)})" if bases else ""
        return f"class {node.name}{suffix}"

    try:
        source_lines = ast.unparse(node).splitlines()
    except Exception:
        return f"def {owner + '.' if owner else ''}{getattr(node, 'name', 'unknown')}"

    first_line = next(
        (
            line
            for line in source_lines
            if line.lstrip().startswith(("def ", "async def "))
        ),
        source_lines[0] if source_lines else f"def {getattr(node, 'name', 'unknown')}",
    ).rstrip(":")

    if owner:
        # check async first — avoid double-replacing if name appears in both forms
        if f"async def {node.name}" in first_line:
            first_line = first_line.replace(f"async def {node.name}", f"async def {owner}.{node.name}", 1)
        else:
            first_line = first_line.replace(f"def {node.name}", f"def {owner}.{node.name}", 1)

    return PYTHON_SIGNATURE_TRIM.sub(" ", first_line)

class JavaScriptRegexExtractor(Extractor):
    """js/ts regex extractor. handles exports, arrow functions, classes, jsdoc."""

    name = "javascript-regex"

    def supports(self, language: str, path: Path) -> bool:
        return language in {"javascript", "typescript"}

    def extract(self, path: Path, language: str, content: str) -> ExtractorResult | None:
        lines = content.splitlines()
        symbols: list[Symbol] = []
        for index, line in enumerate(lines):
            class_match = JS_CLASS.match(line)
            if class_match:
                symbols.append(
                    Symbol(
                        kind="class",
                        name=class_match.group(1),
                        signature=f"class {class_match.group(1)}",
                        docstring=_find_js_docstring(lines, index),
                        line_start=index + 1,
                        line_end=index + 1,
                        source="native",
                    )
                )
                continue

            function_match = JS_EXPORT_FUNCTION.match(line)
            if function_match:
                name, params = function_match.groups()
                async_prefix = "async " if "async" in line else ""
                symbols.append(
                    Symbol(
                        kind="function",
                        name=name,
                        signature=f"{async_prefix}function {name}({params})",
                        docstring=_find_js_docstring(lines, index),
                        line_start=index + 1,
                        line_end=index + 1,
                        source="native",
                    )
                )
                continue

            const_match = JS_EXPORT_CONST.match(line)
            if const_match:
                name, params = const_match.groups()
                async_prefix = "async " if "async" in line else ""
                symbols.append(
                    Symbol(
                        kind="function",
                        name=name,
                        signature=f"{async_prefix}{name} = ({params}) =>",
                        docstring=_find_js_docstring(lines, index),
                        line_start=index + 1,
                        line_end=index + 1,
                        source="native",
                    )
                )
        if not symbols:
            return None
        return ExtractorResult(symbols=symbols, backend=self.name, detail="regex extractor")

def _find_js_docstring(lines: list[str], index: int) -> str:
    """scan backward from definition. collect /** */ block or consecutive // lines."""

    doc_lines: list[str] = []
    cursor = index - 1
    in_block = False
    while cursor >= 0:
        stripped = lines[cursor].strip()
        if not stripped:
            cursor -= 1
            continue
        if stripped.endswith("*/"):
            in_block = True
            cleaned = stripped[:-2].strip()
            if cleaned:
                doc_lines.append(JS_DOC_LINE.sub("", cleaned))
            cursor -= 1
            continue
        if in_block:
            if stripped.startswith("/**") or stripped.startswith("/*"):
                cleaned = stripped.lstrip("/*").strip()
                if cleaned:
                    doc_lines.append(JS_DOC_LINE.sub("", cleaned))
                break
            doc_lines.append(JS_DOC_LINE.sub("", stripped))
            cursor -= 1
            continue
        if stripped.startswith("//"):
            doc_lines.append(stripped[2:].strip())
            cursor -= 1
            continue  # keep scanning — collect all consecutive // lines above
        break
    return " ".join(reversed([line for line in doc_lines if line])).strip()
