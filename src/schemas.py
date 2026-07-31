"""
AKOÚŌ Schema Validation — Validate listening output against canonical schemas.
"""

from __future__ import annotations

import json
from typing import Any


def validate_output(output: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Validate a listening output dict against a JSON schema.

    Performs basic structural validation (required fields, type checks).
    For full validation, use a proper JSON Schema validator.
    """
    errors: list[str] = []

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in output:
            errors.append(f"Missing required field: {field}")

    # Check properties
    properties = schema.get("properties", {})
    for field, value in output.items():
        if field in properties:
            prop = properties[field]
            expected_type = prop.get("type")
            if expected_type and value is not None:
                type_map = {
                    "string": str,
                    "object": dict,
                    "array": list,
                    "number": (int, float),
                    "boolean": bool,
                }
                py_type = type_map.get(expected_type)
                if py_type and not isinstance(value, py_type):
                    errors.append(
                        f"Field '{field}': expected {expected_type}, got {type(value).__name__}"
                    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "field_count": len(output),
    }
