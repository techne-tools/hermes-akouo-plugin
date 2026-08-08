"""
AKOÚŌ Hermes Plugin — Entry Point

Registers 18 slash commands and 4 tools for epistemically-disciplined
sonic analysis via the AKOÚŌ v0.9 listening framework.

Install: pip install -e ~/Development/hermes-akouo-plugin
         hermes plugins reload

API surface (verified against hermes-agent HEAD 3dc9ace02):
  - ctx.register_tool(name, toolset, schema, handler, is_async, description, emoji)
  - ctx.register_command(name, handler, description, args_hint)
  - ctx.register_hook(hook_name, callback)
Tool handlers receive (args: dict, **kwargs) and MUST return a JSON string.
Command handlers receive (raw_args: str) and return str | None.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("hermes_plugins.akouo")

PLUGIN_NAME = "akouo"
PLUGIN_VERSION = "0.9.1"
PLUGIN_DESCRIPTION = "AKOÚŌ — 17 epistemically-disciplined listening modes"

# Paths
_PLUGIN_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
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


# ---------------------------------------------------------------------------
# Tool handlers — signature (args: dict, **kwargs) -> JSON string
# ---------------------------------------------------------------------------

async def _handle_route(args: dict, **kwargs) -> str:
    """Route a listening situation to the appropriate mode chain."""
    from .routing import route_listening_situation

    manifest = _load_manifest()
    plan = route_listening_situation(
        input_type=args.get("input_type", ""),
        intent=args.get("intent", ""),
        keywords=args.get("keywords", "").split(",") if args.get("keywords") else [],
        evidence=args.get("evidence", ""),
        manifest=manifest,
    )
    return json.dumps(plan, indent=2)


async def _handle_manifest(args: dict, **kwargs) -> str:
    """Return the full AKOÚŌ manifest JSON."""
    return json.dumps(_load_manifest(), indent=2)


async def _handle_covenant(args: dict, **kwargs) -> str:
    """Parse a listening covenant text and return structured rules and commitments."""
    from .covenant import parse_covenant

    result = parse_covenant(args.get("covenant_text", ""))
    return json.dumps(result, indent=2)


async def _handle_validate(args: dict, **kwargs) -> str:
    """Validate a listening output JSON against a named schema."""
    from .schemas import validate_output

    output_json = args.get("output_json", "")
    schema_name = args.get("schema_name", "")
    try:
        output = json.loads(output_json)
    except json.JSONDecodeError as e:
        return json.dumps({"valid": False, "error": f"Invalid JSON: {e}"})
    schema = _load_schema(schema_name)
    if not schema:
        return json.dumps({"valid": False, "error": f"Schema '{schema_name}' not found"})
    result = validate_output(output, schema)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool schemas — arguments MUST live under `parameters` (registry.py:698)
# ---------------------------------------------------------------------------

def _tool_schemas() -> dict:
    """Return {tool_name: schema} for every AKOÚŌ tool."""
    return {
        "akouo_route": {
            "description": (
                "Analyse a listening situation and return a routing plan "
                "(mode chain, confidence, risks)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "input_type": {
                        "type": "string",
                        "description": "Type of input (e.g. field recording, live performance, file).",
                    },
                    "intent": {
                        "type": "string",
                        "description": "The listening intent or research question.",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "Comma-separated keywords describing the situation.",
                    },
                    "evidence": {
                        "type": "string",
                        "description": "Optional evidence or context for the routing decision.",
                    },
                },
            },
        },
        "akouo_manifest": {
            "description": "Return the full AKOÚŌ manifest JSON.",
            "parameters": {"type": "object", "properties": {}},
        },
        "akouo_covenant": {
            "description": (
                "Parse a listening covenant text and return structured rules and commitments."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "covenant_text": {
                        "type": "string",
                        "description": "The covenant text to parse.",
                    },
                },
            },
        },
        "akouo_validate": {
            "description": "Validate a listening output JSON against a named schema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "output_json": {
                        "type": "string",
                        "description": "The listening output JSON to validate.",
                    },
                    "schema_name": {
                        "type": "string",
                        "description": "Name of the schema (e.g. listening-output).",
                    },
                },
            },
        },
    }


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

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
    "speech":        {"skills": ["akouo-router"], "purpose": "Voice/speech analysis"},
    "audiovision":   {"skills": ["akouo-router"], "purpose": "Sound-image-scene analysis"},
    "access":        {"skills": ["akouo-router"], "purpose": "Accessibility audit"},
    "field":         {"skills": ["akouo-router"], "purpose": "Field recording analysis"},
    "method":        {"skills": ["akouo-router"], "purpose": "Methodology exploration"},
}


def _make_command_handler(cmd_name: str, cmd_info: dict):
    """Build an async command handler with signature (raw_args: str) -> str."""
    from .commands import handle_command

    async def cmd_handler(raw_args: str = "") -> str:
        return await handle_command(cmd_name, raw_args, cmd_info, _AKOUO_DIR)

    return cmd_handler


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def _ensure_skill_symlinks() -> None:
    """Ensure AKOÚŌ skills are symlinked into ~/.hermes/skills/.

    Deliberate exception to the register_skill() best practice: the 18
    listening modes are distributed as a git submodule and are meant to
    appear in the global <available_skills> index (the slash-command
    briefs reference them by bare name, e.g. ``akouo-router``).
    register_skill() would namespace them as ``akouo:<name>`` and hide
    them from the index — a regression for this workflow.
    """
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


def register(ctx) -> None:
    """Register the AKOÚŌ plugin with Hermes Agent.

    Called once by the plugin loader with a PluginContext. Uses the
    ctx.register_* API (NOT decorators — PluginContext has no
    tool/command/on attributes).
    """
    # Verify submodule presence at load time (replaces the old
    # invalid ``plugin_load`` hook — not in VALID_HOOKS).
    if not _AKOUO_DIR.exists():
        logger.warning(
            "AKOÚŌ submodule not found at %s. Run: git submodule update --init",
            _AKOUO_DIR,
        )
    else:
        try:
            manifest = _load_manifest()
            logger.info(
                "AKOÚŌ v%s loaded (%d skills)",
                manifest.get("akouo_version", "?"),
                len(manifest.get("skills", [])),
            )
        except Exception as exc:
            logger.warning("AKOÚŌ manifest load failed: %s", exc)

    # ── Tools ──────────────────────────────────────────────────────────
    handlers = {
        "akouo_route": _handle_route,
        "akouo_manifest": _handle_manifest,
        "akouo_covenant": _handle_covenant,
        "akouo_validate": _handle_validate,
    }
    for tool_name, schema in _tool_schemas().items():
        ctx.register_tool(
            name=tool_name,
            toolset="akouo",
            schema=schema,
            handler=handlers[tool_name],
            is_async=True,
            description=schema["description"],
            emoji="👂",
        )

    # ── Slash Commands ────────────────────────────────────────────────
    for cmd_name, cmd_info in COMMAND_SKILL_MAP.items():
        ctx.register_command(
            name=cmd_name,
            handler=_make_command_handler(cmd_name, cmd_info),
            description=f"AKOÚŌ /{cmd_name} — {cmd_info['purpose']}",
            args_hint="[description of sound or listening situation]",
        )

    # ── Lifecycle hooks ───────────────────────────────────────────────
    ctx.register_hook("on_session_start", _ensure_skill_symlinks)
