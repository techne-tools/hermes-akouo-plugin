"""
AKOÚŌ → MASA adapter — map AKOÚŌ listening outputs into MASA matter records.

Derivative work notice
=====================

This module is a **derivative integration** of two upstream projects, used
under the MIT License. It is a mapping, not a claim that AKOÚŌ terms are
equivalent to MASA Core terms (MASA adapter contract, adapters/README.md).

1. AKOÚŌ — Operational ears for the agentic era
   Author: emeisazam (eme) — https://github.com/emeisazam
   Organisation: Sonic Field Labs — https://github.com/sonicfieldlabs
   Repository: https://github.com/sonicfieldlabs/akouo
   Version integrated: v0.9.1 (2026-08-02)
   License: MIT — Copyright (c) 2026 akoúō contributors

2. MASA — Sound Matter Aware protocol
   Organisation: Sonic Field Labs — https://github.com/sonicfieldlabs
   Repository: https://github.com/sonicfieldlabs/MASA
   Version integrated: v0.1.0 (2026-07-27)
   License: MIT — Copyright (c) 2026 Sonic Field Labs

The claim taxonomy, listening modes, and epistemic discipline originate
with AKOÚŌ (emeisazam). The record envelope, qualified states, and
conformance contract originate with MASA (Sonic Field Labs). This adapter
is Chris Wenn's inflection of both for practice-as-research at the
University of the Arts Sharjah; it leverages, and does not appropriate,
the upstream work.

Epistemic boundary (AKOÚŌ v0.9.1)
=================================

Since v0.9.1, AKOÚŌ reserves the ``heard`` claim kind for **reports by an
embodied listener** of what was directly present to a declared auditory or
perceptual aperture. Model, sensor, prompt, transcript, field-note, and
description outputs remain measured, inferred, interpreted, or undetermined;
they do not become heard claims by processing represented sound
(claim-taxonomy.schema.json, v0.9.1).

This adapter enforces that boundary: a listening output whose ``listener``
is not an embodied human listener is never emitted with ``heard`` claims.
MASA's Claim schema independently requires ``listeningPassRef`` for
``heard`` claims, so the two contracts agree.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ── Upstream references (cited) ────────────────────────────────────────────

AKOUO_UPSTREAM = {
    "author": "emeisazam (eme)",
    "organisation": "Sonic Field Labs",
    "repository": "https://github.com/sonicfieldlabs/akouo",
    "version": "v0.9.1",
    "license": "MIT",
    "copyright": "Copyright (c) 2026 akoúō contributors",
}

MASA_UPSTREAM = {
    "organisation": "Sonic Field Labs",
    "repository": "https://github.com/sonicfieldlabs/MASA",
    "version": "0.1.0",
    "license": "MIT",
    "copyright": "Copyright (c) 2026 Sonic Field Labs",
}

# AKOÚŌ claim kinds (claim-taxonomy.schema.json, v0.9.1) — identical to MASA
# Claim.kind enum (definitions.schema.json, 0.1.0).
CLAIM_KINDS = ("heard", "measured", "inferred", "interpreted", "speculative", "undetermined")

# AKOÚŌ listening modes (listening-output.schema.json, v0.9.1) — carried as
# namespaced MASA modes. MASA's ListeningPass.modes is an open string array
# (no enum), so no protocol change is required.
AKOUO_MODES = (
    "signal-inspection-listening",
    "acoulogical-object-listening",
    "embodied-affective-listening",
    "transductive-media-listening",
    "forensic-archival-listening",
    "ecological-posthuman-listening",
    "critical-political-listening",
    "musical-aesthetic-listening",
    "symbolic-fictional-listening",
    "audiovisual-scenic-listening",
    "voice-speech-listening",
    "accessibility-normative-listening",
    "material-event-listening",
    "memory-lineage-listening",
    "sovereign-listening",
)

# AKOÚŌ input types (listening-output.schema.json, v0.9.1).
AKOUO_INPUT_TYPES = (
    "audio_file", "sound_prompt", "transcript", "field_note", "archive_note",
    "dataset_description", "spectrogram", "waveform", "video", "metadata",
    "model_output", "mixed", "unknown", "other",
)

# MASA profiles used by this adapter (MASA README, 0.1.0).
MASA_PROFILES = ["core", "listening"]


@dataclass
class AdapterOptions:
    """Options controlling the AKOÚŌ → MASA mapping.

    Attributes:
        namespace: Extension namespace for AKOÚŌ-specific fields.
            Defaults to ``akouo:`` per the MASA adapter contract
            (adapters/README.md: real applications choose and govern
            their own namespace).
        default_actor_kind: Actor kind for the listening actor when the
            AKOÚŌ output does not declare one.
        enforce_heard_boundary: When True (default), model/sensor/prompt/
            transcript/description outputs are never emitted with ``heard``
            claims, per AKOÚŌ v0.9.1.
    """

    namespace: str = "akouo:"
    default_actor_kind: str = "agent"
    enforce_heard_boundary: bool = True


class AdapterError(ValueError):
    """Raised when an AKOÚŌ output cannot be mapped to a MASA record."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _urn(prefix: str = "") -> str:
    return f"urn:uuid:{uuid.uuid4()}"


def _qualified(value: Any, state: str = "known") -> dict[str, Any]:
    """Build a MASA QualifiedValue (definitions.schema.json, 0.1.0)."""
    return {"state": state, "value": value}


def _is_embodied_listener(listener: dict[str, Any] | None) -> bool:
    """Whether the AKOÚŌ listener declaration is an embodied human listener.

    AKOÚŌ v0.6+ declares ``listener`` as human, agent, or hybrid under a
    process (listening-output.schema.json). Only human (or hybrid with a
    human component) listeners can produce ``heard`` claims under the
    v0.9.1 boundary.
    """
    if not listener:
        return False
    kind = listener.get("kind") or listener.get("type") or ""
    if kind == "human":
        return True
    if kind == "hybrid":
        # A hybrid listener may report heard claims only if a human
        # component is declared; otherwise the report is attributable
        # to the model and stays inferred.
        return bool(listener.get("human_component") or listener.get("human"))
    return False


def _map_claim_kind(kind: str) -> str:
    """Map an AKOÚŌ claim kind to a MASA Claim.kind.

    The taxonomies are identical (AKOÚŌ claim-taxonomy.schema.json v0.9.1;
    MASA definitions.schema.json 0.1.0), so this is a pass-through with
    validation.
    """
    if kind not in CLAIM_KINDS:
        raise AdapterError(f"Unknown claim kind: {kind!r}")
    return kind


def _map_confidence(akouo_confidence: str) -> dict[str, Any]:
    """Map an AKOÚŌ confidence level to a MASA Confidence object.

    AKOÚŌ confidence is one of low/medium/high (claim-taxonomy.schema.json,
    v0.9.1). MASA Confidence requires an assessed structure with status,
    method, expression, and scale (definitions.schema.json, 0.1.0).
    """
    if akouo_confidence not in ("low", "medium", "high"):
        return {"status": "not_assessed"}
    return {
        "status": "assessed",
        "method": "akouo-confidence",
        "expression": akouo_confidence,
        "scale": "akouo-confidence-scale",
    }


def _map_method(name: str) -> dict[str, Any]:
    """Build a MASA Method object (definitions.schema.json, 0.1.0).

    Method requires name, version (QualifiedValue), and parameters.
    """
    return {
        "name": name,
        "version": {"state": "known", "value": AKOUO_UPSTREAM["version"]},
        "parameters": {},
    }


def _map_claims(
    listening_claims: dict[str, list[dict[str, Any]]],
    *,
    listener: dict[str, Any] | None,
    enforce_heard_boundary: bool,
    about_refs: list[str],
    basis_ref: str,
) -> list[dict[str, Any]]:
    """Map AKOÚŌ ``listening_claims`` to MASA Claim objects.

    Each AKOÚŌ claim has ``statement``, ``confidence``, and ``basis``
    (claim-taxonomy.schema.json, v0.9.1). MASA Claim requires ``id``,
    ``type``, ``kind``, ``about`` (minItems 1), ``basis`` (EvidenceReference
    list with ref+role), ``actor``, ``createdAt``, ``method``, ``confidence``,
    ``uncertainty``, ``disclosure``, ``extensions``
    (definitions.schema.json, 0.1.0).

    The v0.9.1 embodied heard-claim boundary is enforced here: when the
    listener is not an embodied human listener, ``heard`` claims are
    reclassified as ``inferred`` (attributable model perception) and a
    boundary note is attached.
    """
    claims: list[dict[str, Any]] = []
    unknown_kinds = [k for k in listening_claims if k not in CLAIM_KINDS]
    if unknown_kinds:
        raise AdapterError(f"Unknown claim kinds: {', '.join(sorted(unknown_kinds))}")
    for kind in CLAIM_KINDS:
        for claim in listening_claims.get(kind, []):
            mapped_kind = _map_claim_kind(kind)
            boundary_note = None
            if kind == "heard" and enforce_heard_boundary and not _is_embodied_listener(listener):
                mapped_kind = "inferred"
                boundary_note = (
                    "Reclassified from heard per AKOÚŌ v0.9.1: model, sensor, prompt, "
                    "transcript, field-note, and description outputs do not become heard "
                    "claims by processing represented sound."
                )
            claim_obj: dict[str, Any] = {
                "id": _urn(),
                "type": "masa:Claim",
                "kind": mapped_kind,
                "about": about_refs,
                "basis": [
                    {
                        "ref": basis_ref,
                        "role": "representation",
                        "locator": claim.get("basis", ""),
                    }
                ],
                "actor": _urn("actor"),
                "createdAt": _now(),
                "content": claim.get("statement", ""),
                "method": _map_method("akouo-listening"),
                "confidence": _map_confidence(claim.get("confidence", "")),
                "uncertainty": [],
                "disclosure": "private",
                "extensions": {},
            }
            # MASA Claim kind-specific requirements (definitions.schema.json,
            # 0.1.0): measured needs value/unit/window; interpreted needs
            # position; undetermined needs uncertainty (minItems 1);
            # speculative needs boundary.
            if mapped_kind == "measured":
                claim_obj["value"] = claim.get("statement", "")
                claim_obj["unit"] = "akouo-statement"
                claim_obj["window"] = {
                    "kind": "record",
                    "unit": "record",
                    "start": 0,
                    "end": 1,
                }
            elif mapped_kind == "interpreted":
                claim_obj["position"] = _qualified("listening")
            elif mapped_kind == "undetermined":
                claim_obj["uncertainty"] = [claim.get("basis", "Unavailable contextual evidence")]
            elif mapped_kind == "speculative":
                claim_obj["boundary"] = claim.get("basis", "Speculative boundary")
            if boundary_note:
                claim_obj["boundary"] = boundary_note
            claims.append(claim_obj)
    return claims


def _map_modes(listening_mode: str) -> list[str]:
    """Map an AKOÚŌ listening mode to a namespaced MASA mode.

    MASA ListeningPass.modes is an open string array (definitions.schema.json,
    0.1.0); AKOÚŌ modes are carried as ``akouo:<mode>`` attributed terms.
    """
    if listening_mode not in AKOUO_MODES:
        raise AdapterError(f"Unknown AKOÚŌ listening mode: {listening_mode!r}")
    return [f"akouo:{listening_mode}"]


def _map_encounter(
    output: dict[str, Any],
    *,
    actor_id: str,
    namespace: str,
) -> dict[str, Any]:
    """Map the listening situation to a MASA Encounter.

    MASA Encounter requires id, type, occurredAt, actors, question,
    position, accessConditions, contextRefs, extensions
    (definitions.schema.json, 0.1.0).
    """
    return {
        "id": _urn(),
        "type": "masa:Encounter",
        "occurredAt": _now(),
        "actors": [actor_id],
        "question": output.get("object_listened_to", ""),
        "position": _qualified("listening"),
        "accessConditions": [],
        "contextRefs": [],
        "extensions": {
            f"{namespace}input_type": output.get("input_type", "unknown"),
        },
    }


def _map_aperture(
    output: dict[str, Any],
    *,
    namespace: str,
) -> dict[str, Any]:
    """Map the AKOÚŌ apparatus declaration to a MASA Aperture.

    MASA Aperture requires id, type, description, channels, ranges,
    windows, preprocessing (Method list), exclusions, blindSpots,
    extensions (definitions.schema.json, 0.1.0). AKOÚŌ's ``apparatus``
    declaration (v0.6+) describes the listening substrate; it maps to the
    aperture's channels and preprocessing.
    """
    apparatus = output.get("apparatus", {})
    channels = apparatus.get("channels", []) if isinstance(apparatus, dict) else []
    preprocessing = apparatus.get("preprocessing", []) if isinstance(apparatus, dict) else []
    return {
        "id": _urn(),
        "type": "masa:Aperture",
        "description": (
            f"AKOÚŌ {output.get('listening_mode', '')} aperture "
            f"({AKOUO_UPSTREAM['version']})"
        ),
        "channels": channels if isinstance(channels, list) else [],
        "ranges": [],
        "windows": [],
        "preprocessing": [_map_method(p) for p in preprocessing] if isinstance(preprocessing, list) else [],
        "exclusions": [],
        "blindSpots": output.get("what_remains_hidden", []),
        "extensions": {
            f"{namespace}apparatus": apparatus,
        },
    }


def _map_listening_pass(
    output: dict[str, Any],
    *,
    actor_id: str,
    encounter_id: str,
    aperture_id: str,
    claim_ids: list[str],
    representation_id: str,
    namespace: str,
) -> dict[str, Any]:
    """Map an AKOÚŌ listening output to a MASA ListeningPass.

    MASA ListeningPass requires id, type, actors, representations
    (minItems 1), encounterRef, apertureRef, modes, createdAt, outcome,
    claimRefs, disclosure, extensions (definitions.schema.json, 0.1.0).
    Outcome is ``claims`` when claimRefs is non-empty, else ``undetermined``.
    """
    outcome = "claims" if claim_ids else "undetermined"
    return {
        "id": _urn(),
        "type": "masa:ListeningPass",
        "actors": [actor_id],
        "representations": [representation_id],
        "encounterRef": encounter_id,
        "apertureRef": aperture_id,
        "modes": _map_modes(output.get("listening_mode", "")),
        "createdAt": _now(),
        "outcome": outcome,
        "claimRefs": claim_ids,
        "notes": (
            f"AKOÚŌ {output.get('listening_mode', '')} pass; "
            f"main reading: {output.get('main_reading', '')}; "
            f"alternative reading: {output.get('alternative_reading', '')}"
        ),
        "disclosure": "private",
        "extensions": {
            f"{namespace}akouo_version": output.get("akouo_version", AKOUO_UPSTREAM["version"]),
            f"{namespace}listener": output.get("listener", {}),
            f"{namespace}memory": output.get("memory", {}),
            f"{namespace}covenant": output.get("covenant", {}),
            f"{namespace}what_appears": output.get("what_appears", []),
            f"{namespace}mediations": output.get("mediations", []),
            f"{namespace}risks": output.get("risks", []),
            f"{namespace}recommended_next_mode": output.get("recommended_next_mode", "none"),
        },
    }


def akouo_output_to_masa_record(
    output: dict[str, Any],
    *,
    options: AdapterOptions | None = None,
) -> dict[str, Any]:
    """Map an AKOÚŌ standard listening output to a MASA matter record.

    Args:
        output: An AKOÚŌ listening output conforming to
            listening-output.schema.json (v0.9.1).
        options: Mapping options (namespace, heard-boundary enforcement).

    Returns:
        A MASA matter record conforming to matter-record.schema.json (0.1.0).

    Raises:
        AdapterError: If the output cannot be mapped (unknown mode, unknown
            claim kind, missing required fields).

    References:
        - AKOÚŌ listening-output.schema.json, v0.9.1 (emeisazam / Sonic Field Labs)
        - AKOÚŌ claim-taxonomy.schema.json, v0.9.1 (emeisazam / Sonic Field Labs)
        - MASA matter-record.schema.json, 0.1.0 (Sonic Field Labs)
        - MASA definitions.schema.json, 0.1.0 (Sonic Field Labs)
        - MASA adapters/README.md, 0.1.0 (Sonic Field Labs)
    """
    options = options or AdapterOptions()
    namespace = options.namespace

    # Validate required AKOÚŌ fields (listening-output.schema.json, v0.9.1).
    required = (
        "object_listened_to", "input_type", "listening_mode", "listening_claims",
        "what_appears", "what_remains_hidden", "mediations", "risks",
        "main_reading", "alternative_reading", "recommended_next_mode",
    )
    missing = [f for f in required if f not in output]
    if missing:
        raise AdapterError(f"Missing required AKOÚŌ fields: {', '.join(missing)}")

    if output.get("input_type") not in AKOUO_INPUT_TYPES:
        raise AdapterError(f"Unknown AKOÚŌ input_type: {output.get('input_type')!r}")

    listener = output.get("listener", {})
    actor_id = _urn("actor")
    encounter_id = _urn("encounter")
    aperture_id = _urn("aperture")
    representation_id = _urn("representation")
    policy_id = _urn("policy")
    rule_id = _urn("rule")

    claims = _map_claims(
        output.get("listening_claims", {}),
        listener=listener,
        enforce_heard_boundary=options.enforce_heard_boundary,
        about_refs=[representation_id],
        basis_ref=representation_id,
    )
    claim_ids = [c["id"] for c in claims]
    for c in claims:
        c["actor"] = actor_id
        c["listeningPassRef"] = None  # filled after pass id is known

    encounter = _map_encounter(output, actor_id=actor_id, namespace=namespace)
    aperture = _map_aperture(output, namespace=namespace)
    listening_pass = _map_listening_pass(
        output,
        actor_id=actor_id,
        encounter_id=encounter["id"],
        aperture_id=aperture["id"],
        claim_ids=claim_ids,
        representation_id=representation_id,
        namespace=namespace,
    )
    for c in claims:
        c["listeningPassRef"] = listening_pass["id"]

    record = {
        "$schema": "https://masa.sonicfield.org/schemas/0.1.0/matter-record.schema.json",
        "masaVersion": "0.1.0",
        "id": _urn("record"),
        "type": "masa:MatterRecord",
        "revision": 1,
        "profiles": MASA_PROFILES,
        "createdAt": _now(),
        "createdBy": actor_id,
        "title": f"AKOÚŌ {output.get('listening_mode', '')} listening account",
        "description": (
            "Mapped from an AKOÚŌ listening output by the techne-tools "
            "hermes-akouo-plugin adapter. AKOÚŌ is by emeisazam / Sonic Field "
            "Labs (MIT); MASA is by Sonic Field Labs (MIT)."
        ),
        "disclosure": "private",
        "registers": ["digital-technical"],
        "scales": ["object-event"],
        "actors": [
            {
                "id": actor_id,
                "type": "masa:Actor",
                "actorKind": options.default_actor_kind,
                "roles": ["listener"],
                "name": _qualified(listener.get("name", "AKOÚŌ listener")),
                "disclosure": "private",
                "extensions": {
                    f"{namespace}listener_declaration": listener,
                },
            }
        ],
        "sources": [],
        "representations": [
            {
                "id": representation_id,
                "type": "masa:Representation",
                "role": "source-representation",
                "mediaType": "audio/wav",
                "format": {
                    "state": "unknown",
                    "reason": "The AKOÚŌ output does not bundle source bytes.",
                    "reasonCode": "not_bundled",
                },
                "availability": "unavailable",
                "locator": {
                    "state": "unavailable",
                    "reason": "No asset is bundled with this mapped record.",
                    "reasonCode": "not_bundled",
                },
                "integrity": {
                    "state": "unknown",
                    "reason": "Integrity cannot be verified without bytes.",
                    "reasonCode": "not_bundled",
                },
                "policyRefs": [policy_id],
                "disclosure": "private",
                "extensions": {
                    f"{namespace}object_listened_to": output.get("object_listened_to", ""),
                },
            }
        ],
        "encounters": [encounter],
        "apertures": [aperture],
        "listeningPasses": [listening_pass],
        "claims": claims,
        "measurements": [],
        "regions": [],
        "observations": [],
        "mappings": [],
        "relations": [],
        "policies": [
            {
                "id": policy_id,
                "type": "masa:Policy",
                "policyKind": "composite",
                "issuer": actor_id,
                "status": "active",
                "disclosure": "private",
                "rules": [
                    {
                        "id": rule_id,
                        "effect": "permission",
                        "actions": ["read", "validate"],
                        "targets": [representation_id],
                        "subjects": [actor_id],
                        "authorityBasis": {
                            "state": "known",
                            "value": "Local creator declaration for this private mapped record",
                        },
                        "constraints": {"network": "prohibited"},
                        "duties": ["Preserve provenance and unknown states"],
                    }
                ],
                "review": {
                    "contact": {
                        "state": "unknown",
                        "reason": "No external contact exists for a local mapped record.",
                        "reasonCode": "local_fixture",
                    },
                    "route": {
                        "state": "known",
                        "value": "Review the record with the local MASA CLI",
                    },
                },
                "extensions": {},
            }
        ],
        "contexts": [],
        "agentRuns": [],
        "capabilities": [],
        "integrity": {
            "state": "unknown",
            "reason": "The mapped record is an account rather than a bundled byte artifact.",
            "reasonCode": "not_bundled",
        },
        "history": {"mode": "embedded", "events": []},
        "extensions": {
            f"{namespace}adapter": {
                "name": "hermes-akouo-plugin.masa_adapter",
                "version": "0.1.0",
                "akouo_version": AKOUO_UPSTREAM["version"],
                "masa_version": MASA_UPSTREAM["version"],
                "upstream_akouo": AKOUO_UPSTREAM["repository"],
                "upstream_masa": MASA_UPSTREAM["repository"],
            }
        },
    }
    return record


def masa_record_to_akouo_output(record: dict[str, Any]) -> dict[str, Any]:
    """Map a MASA matter record back to an AKOÚŌ listening output.

    This is the reverse direction of the adapter. It is lossy by design:
    MASA fields that have no AKOÚŌ equivalent (e.g. measurements, regions,
    policies) are dropped, and AKOÚŌ-specific fields are recovered from the
    ``akouo:`` extension namespace.

    References:
        - MASA adapters/README.md, 0.1.0: adapters must document loss,
          default, unknown, and withheld behavior.
    """
    namespace = "akouo:"
    listening_pass = record["listeningPasses"][0]
    encounter = record["encounters"][0]
    aperture = record["apertures"][0]
    actor = record["actors"][0]

    claims: dict[str, list[dict[str, Any]]] = {k: [] for k in CLAIM_KINDS}
    for claim in record.get("claims", []):
        kind = claim.get("kind", "undetermined")
        if kind not in claims:
            claims[kind] = []
        claims[kind].append(
            {
                "statement": claim.get("content", ""),
                "confidence": claim.get("confidence", "undetermined"),
                "basis": claim.get("basis", [{}])[0].get("description", "")
                if claim.get("basis") else "",
            }
        )

    ext = listening_pass.get("extensions", {})
    return {
        "object_listened_to": encounter.get("question", ""),
        "input_type": encounter.get("extensions", {}).get(f"{namespace}input_type", "unknown"),
        "listening_mode": listening_pass.get("modes", ["unknown"])[0].removeprefix("akouo:"),
        "listening_claims": claims,
        "what_appears": ext.get(f"{namespace}what_appears", []),
        "what_remains_hidden": aperture.get("blindSpots", []),
        "mediations": ext.get(f"{namespace}mediations", []),
        "risks": ext.get(f"{namespace}risks", []),
        "main_reading": "",
        "alternative_reading": "",
        "recommended_next_mode": ext.get(f"{namespace}recommended_next_mode", "none"),
        "akouo_version": ext.get(f"{namespace}akouo_version", AKOUO_UPSTREAM["version"]),
        "apparatus": aperture.get("extensions", {}).get(f"{namespace}apparatus", {}),
        "listener": ext.get(f"{namespace}listener", {}),
        "memory": ext.get(f"{namespace}memory", {}),
        "covenant": ext.get(f"{namespace}covenant", {}),
    }


def main() -> None:
    """CLI entry point: map an AKOÚŌ output JSON file to a MASA record."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Map an AKOÚŌ listening output to a MASA matter record."
    )
    parser.add_argument("input", help="Path to AKOÚŌ listening output JSON")
    parser.add_argument("--out", help="Output path (default: stdout)")
    parser.add_argument(
        "--no-heard-boundary",
        action="store_true",
        help="Disable the v0.9.1 embodied heard-claim boundary (not recommended)",
    )
    args = parser.parse_args()

    with open(args.input) as f:
        output = json.load(f)

    options = AdapterOptions(enforce_heard_boundary=not args.no_heard_boundary)
    record = akouo_output_to_masa_record(output, options=options)
    text = json.dumps(record, indent=2)

    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
