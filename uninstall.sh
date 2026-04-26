#!/usr/bin/env bash
set -euo pipefail

SKILL_LINK="${HOME}/.claude/skills/codelod"

echo "removing claude skill..."
rm -f "${SKILL_LINK}"

echo "uninstalling codelod python package..."
pip uninstall codelod -y --quiet 2>/dev/null || true

echo "done."
