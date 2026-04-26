# Artifact Contract

`CodeLOD` writes its output to `.context/`.

## Levels

### `L0`

File: `.context/L0.md`

Purpose: cheap structural scan.

Content:
- repo-relative ASCII tree
- source-like files only
- excludes generated, dependency, VCS, and cache directories

### `L1`

File: `.context/L1.md`

Purpose: cheap semantic scan.

Content:
- one line per file
- repo-relative path
- one-sentence summary inferred from file type and top-level symbols

### `L2`

Directory: `.context/L2/`

Purpose: symbol-level inspection without full implementations.

One JSON file is generated per source file. The mirrored path is preserved under `L2` and the file name ends with `.json`.

Example:
- source: `src/api/routes.py`
- metadata: `.context/L2/src/api/routes.py.json`

Schema:

```json
{
  "path": "src/api/routes.py",
  "language": "python",
  "summary": "Python module containing router setup and request handlers.",
  "extractor": "python-ast",
  "cache_hit": false,
  "attempts": [
    {
      "backend": "python-ast",
      "status": "selected",
      "detail": "python ast"
    }
  ],
  "symbols": [
    {
      "kind": "function",
      "name": "list_users",
      "signature": "def list_users(limit: int = 50) -> list[User]",
      "docstring": "Return paginated users.",
      "line_start": 12,
      "line_end": 18,
      "container": "UserRoutes",
      "source": "native"
    }
  ]
}
```

Additional L2 fields:
- `extractor`: the backend that produced the winning symbol set
- `cache_hit`: whether this file analysis came from the incremental cache
- `attempts`: ordered backend attempts with `selected`, `empty`, or `skipped` status
- `container`: optional parent type or scope
- `source`: symbol origin such as `native`, `tree-sitter`, `ctags`, or `heuristic`

Backend order:
1. language-native extractors
2. Tree-sitter when available
3. Universal Ctags fallback
4. heuristic extractors for common languages
5. summary-only mode

## Escalation Policy

Use this sequence unless the task is already precisely scoped to known files:

1. `L0` to choose directories
2. `L1` to choose files
3. `L2` to choose symbols
4. `L3` to inspect implementation details

Escalate to `L3` only when you need:
- control flow
- exact data transformations
- bug root cause inside a function or method body
- concrete edits

Stay at `L1-L2` when the task is:
- architectural orientation
- ownership discovery
- entrypoint discovery
- identifying candidate files for a change