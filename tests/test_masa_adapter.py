"""
Tests for the AKOÚŌ → MASA adapter.

Run directly (no dependencies):
    python3 tests/test_masa_adapter.py

Or with pytest:
    python -m pytest tests/test_masa_adapter.py -v
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from masa_adapter import (  # noqa: E402
    AdapterError,
    AdapterOptions,
    akouo_output_to_masa_record,
    masa_record_to_akouo_output,
)

EXAMPLE = json.loads(
    (Path(__file__).resolve().parent.parent / "examples" / "akouo-signal-inspection-output.json").read_text()
)


def test_round_trip():
    """AKOÚŌ → MASA → AKOÚŌ preserves the core listening account."""
    record = akouo_output_to_masa_record(EXAMPLE)
    back = masa_record_to_akouo_output(record)
    assert back["object_listened_to"] == EXAMPLE["object_listened_to"]
    assert back["listening_mode"] == EXAMPLE["listening_mode"]
    assert back["input_type"] == EXAMPLE["input_type"]
    assert back["what_remains_hidden"] == EXAMPLE["what_remains_hidden"]


def test_heard_boundary_agent_listener():
    """v0.9.1: an agent listener's heard claims are reclassified to inferred."""
    record = akouo_output_to_masa_record(EXAMPLE)
    kinds = [c["kind"] for c in record["claims"]]
    assert "heard" not in kinds
    assert "inferred" in kinds
    reclassified = [c for c in record["claims"] if c.get("boundary")]
    assert reclassified, "expected a boundary note on the reclassified claim"
    assert "v0.9.1" in reclassified[0]["boundary"]


def test_heard_preserved_human_listener():
    """An embodied human listener's heard claims are preserved."""
    human = copy.deepcopy(EXAMPLE)
    human["listener"] = {"kind": "human", "name": "Chris Wenn", "process": "in-person listening"}
    record = akouo_output_to_masa_record(human)
    kinds = [c["kind"] for c in record["claims"]]
    assert "heard" in kinds


def _assert_raises(exc_type, fn):
    """Minimal pytest.raises replacement (no dependencies)."""
    try:
        fn()
    except exc_type:
        return
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"expected {exc_type.__name__}, got {type(e).__name__}: {e}")
    raise AssertionError(f"expected {exc_type.__name__}, but no exception was raised")


def test_unknown_mode_raises():
    bad = copy.deepcopy(EXAMPLE)
    bad["listening_mode"] = "not-a-real-mode"
    _assert_raises(AdapterError, lambda: akouo_output_to_masa_record(bad))


def test_unknown_claim_kind_raises():
    bad = copy.deepcopy(EXAMPLE)
    bad["listening_claims"]["telepathic"] = [{"statement": "x", "confidence": "high", "basis": "y"}]
    _assert_raises(AdapterError, lambda: akouo_output_to_masa_record(bad))


def test_missing_required_field_raises():
    bad = copy.deepcopy(EXAMPLE)
    del bad["main_reading"]
    _assert_raises(AdapterError, lambda: akouo_output_to_masa_record(bad))


def test_custom_namespace():
    record = akouo_output_to_masa_record(EXAMPLE, options=AdapterOptions(namespace="techne:"))
    ext = record["extensions"]
    assert "techne:adapter" in ext
    assert "akouo:adapter" not in ext


def test_record_shape():
    """The mapped record carries the expected MASA structure."""
    record = akouo_output_to_masa_record(EXAMPLE)
    assert record["type"] == "masa:MatterRecord"
    assert record["masaVersion"] == "0.1.0"
    assert "core" in record["profiles"] and "listening" in record["profiles"]
    assert record["registers"] == ["digital-technical"]
    assert record["scales"] == ["object-event"]
    assert len(record["representations"]) == 1
    assert len(record["policies"]) == 1
    assert record["listeningPasses"][0]["modes"] == ["akouo:signal-inspection-listening"]
    assert record["listeningPasses"][0]["outcome"] == "claims"
    # every claim references the listening pass
    for c in record["claims"]:
        assert c["listeningPassRef"] == record["listeningPasses"][0]["id"]


def test_relations_use_ontology_vocabulary():
    """Relations must use predicates registered in the MASA ontology.

    The schema enforces the predicate pattern but the ontology
    (packages/core/src/generated/ontology.ts) defines semantics. Invented
    predicates would validate but carry no meaning.
    """
    record = akouo_output_to_masa_record(EXAMPLE)
    preds = {r["predicate"] for r in record["relations"]}
    assert preds <= {
        "masa:listened-as",
        "masa:attributed-to",
        "masa:measured-from",
        "masa:speculates-about",
        "masa:part-of",
    }, preds
    # every relation has the required shape
    for r in record["relations"]:
        assert r["type"] == "masa:Relation"
        assert r["subject"] and r["object"] and r["assertedBy"]
        assert r["basis"] and r["extensions"] == {}


def test_relations_cover_claims():
    """Every claim is attributed to the actor and linked to the representation."""
    record = akouo_output_to_masa_record(EXAMPLE)
    claim_ids = {c["id"] for c in record["claims"]}
    attributed = {
        r["subject"] for r in record["relations"] if r["predicate"] == "masa:attributed-to"
    }
    assert claim_ids == attributed


if __name__ == "__main__":
    passed = 0
    failed = 0
    for name in sorted(dir()):
        if name.startswith("test_"):
            fn = globals()[name]
            try:
                fn()
                print(f"PASS {name}")
                passed += 1
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {name}: {e}")
                failed += 1
    print(f"---\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
