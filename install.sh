#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${HOME}/.claude/skills"
SKILL_LINK="${SKILLS_DIR}/codelod"

echo "installing claude skill..."
mkdir -p "${SKILLS_DIR}"
ln -sf "${REPO}" "${SKILL_LINK}"

echo ""
echo "done."
echo "  skill: ${SKILL_LINK}"
echo "  usage: python3 ${SKILL_LINK}/scripts/build_context.py <repo-path>"
