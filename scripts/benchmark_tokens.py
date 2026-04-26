"""token savings benchmark — compare reading all source vs codelod l0/l1/l2 layers."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# token counting

def _count_tokens_anthropic(text: str) -> int:
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.count_tokens(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": text}],
    )
    return response.input_tokens

def _count_tokens_heuristic(text: str) -> int:
    # rough approximation — good enough for relative comparison
    return max(1, len(text) // 4)

def _build_counter() -> tuple[callable, str]:
    """pick anthropic api if key present, else fall back to char/4 heuristic."""
    try:
        import anthropic
        import os
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not set")
        anthropic.Anthropic()
        return _count_tokens_anthropic, "Anthropic API"
    except (ImportError, ValueError):
        return _count_tokens_heuristic, "heuristic (chars/4)"

# content collection

def _collect_source(root: Path) -> str:
    """concat all tracked source files — baseline (l3) token cost."""
    sys.path.insert(0, str(Path(__file__).parent))
    from codelod_context.fs import iter_source_files, safe_read_text

    parts: list[str] = []
    for rel in iter_source_files(root):
        content = safe_read_text(root / rel)
        parts.append(f"# {rel.as_posix()}\n{content}")
    return "\n\n".join(parts)

def _collect_l0(ctx: Path) -> str:
    return (ctx / "L0.md").read_text(encoding="utf-8")

def _collect_l1(ctx: Path) -> str:
    return (ctx / "L0.md").read_text(encoding="utf-8") + "\n\n" + (ctx / "L1.md").read_text(encoding="utf-8")

def _collect_l2(ctx: Path) -> str:
    """l0 + l1 + all l2 symbol jsons — worst case, no source reads needed."""
    l2_dir = ctx / "L2"
    parts = [_collect_l1(ctx)]
    for json_file in sorted(l2_dir.rglob("*.json")):
        parts.append(json_file.read_text(encoding="utf-8"))
    return "\n\n".join(parts)

# main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark CodeLOD token savings.")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root (default: current directory).",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Regenerate .context/ before benchmarking.",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    ctx = root / ".context"

    build_script = Path(__file__).parent / "build_context.py"

    if args.rebuild or not ctx.exists():
        print("Building context artifacts...")
        result = subprocess.run(
            [sys.executable, str(build_script), str(root)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Build failed: {result.stderr.strip()}", file=sys.stderr)
            return 1
        print("Done.\n")

    count_tokens, method = _build_counter()
    print(f"Token counter : {method}")
    print(f"Repository    : {root}\n")

    levels = [
        ("Baseline (all source)", _collect_source(root)),
        ("L0 only  (file tree)", _collect_l0(ctx)),
        ("L0 + L1  (+ summaries)", _collect_l1(ctx)),
        ("L0 + L1 + L2  (+ symbols)", _collect_l2(ctx)),
    ]

    print("Counting tokens...\n")
    results: list[tuple[str, int]] = []
    for label, content in levels:
        n = count_tokens(content)
        results.append((label, n))
        print(f"  {label:<34}  {n:>8,} tokens")

    baseline = results[0][1]
    print()
    print(f"{'Level':<34}  {'Tokens':>8}  {'Saved':>7}  {'% saved':>8}")
    print("-" * 65)
    for label, n in results:
        saved = baseline - n
        pct = saved / baseline * 100 if baseline else 0
        bar = f"{'':>7}" if saved == 0 else f"{saved:>7,}"
        print(f"{label:<34}  {n:>8,}  {bar}  {pct:>7.1f}%")

    print()
    _, best_n = results[-1]
    print(
        f"Typical task uses L0+L1 to find files, then L2 for a few targets.\n"
        f"Worst case (all L2, no L3 reads): {baseline - best_n:,} tokens saved "
        f"({(baseline - best_n) / baseline * 100:.1f}% reduction)."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
