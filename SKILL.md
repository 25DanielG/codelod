---
name: codelod
description: repository files -> context level layers (L0 tree, L1 summaries, L2 symbols, L3 source). creates a zoom-in workflow that saves tokens + JSON audit trail
disable-model-invocation: false
---

# CodeLOD

Use this skill when the user expresses concerns about token efficiency and the task touches an unfamiliar or any sizeable codebase.
The goal is to replace "open files until the answer appears" with progressive context resolution:

- `L0`: repo tree
- `L1`: one-sentence file summaries
- `L2`: per-file symbol/signature metadata with docstrings
- `L3`: full source code

## Installation

```bash
git clone https://github.com/25DanielG/codelod
cd codelod
bash install.sh
```

This installs the `codelod` CLI and symlinks the skill into `~/.claude/skills/codelod`.

To remove: `bash uninstall.sh`

## Workflow

1. Locate the skill directory:

```bash
CODELOD=~/.claude/skills/codelod
```

2. Generate or refresh context layers:

```bash
python3 $CODELOD/scripts/build_context.py <repo-path>
```

This works with any `python3` — no pip install or venv required. The script self-resolves `codelod_context` relative to its own location.

3. Start at `.context/L0.md` to identify the relevant area of the repo.
4. Read `.context/L1.md` only for the directories or files that look relevant.
5. Open the matching `.context/L2/[filename].json` files to inspect signatures, classes, functions, and docstrings.
6. Read full source files only after `L0-L2` narrow the scope enough that implementation detail is necessary.

## Operating Rules

- **Always read L0 first.** No exceptions. Even if the task seems narrow.
- **Always read L1 before opening any source file.** L1 costs ~200 tokens and prevents reading the wrong file.
- Only open L2 for files L1 identifies as relevant. Only open L3 (full source) for files L2 confirms need implementation detail.
- If `.context/` is missing or stale, regenerate before doing anything else.
- When a task touches ≤3 files and you already know exactly which ones, you may skip L0/L1 — but read L2 first.
- Never read a full source file speculatively. L2 signatures are enough to understand structure.
- Prefer `extractor` and `attempts` fields in L2 to judge parser confidence.

## Artifact Layout

- `.context/L0.md`: ASCII tree of tracked source-like files
- `.context/L1.md`: per-file natural-language summaries
- `.context/L2/`: per-file JSON metadata
- `.context/.cache/analysis.json`: incremental cache keyed by file digest
- `L3`: the real repo files

## L2 Backend Order

`CodeLOD` resolves L2 with a backend chain instead of a single parser:

1. language-native extractors when they are stronger than generic tools
2. Tree-sitter when Python bindings and grammars are installed
3. Universal Ctags as the broad structured fallback
4. heuristic regex extractors for common non-Python languages
5. summary-only mode when no symbol extractor can provide useful output

Read [references/FORMAT.md](references/FORMAT.md) for the artifact contract and the escalation policy.
Read [examples/escalation-example.md](examples/escalation-example.md) for a minimal traversal example.
