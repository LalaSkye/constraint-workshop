"""registry — Load and validate the MGTP transition registry from YAML."""

import yaml

from authority_gate import Evidence
from mgtp.types import RiskClass

_REQUIRED_FIELDS = {"id", "irreversible", "risk_class", "required_authority", "gate_version"}


def load_registry(path: str) -> dict:
    """Load a transition registry YAML file.

    Returns a dict mapping transition_id -> entry dict.

    Raises:
        ValueError: if the file is missing the version field, contains duplicate
                    transition IDs, is missing required fields, or has invalid
                    enum values for risk_class or required_authority.
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "version" not in data:
        raise ValueError("Registry YAML must contain a top-level 'version' field.")

    transitions = data.get("transitions", [])
    registry: dict = {}

    for entry in transitions:
        tid = entry.get("id")
        if tid is None:
            raise ValueError(f"Transition entry missing required field 'id': {entry}")

        if tid in registry:
            raise ValueError(f"Duplicate transition ID in registry: '{tid}'")

        missing = _REQUIRED_FIELDS - set(entry.keys())
        if missing:
            raise ValueError(
                f"Transition '{tid}' missing required fields: {sorted(missing)}"
            )

        # Validate risk_class against RiskClass enum.
        rc = entry["risk_class"]
        try:
            RiskClass(rc)
        except ValueError:
            valid = [e.value for e in RiskClass]
            raise ValueError(
                f"Transition '{tid}' has invalid risk_class '{rc}'. "
                f"Must be one of: {valid}"
            )

        # Validate required_authority against Evidence enum names.
        ra = entry["required_authority"]
        try:
            Evidence[ra]
        except KeyError:
            valid = [e.name for e in Evidence]
            raise ValueError(
                f"Transition '{tid}' has invalid required_authority '{ra}'. "
                f"Must be one of: {valid}"
            )

        registry[tid] = entry

    return registry
