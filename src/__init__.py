"""
AKOÚŌ Hermes Plugin — Entry Point

Registers 18 slash commands and 4 tools for epistemically-disciplined
sonic analysis via the AKOÚŌ v0.9 listening framework.

Install: pip install -e ~/Development/hermes-akouo-plugin
         hermes plugins reload
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PLUGIN_NAME = "akouo"
PLUGIN_VERSION = "0.9.1"
PLUGIN_DESCRIPTION = "AKOÚŌ — 17 epistemically-disciplined listening modes"

# Paths
_PLUGIN_DIR = Path(__file__).resolve().parent.parent
_AKOUO_DIR = _PLUGIN_DIR / "akouo"
_SKILLS_DIR = _AKOUO_DIR / "skills"
_SCHEMAS_DIR = _AKOUO_DIR / "schemas"
_COMMANDS_DIR = _AKOUO_DIR / "commands"
_MANIFEST_PATH = _AKOUO_DIR / "akouo.manifest.json"


def _load_manifest() -> dict:
    """Load the AKOÚŌ manifest."""
    with open(_MANIFEST_PATH) as f:
        return json.load(f)


def _load_command(name: str) -> str:
    """Load a command definition markdown file."""
    path = _COMMANDS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text()
    return f"# /{name}\n\nCommand definition not found."


def _load_schema(name: str) -> dict:
    """Load a JSON schema by name."""
    path = _SCHEMAS_DIR / f"{name}.schema.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def register(hermes):
    """Register the AKOÚŌ plugin with Hermes Agent."""

    manifest = _load_manifest()

    # ── Tools ──────────────────────────────────────────────────────────

    @hermes.tool(
        name="akouo_route",
        description="Analyse a listening situation and return a routing plan (mode chain, confidence, risks)."
    )
    async def akouo_route(ctx, input_type: str = "", intent: str = "",
                          keywords: str = "", evidence: str = "") -> str:
        """Route a listening situation to the appropriate mode chain."""
        from .routing import route_listening_situation
        plan = route_listening_situation(
            input_type=input_type,
            intent=intent,
            keywords=keywords.split(",") if keywords else [],
            evidence=evidence,
            manifest=manifest,
        )
        return json.dumps(plan, indent=2)

    @hermes.tool(
        name="akouo_manifest",
        description="Return the full AKOÚŌ manifest JSON."
    )
    async def akouo_manifest(ctx) -> str:
        """Return the full AKOÚŌ manifest."""
        return json.dumps(manifest, indent=2)

    @hermes.tool(
        name="akouo_covenant",
        description="Parse a listening covenant text and return structured rules and commitments."
    )
    async def akouo_covenant(ctx, covenant_text: str = "") -> str:
        """Parse a listening covenant."""
        from .covenant import parse_covenant
        result = parse_covenant(covenant_text)
        return json.dumps(result, indent=2)

    @hermes.tool(
        name="akouo_validate",
        description="Validate a listening output JSON against a named schema."
    )
    async def akouo_validate(ctx, output_json: str = "", schema_name: str = "") -> str:
        """Validate output against a schema."""
        from .schemas import validate_output
        try:
            output = json.loads(output_json)
        except json.JSONDecodeError as e:
            return json.dumps({"valid": False, "error": f"Invalid JSON: {e}"})
        schema = _load_schema(schema_name)
        if not schema:
            return json.dumps({"valid": False, "error": f"Schema '{schema_name}' not found"})
        result = validate_output(output, schema)
        return json.dumps(result, indent=2)

    # ── Slash Commands ─────────────────────────────────────────────────

    COMMAND_SKILL_MAP = {
        "listen":        {"skills": ["akouo-router"], "purpose": "Default routed pass"},
        "full-ear":      {"skills": ["akouo-router"], "purpose": "Broad multimodal scan"},
        "forensic":      {"skills": ["akouo-router"], "purpose": "Strict evidentiary listening"},
        "tech":          {"skills": ["akouo-router"], "purpose": "Technical inspection"},
        "fiction":       {"skills": ["akouo-router"], "purpose": "Speculative worldbuilding"},
        "covenant":      {"skills": ["akouo-router"], "purpose": "Covenant-bound listening"},
        "remember":      {"skills": ["akouo-router"], "purpose": "Memory/lineage listening"},
        "one-sound-many-ears": {"skills": ["akouo-router"], "purpose": "Comparative flagship"},
        "route":         {"skills": ["akouo-router"], "purpose": "Handoff plan only"},
        "study":         {"skills": ["akouo-router"], "purpose": "Research-oriented listening"},
        "reference":     {"skills": ["reference-layer"], "purpose": "Conceptual mapping"},
        "litany":        {"skills": ["akouo-router"], "purpose": "Audits sound-vs-vision"},
        "transduce":     {"skills": ["akouo-router"], "purpose": "Mediation-chain analysis"},
        "voice":         {"skills": ["akouo-router"], "purpose": "Voice/speech analysis"},
        "audiovision":   {"skills": ["akouo-router"], "purpose": "Sound-image-scene analysis"},
        "access":        {"skills": ["akouo-router"], "purpose": "Accessibility audit"},
        "field":         {"skills": ["akouo-router"], "purpose": "Field recording analysis"},
        "method":        {"skills": ["akouo-router"], "purpose": "Methodology exploration"},
    }

    for cmd_name, cmd_info in COMMAND_SKILL_MAP.items():

        @hermes.command(
            name=cmd_name,
            description=f"AKOÚŌ /{cmd_name} — {cmd_info['purpose']}",
            usage=f"/{cmd_name} [description of sound or listening situation]"
        )
        async def cmd_handler(ctx, args: str = "", _name=cmd_name, _info=cmd_info):
            """Handle an AKOÚŌ command."""
            from .commands import handle_command
            return await handle_command(ctx, _name, args, _info, _AKOUO_DIR)

    # ── Lifecycle hooks ───────────────────────────────────────────────

    @hermes.on("session_start")
    async def on_session_start(ctx):
        """Ensure AKOÚŌ skills are symlinked on session start."""
        _ensure_skill_symlinks()

    @hermes.on("plugin_load")
    async def on_plugin_load(ctx):
        """Verify AKOÚŌ submodule is present on plugin load."""
        if not _AKOUO_DIR.exists():
            ctx.logger.warning(
                "AKOÚŌ submodule not found at %s. Run: git submodule update --init",
                _AKOUO_DIR
            )
        else:
            ctx.logger.info("AKOÚŌ v%s loaded (%d skills)",
                          manifest.get("akouo_version", "?"),
                          len(manifest.get("skills", [])))


def _ensure_skill_symlinks():
    """Ensure AKOÚŌ skills are symlinked into ~/.hermes/skills/."""
    import shutil

    hermes_skills = Path.home() / ".hermes" / "skills"
    hermes_skills.mkdir(parents=True, exist_ok=True)

    if not _SKILLS_DIR.exists():
        return

    for skill_dir in _SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        target = hermes_skills / skill_dir.name
        if target.exists() and not target.is_symlink():
            # Existing directory — skip (user may have local modifications)
            continue
        if target.is_symlink() and target.resolve() == skill_dir.resolve():
            # Already pointing to the right place
            continue
        if target.is_symlink():
            target.unlink()
        # Create symlink
        try:
            target.symlink_to(skill_dir, target_is_directory=True)
        except FileExistsError:
            pass
