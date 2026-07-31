#!/usr/bin/env bash
# AKOÚŌ Hermes Plugin — One-command setup
# Usage: bash scripts/install.sh

set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_SKILLS="${HOME}/.hermes/skills"
AKOUO_SKILLS="${PLUGIN_DIR}/akouo/skills"

echo "🔌 Installing AKOÚŌ Hermes Plugin..."

# 1. Ensure submodule is initialised
if [ ! -d "${AKOUO_SKILLS}" ]; then
    echo "📦 Initialising submodule..."
    git -C "${PLUGIN_DIR}" submodule update --init --recursive
fi

# 2. Symlink skills
echo "🔗 Symlinking skills..."
mkdir -p "${HERMES_SKILLS}"
for skill_dir in "${AKOUO_SKILLS}"/*/; do
    skill_name="$(basename "${skill_dir}")"
    target="${HERMES_SKILLS}/${skill_name}"
    if [ -L "${target}" ] && [ "$(readlink "${target}")" = "${skill_dir%/}" ]; then
        echo "   ✓ ${skill_name} (already linked)"
    elif [ -e "${target}" ]; then
        echo "   ⚠ ${skill_name} exists — skipping (remove manually if safe)"
    else
        ln -s "${skill_dir%/}" "${target}"
        echo "   ✓ ${skill_name} linked"
    fi
done

# 3. Install Python package
echo "🐍 Installing Python package..."
pip install -e "${PLUGIN_DIR}" 2>/dev/null || pip3 install -e "${PLUGIN_DIR}"

# 4. Register plugin with Hermes
echo "🔄 Reloading Hermes plugins..."
hermes plugins reload 2>/dev/null || echo "   ⚠ Run 'hermes plugins reload' manually"

echo ""
echo "✅ AKOÚŌ v$(git -C "${PLUGIN_DIR}/akouo" describe --tags 2>/dev/null || echo '?') installed"
echo "   Skills: $(ls "${AKOUO_SKILLS}" | wc -l | tr -d ' ') listening modes"
echo "   Commands: 18 slash commands (/listen, /forensic, /covenant, ...)"
echo "   Tools: akouo_route, akouo_manifest, akouo_covenant, akouo_validate"
