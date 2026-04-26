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

## Workflow

1. Verify the repo has a working Python environment before running the generator.

Suggested checks:

```bash
python3 --version
python3 -c "import sys; print(sys.executable)"
```

If `python3` is unavailable or broken, do not assume the skill can build `.context/` artifacts. Either use an existing `.context/` directory if it is present and trustworthy, or fix/select the correct Python environment first.

2. Generate or refresh the context layers from the repo root only after the environment check passes:

```bash
python3 scripts/build_context.py
```

3. Start at `.context/L0.md` to identify the relevant area of the repo.
4. Read `.context/L1.md` only for the directories or files that look relevant.
5. Open the matching `.context/L2/[filename].json` files to inspect signatures, classes, functions, and docstrings.
6. Read full source files only after `L0-L2` narrow the scope enough that implementation detail is necessary.

## Operating Rules

- Default to the lowest detail level that can still move the task forward with quality.
- Do not jump straight to full files for broad questions, repo exploration, or initial triage.
- Treat `L3` as the final escalation step, not the starting point.
- If the context artifacts look stale after a code change, regenerate them before continuing.
- Before regenerating, confirm that `python3` resolves to a usable interpreter for the current repo.
- When a task is limited to 2-3 files, keep the rest of the repo at `L0-L2`.
- Prefer the `extractor` and `attempts` fields in `L2` to understand whether a file was analyzed by a strong parser, a fallback backend, or summary-only mode.

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
