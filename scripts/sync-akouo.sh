#!/usr/bin/env bash
# Sync AKOÚŌ upstream — pull latest, update submodule, re-link skills
# Usage: bash scripts/sync-akouo.sh

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_SKILLS="${HOME}/.hermes/skills"
AKOUO_DIR="${PLUGIN_DIR}/akouo"

echo "🔄 Syncing AKOÚŌ upstream..."

# 1. Fetch upstream tags
echo "📡 Fetching upstream..."
git -C "${AKOUO_DIR}" fetch --tags origin

# 2. Check for new version
CURRENT_TAG="$(git -C "${AKOUO_DIR}" describe --tags 2>/dev/null || echo 'none')"
echo "   Current: ${CURRENT_TAG}"

# 3. Update submodule to latest tag
LATEST_TAG="$(git -C "${AKOUO_DIR}" tag -l 'v*' --sort=-v:refname | head -1)"
echo "   Latest:  ${LATEST_TAG}"

if [ "${CURRENT_TAG}" = "${LATEST_TAG}" ]; then
    echo "   ✓ Already at latest version"
else
    echo "   ⬆ Updating to ${LATEST_TAG}..."
    git -C "${AKOUO_DIR}" checkout "${LATEST_TAG}"
    git -C "${PLUGIN_DIR}" add akouo
    git -C "${PLUGIN_DIR}" commit -m "chore: update akouo submodule to ${LATEST_TAG}" || true
    echo "   ✓ Updated to ${LATEST_TAG}"
fi

# 4. Re-link skills (in case new skills were added)
echo "🔗 Re-linking skills..."
mkdir -p "${HERMES_SKILLS}"
for skill_dir in "${AKOUO_DIR}/skills"/*/; do
    skill_name="$(basename "${skill_dir}")"
    target="${HERMES_SKILLS}/${skill_name}"
    if [ -L "${target}" ] && [ "$(readlink "${target}")" = "${skill_dir%/}" ]; then
        :  # already correct
    elif [ -e "${target}" ]; then
        echo "   ⚠ ${skill_name} exists — skipping"
    else
        ln -s "${skill_dir%/}" "${target}"
        echo "   ✓ ${skill_name} linked"
    fi
done

# 5. Reload Hermes plugins
echo "🔄 Reloading Hermes plugins..."
hermes plugins reload 2>/dev/null || echo "   ⚠ Run 'hermes plugins reload' manually"

echo ""
echo "✅ Sync complete — AKOÚŌ ${LATEST_TAG}"
