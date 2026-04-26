#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${HOME}/.claude/skills"
SKILL_LINK="${SKILLS_DIR}/codelod"

echo "installing codelod python package..."
pip install -e "${REPO}" --quiet

echo "installing claude skill..."
mkdir -p "${SKILLS_DIR}"
ln -sf "${REPO}" "${SKILL_LINK}"

echo ""
echo "done."
echo "  cli:   codelod <repo-path>"
echo "  bench: codelod-benchmark <repo-path>"
echo "  skill: ${SKILL_LINK}"
