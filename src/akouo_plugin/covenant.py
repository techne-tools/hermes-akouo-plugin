"""
AKOÚŌ Covenant — Parse listening covenant text.

A covenant is a small, human-written declaration of sonic sovereignty:
what this ear will not listen to, will release after hearing, will not
reveal, will not retain, will blur, or will refuse at certain hours,
and why.
"""

from __future__ import annotations

import re
from typing import Any


def parse_covenant(text: str) -> dict[str, Any]:
    """Parse a listening covenant from free-form text.

    Returns a structured dict with id, rules, and commitments.
    """
    lines = text.strip().split("\n")
    covenant: dict[str, Any] = {
        "id": _extract_id(text),
        "extends": _extend_lineage(text),
        "rules": [],
        "commitments": [],
        "raw": text,
    }

    # Known rule verbs
    rule_verbs = [
        "do_not_listen", "ignore", "do_not_reveal", "do_not_retain",
        "coarsen", "quiet_hours", "max_window", "require_consent",
    ]

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check for rule patterns
        for verb in rule_verbs:
            if verb in line.lower():
                rule = {"verb": verb, "description": line}
                # Extract value if present
                value_match = re.search(rf"{re.escape(verb)}[:\s]+(.+)", line, re.IGNORECASE)
                if value_match:
                    rule["value"] = value_match.group(1).strip()
                covenant["rules"].append(rule)
                break
        else:
            # Non-rule lines become commitments
            if not any(r["description"] == line for r in covenant["rules"]):
                covenant["commitments"].append(line)

    return covenant


def _extract_id(text: str) -> str:
    """Extract a covenant ID from the text."""
    match = re.search(r"(?:covenant|covenant_id|id)[:\s]+([\w-]+)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return "anonymous"


def _extend_lineage(text: str) -> list[str]:
    """Extract extends lineage from the text."""
    match = re.search(r"extends[:\s]+([\w\s,./-]+)", text, re.IGNORECASE)
    if match:
        return [e.strip() for e in match.group(1).split(",")]
    return []
