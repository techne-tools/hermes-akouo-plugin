"""
AKOÚŌ Routing — Programmatic listening situation router.

Implements the scoring heuristic from akouo-router/SKILL.md to produce
a routing plan: primary mode, secondary mode, corrective mode, evidence
level, claim permissions, and risks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def route_listening_situation(
    input_type: str,
    intent: str,
    keywords: list[str],
    evidence: str,
    manifest: dict,
) -> dict[str, Any]:
    """Route a listening situation to the appropriate mode chain.

    Args:
        input_type: Type of input (e.g., "file", "live", "recording", "description")
        intent: What the user wants to do
        keywords: Comma-separated keywords describing the situation
        evidence: Available evidence description
        manifest: The AKOÚŌ manifest dict

    Returns:
        Routing plan dict with mode chain, confidence, risks, and claim permissions.
    """
    skills = manifest.get("skills", [])
    commands = manifest.get("commands", [])

    # Build mode index
    modes = {s["id"]: s for s in skills if s.get("kind") == "mode"}
    router = next((s for s in skills if s.get("kind") == "router"), None)

    # Keyword-to-mode mapping
    keyword_map = {
        "signal": "signal-inspection-listening",
        "waveform": "signal-inspection-listening",
        "spectrogram": "signal-inspection-listening",
        "technical": "signal-inspection-listening",
        "perceptual": "acoulogical-object-listening",
        "texture": "acoulogical-object-listening",
        "morphology": "acoulogical-object-listening",
        "body": "embodied-affective-listening",
        "affect": "embodied-affective-listening",
        "vibration": "embodied-affective-listening",
        "mediation": "transductive-media-listening",
        "codec": "transductive-media-listening",
        "microphone": "transductive-media-listening",
        "forensic": "forensic-archival-listening",
        "evidence": "forensic-archival-listening",
        "archive": "forensic-archival-listening",
        "ecology": "ecological-posthuman-listening",
        "environment": "ecological-posthuman-listening",
        "field": "ecological-posthuman-listening",
        "political": "critical-political-listening",
        "power": "critical-political-listening",
        "critical": "critical-political-listening",
        "music": "musical-aesthetic-listening",
        "rhythm": "musical-aesthetic-listening",
        "pitch": "musical-aesthetic-listening",
        "fiction": "symbolic-fictional-listening",
        "speculative": "symbolic-fictional-listening",
        "narrative": "symbolic-fictional-listening",
        "memory": "memory-lineage-listening",
        "lineage": "memory-lineage-listening",
        "history": "memory-lineage-listening",
        "covenant": "sovereign-listening",
        "sovereignty": "sovereign-listening",
        "ethics": "sovereign-listening",
        "voice": "voice-speech-listening",
        "speech": "voice-speech-listening",
        "audiovisual": "audiovisual-scenic-listening",
        "scene": "audiovisual-scenic-listening",
        "accessibility": "accessibility-normative-listening",
        "access": "accessibility-normative-listening",
        "normative": "accessibility-normative-listening",
        "material": "material-event-listening",
        "event": "material-event-listening",
        "object": "material-event-listening",
    }

    # Score modes by keyword matches
    scores: dict[str, float] = {}
    for kw in keywords:
        kw = kw.strip().lower()
        if kw in keyword_map:
            mode_id = keyword_map[kw]
            scores[mode_id] = scores.get(mode_id, 0) + 1.0

    # Intent-based scoring
    intent_lower = intent.lower()
    intent_map = {
        "technical": "signal-inspection-listening",
        "perceptual": "acoulogical-object-listening",
        "affective": "embodied-affective-listening",
        "mediation": "transductive-media-listening",
        "forensic": "forensic-archival-listening",
        "ecological": "ecological-posthuman-listening",
        "political": "critical-political-listening",
        "musical": "musical-aesthetic-listening",
        "aesthetic": "musical-aesthetic-listening",
        "fictional": "symbolic-fictional-listening",
        "speculative": "symbolic-fictional-listening",
        "memory": "memory-lineage-listening",
        "covenant": "sovereign-listening",
        "voice": "voice-speech-listening",
        "audiovisual": "audiovisual-scenic-listening",
        "accessibility": "accessibility-normative-listening",
        "material": "material-event-listening",
    }
    for intent_kw, mode_id in intent_map.items():
        if intent_kw in intent_lower:
            scores[mode_id] = scores.get(mode_id, 0) + 2.0

    # Default to acoulogical if nothing matched
    if not scores:
        scores["acoulogical-object-listening"] = 1.0

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: -x[1])

    # Build mode chain
    primary_id = ranked[0][0]
    secondary_id = ranked[1][0] if len(ranked) > 1 else None
    corrective_id = None

    # Find a corrective mode (one with corrective=true) if not already in chain
    for mode_id, _ in ranked[2:]:
        if modes.get(mode_id, {}).get("corrective", False):
            corrective_id = mode_id
            break
    if not corrective_id:
        for mode_id, mode in modes.items():
            if mode.get("corrective", False) and mode_id != primary_id and mode_id != secondary_id:
                corrective_id = mode_id
                break

    # Evidence level
    evidence_lower = evidence.lower()
    if any(w in evidence_lower for w in ["file", "audio", "recording", "waveform", "spectrogram"]):
        evidence_level = "high"
    elif any(w in evidence_lower for w in ["description", "memory", "report"]):
        evidence_level = "medium"
    else:
        evidence_level = "low"

    # Claim permissions
    claim_permissions = {
        "measured": evidence_level in ("high", "medium"),
        "interpreted": evidence_level == "high",
        "speculative": True,
    }

    # Risks
    risks = []
    if evidence_level == "low":
        risks.append("Low evidence — claims should be hedged")
    if primary_id == secondary_id:
        risks.append("Primary and secondary modes are the same — consider broadening")
    if not corrective_id:
        risks.append("No corrective mode identified — consider adding one")

    return {
        "primary_mode": primary_id,
        "primary_label": modes.get(primary_id, {}).get("label", primary_id),
        "secondary_mode": secondary_id,
        "secondary_label": modes.get(secondary_id, {}).get("label", secondary_id) if secondary_id else None,
        "corrective_mode": corrective_id,
        "corrective_label": modes.get(corrective_id, {}).get("label", corrective_id) if corrective_id else None,
        "evidence_level": evidence_level,
        "claim_permissions": claim_permissions,
        "risks": risks,
        "confidence": "high" if evidence_level == "high" and len(ranked) >= 2 else "medium",
    }
