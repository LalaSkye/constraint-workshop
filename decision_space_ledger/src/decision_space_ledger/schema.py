"""Schema definition and strict validation for decision_space_snapshot_v1.

Validates without any third-party dependencies.  All checks are explicit and
deterministic.  Raises ValueError with a descriptive message on any violation.
"""

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "decision_space_snapshot_v1",
    "type": "object",
    "required": [
        "version",
        "variables",
        "allowed_transitions",
        "exclusions",
        "reason_code_families",
    ],
    "additionalProperties": False,
    "properties": {
        "version": {"type": "string", "enum": ["v1"]},
        "variables": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
        "allowed_transitions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["from", "to"],
                "additionalProperties": False,
                "properties": {
                    "from": {"type": "string"},
                    "to": {"type": "string"},
                },
            },
        },
        "exclusions": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
        },
        "reason_code_families": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True,
            },
        },
    },
}

_REQUIRED_KEYS = frozenset(SCHEMA["required"])
_ALLOWED_KEYS = frozenset(SCHEMA["properties"])


def validate(snapshot):
    """Validate a decision_space_snapshot_v1 dict strictly.

    Returns the snapshot unchanged if valid.
    Raises ValueError with a descriptive message on any violation.
    """
    if not isinstance(snapshot, dict):
        raise ValueError(
            f"snapshot must be a dict, got {type(snapshot).__name__}"
        )

    extra_keys = set(snapshot) - _ALLOWED_KEYS
    if extra_keys:
        raise ValueError(
            f"unexpected keys in snapshot: {sorted(extra_keys)}"
        )

    for key in sorted(_REQUIRED_KEYS):
        if key not in snapshot:
            raise ValueError(f"required key missing: '{key}'")

    # version
    version = snapshot["version"]
    if not isinstance(version, str):
        raise ValueError(
            f"version must be a string, got {type(version).__name__}"
        )
    if version != "v1":
        raise ValueError(f"version must be 'v1', got {version!r}")

    # variables
    variables = snapshot["variables"]
    if not isinstance(variables, list):
        raise ValueError(
            f"variables must be a list, got {type(variables).__name__}"
        )
    for i, v in enumerate(variables):
        if not isinstance(v, str):
            raise ValueError(
                f"variables[{i}] must be a string, got {type(v).__name__}"
            )
    if len(variables) != len(set(variables)):
        raise ValueError("variables must contain unique items")

    # allowed_transitions
    transitions = snapshot["allowed_transitions"]
    if not isinstance(transitions, list):
        raise ValueError(
            f"allowed_transitions must be a list, got {type(transitions).__name__}"
        )
    for i, t in enumerate(transitions):
        if not isinstance(t, dict):
            raise ValueError(
                f"allowed_transitions[{i}] must be an object, got {type(t).__name__}"
            )
        extra_t = set(t) - {"from", "to"}
        if extra_t:
            raise ValueError(
                f"allowed_transitions[{i}] has unexpected keys: {sorted(extra_t)}"
            )
        for field in ("from", "to"):
            if field not in t:
                raise ValueError(
                    f"allowed_transitions[{i}] missing required key '{field}'"
                )
            if not isinstance(t[field], str):
                raise ValueError(
                    f"allowed_transitions[{i}]['{field}'] must be a string, "
                    f"got {type(t[field]).__name__}"
                )

    # exclusions
    exclusions = snapshot["exclusions"]
    if not isinstance(exclusions, list):
        raise ValueError(
            f"exclusions must be a list, got {type(exclusions).__name__}"
        )
    for i, e in enumerate(exclusions):
        if not isinstance(e, str):
            raise ValueError(
                f"exclusions[{i}] must be a string, got {type(e).__name__}"
            )
    if len(exclusions) != len(set(exclusions)):
        raise ValueError("exclusions must contain unique items")

    # reason_code_families
    families = snapshot["reason_code_families"]
    if not isinstance(families, dict):
        raise ValueError(
            f"reason_code_families must be an object, got {type(families).__name__}"
        )
    for family_name, codes in families.items():
        if not isinstance(family_name, str):
            raise ValueError(
                f"reason_code_families key must be a string, "
                f"got {type(family_name).__name__}"
            )
        if not isinstance(codes, list):
            raise ValueError(
                f"reason_code_families['{family_name}'] must be a list, "
                f"got {type(codes).__name__}"
            )
        for i, code in enumerate(codes):
            if not isinstance(code, str):
                raise ValueError(
                    f"reason_code_families['{family_name}'][{i}] must be a string, "
                    f"got {type(code).__name__}"
                )
        if len(codes) != len(set(codes)):
            raise ValueError(
                f"reason_code_families['{family_name}'] must contain unique items"
            )

    return snapshot
