"""language config — excluded dirs, file extensions, comment prefixes, tree-sitter queries."""

from __future__ import annotations

from pathlib import Path

EXCLUDED_DIRS = {
    ".context",
    ".git",
    ".hg",
    ".idea",
    ".svn",
    ".next",
    ".nuxt",
    ".parcel-cache",
    ".pytest_cache",
    ".ruff_cache",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "tmp",
    "vendor",
    "venv",
}

TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".graphql",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".lua",
    ".m",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".scss",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}

LANGUAGE_BY_EXTENSION = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".graphql": "graphql",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "javascript",
    ".kt": "kotlin",
    ".lua": "lua",
    ".md": "markdown",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".scala": "scala",
    ".scss": "scss",
    ".sh": "shell",
    ".sql": "sql",
    ".swift": "swift",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".vue": "vue",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}

COMMENT_PREFIXES = {
    "c": "//",
    "cpp": "//",
    "csharp": "//",
    "go": "//",
    "java": "//",
    "javascript": "//",
    "kotlin": "//",
    "lua": "--",
    "php": "//",
    "python": "#",
    "ruby": "#",
    "rust": "//",
    "scala": "//",
    "shell": "#",
    "swift": "//",
    "typescript": "//",
}

TREE_SITTER_QUERY_BY_LANGUAGE = {
    "go": """
      [
        (function_declaration name: (identifier) @name)
        (method_declaration name: (field_identifier) @name)
        (type_declaration (type_spec name: (type_identifier) @name))
      ] @symbol
    """,
    "javascript": """
      [
        (function_declaration name: (identifier) @name)
        (method_definition name: (property_identifier) @name)
        (class_declaration name: (identifier) @name)
        (lexical_declaration (variable_declarator name: (identifier) @name value: [(arrow_function) (function)]))
      ] @symbol
    """,
    "python": """
      [
        (function_definition name: (identifier) @name)
        (class_definition name: (identifier) @name)
      ] @symbol
    """,
    "ruby": """
      [
        (method name: (identifier) @name)
        (singleton_method name: (identifier) @name)
        (class name: (_) @name)
        (module name: (_) @name)
      ] @symbol
    """,
    "rust": """
      [
        (function_item name: (identifier) @name)
        (struct_item name: (type_identifier) @name)
        (enum_item name: (type_identifier) @name)
        (trait_item name: (type_identifier) @name)
        (impl_item type: (_) @name)
      ] @symbol
    """,
    "typescript": """
      [
        (function_declaration name: (identifier) @name)
        (method_definition name: (property_identifier) @name)
        (class_declaration name: (type_identifier) @name)
        (interface_declaration name: (type_identifier) @name)
        (lexical_declaration (variable_declarator name: (identifier) @name value: [(arrow_function) (function)]))
      ] @symbol
    """,
}

DOCKERFILE_NAMES = {"Dockerfile"}

def infer_language(relative_path: Path) -> str:
    """infer language from filename. dockerfile check first, then extension lookup."""

    if relative_path.name in DOCKERFILE_NAMES:
        return "docker"
    return LANGUAGE_BY_EXTENSION.get(relative_path.suffix.lower(), "text")
