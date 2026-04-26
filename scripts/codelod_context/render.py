"""ascii tree renderer for l0 artifact."""

from __future__ import annotations

from pathlib import Path

def render_tree(files: list[Path]) -> str:
    """build ascii tree from file list. dirs before files, entries sorted."""

    lines = ["# L0 Repository Tree", ""]
    tree: dict[str, dict] = {}
    for path in files:
        cursor = tree
        for part in path.parts:
            cursor = cursor.setdefault(part, {})

    def walk(node: dict[str, dict], prefix: str = "") -> None:
        # empty dict = leaf file, non-empty = dir — sort dirs first
        entries = sorted(node.items(), key=lambda item: (item[1] == {}, item[0]))
        for index, (name, child) in enumerate(entries):
            connector = "└── " if index == len(entries) - 1 else "├── "
            lines.append(prefix + connector + name)
            extension = "    " if index == len(entries) - 1 else "│   "
            if child:
                walk(child, prefix + extension)

    walk(tree)
    lines.append("")
    return "\n".join(lines)
