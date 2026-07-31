"""
AKOÚŌ Command Handlers — Handle slash command invocations.

Each command loads the relevant AKOÚŌ skills and produces a listening brief.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


async def handle_command(
    ctx,
    command_name: str,
    args: str,
    info: dict[str, Any],
    akouo_dir: Path,
) -> str:
    """Handle an AKOÚŌ slash command invocation.

    Args:
        ctx: Hermes command context
        command_name: The command name (e.g., "listen", "forensic")
        args: The user's argument string
        info: Command metadata (skills, purpose)
        akouo_dir: Path to the AKOÚŌ submodule

    Returns:
        A formatted listening brief or routing plan.
    """
    # Load the command definition
    commands_dir = akouo_dir / "commands"
    cmd_path = commands_dir / f"{command_name}.md"
    command_def = ""
    if cmd_path.exists():
        command_def = cmd_path.read_text()

    # Load the manifest
    manifest_path = akouo_dir / "akouo.manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    # Build the listening brief
    brief_parts = [
        f"## AKOÚŌ /{command_name}",
        f"**Purpose:** {info['purpose']}",
        f"**Skills:** {', '.join(info['skills'])}",
        "",
    ]

    if args:
        brief_parts.append(f"**Listening situation:** {args}")
        brief_parts.append("")

    if command_def:
        brief_parts.append("### Command Definition")
        brief_parts.append(command_def)
        brief_parts.append("")

    # Add manifest skills summary
    skills = manifest.get("skills", [])
    if skills:
        brief_parts.append("### Available Modes")
        for skill in skills:
            if skill.get("kind") == "mode":
                brief_parts.append(
                    f"- **{skill.get('label', skill['id'])}** — {skill.get('summary', '')}"
                )
        brief_parts.append("")

    # Add routing guidance
    brief_parts.append("### Routing Guidance")
    brief_parts.append(
        "Load the router skill first, then the primary mode, then secondary "
        "and corrective modes as needed. See the command definition above for "
        "the recommended mode chain."
    )

    return "\n".join(brief_parts)
