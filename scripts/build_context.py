"""entrypoint. parse args, walk repo, write .context/ artifacts."""

import sys
from pathlib import Path

# add repo root to path so codelod_context is importable without pip install
sys.path.insert(0, str(Path(__file__).parent.parent))

from codelod_context.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
