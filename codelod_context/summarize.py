"""one-line file summaries for l1 artifact."""

from __future__ import annotations

from pathlib import Path

from codelod_context.models import Symbol

def summarize_file(path: Path, language: str, symbols: list[Symbol]) -> str:
    """produce one-line summary. use symbols if extracted, fall back to filename heuristic."""

    stem = path.stem.replace("_", " ").replace("-", " ").strip() or path.name

    # hard-coded well-known files — summaries won't improve from symbol extraction
    if path.name == "SKILL.md":
        return "Skill definition and operating instructions for CodeLOD."
    if path.name == "FORMAT.md":
        return "Reference document describing the L0-L2 artifact contract and escalation rules."
    if path.name == "__init__.py":
        return "Python package initialization and exported package surface."

    if language == "markdown":
        return f"Documentation about {stem}."
    if language in {"json", "yaml", "toml"}:
        return f"Configuration or structured data for {stem}."
    if path.name == "Dockerfile":
        return "Container build instructions for the repository."

    if symbols:
        lead = ", ".join(symbol.name for symbol in symbols[:3])
        noun = "module" if language == "python" else "source file"
        if len(symbols) > 3:
            lead += ", and more"
        return f"{language.capitalize()} {noun} defining {lead}."

    if path.parent.name == "scripts":
        return f"Utility script related to {stem}."
    return f"{language.capitalize()} file for {stem}."
