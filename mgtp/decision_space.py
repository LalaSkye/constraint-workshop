"""decision_space — Deterministic Decision-Space Diff Ledger.

Schema: decision_space_snapshot_v1

{
  "version": "v1",
  "variables": [string],
  "allowed_transitions": [{"from": string, "to": string}],
  "exclusions": [string],
  "reason_code_families": {"<family>": [string]}
}

All operations are deterministic, stdlib-only, fail-closed on schema violation.
"""

import hashlib
import json


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_snapshot(snapshot: dict) -> None:
    """Validate a decision-space snapshot against the v1 schema.

    Raises ValueError on any schema violation.
    All checks are deterministic and fail-closed.
    """
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a dict")

    # version
    if "version" not in snapshot:
        raise ValueError("missing required field: version")
    if snapshot["version"] != "v1":
        raise ValueError(f"unsupported version: {snapshot['version']!r}; expected 'v1'")

    # variables
    if "variables" not in snapshot:
        raise ValueError("missing required field: variables")
    if not isinstance(snapshot["variables"], list):
        raise ValueError("variables must be a list")
    for i, v in enumerate(snapshot["variables"]):
        if not isinstance(v, str):
            raise ValueError(f"variables[{i}] must be a string, got {type(v).__name__}")

    # allowed_transitions
    if "allowed_transitions" not in snapshot:
        raise ValueError("missing required field: allowed_transitions")
    if not isinstance(snapshot["allowed_transitions"], list):
        raise ValueError("allowed_transitions must be a list")
    for i, t in enumerate(snapshot["allowed_transitions"]):
        if not isinstance(t, dict):
            raise ValueError(f"allowed_transitions[{i}] must be a dict")
        if "from" not in t:
            raise ValueError(f"allowed_transitions[{i}] missing field: from")
        if "to" not in t:
            raise ValueError(f"allowed_transitions[{i}] missing field: to")
        if not isinstance(t["from"], str):
            raise ValueError(f"allowed_transitions[{i}].from must be a string")
        if not isinstance(t["to"], str):
            raise ValueError(f"allowed_transitions[{i}].to must be a string")

    # exclusions
    if "exclusions" not in snapshot:
        raise ValueError("missing required field: exclusions")
    if not isinstance(snapshot["exclusions"], list):
        raise ValueError("exclusions must be a list")
    for i, e in enumerate(snapshot["exclusions"]):
        if not isinstance(e, str):
            raise ValueError(f"exclusions[{i}] must be a string, got {type(e).__name__}")

    # reason_code_families
    if "reason_code_families" not in snapshot:
        raise ValueError("missing required field: reason_code_families")
    if not isinstance(snapshot["reason_code_families"], dict):
        raise ValueError("reason_code_families must be a dict")
    for family, codes in snapshot["reason_code_families"].items():
        if not isinstance(family, str):
            raise ValueError(f"reason_code_families key must be a string, got {type(family).__name__}")
        if not isinstance(codes, list):
            raise ValueError(f"reason_code_families[{family!r}] must be a list")
        for j, code in enumerate(codes):
            if not isinstance(code, str):
                raise ValueError(
                    f"reason_code_families[{family!r}][{j}] must be a string, got {type(code).__name__}"
                )


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------

def canonicalize_snapshot(snapshot: dict) -> dict:
    """Return a deterministically sorted copy of a snapshot.

    - variables, exclusions: sorted lexicographically
    - allowed_transitions: sorted by (from, to)
    - reason_code_families: keys sorted, each value list sorted
    - version: preserved as-is
    """
    return {
        "version": snapshot["version"],
        "variables": sorted(snapshot["variables"]),
        "allowed_transitions": sorted(
            snapshot["allowed_transitions"], key=lambda t: (t["from"], t["to"])
        ),
        "exclusions": sorted(snapshot["exclusions"]),
        "reason_code_families": {
            family: sorted(codes)
            for family, codes in sorted(snapshot["reason_code_families"].items())
        },
    }


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def snapshot_hash(snapshot: dict) -> str:
    """Return SHA256 hex digest (lower-case) of the canonical JSON of a snapshot.

    The snapshot is canonicalized before hashing, so key insertion order
    and list order do not affect the result.
    """
    canonical = canonicalize_snapshot(snapshot)
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def diff_snapshots(a: dict, b: dict) -> dict:
    """Compute a deterministic structural diff between two snapshots.

    Both snapshots are validated and canonicalized before diffing.

    Returns:
    {
      "variables_added": [str],
      "variables_removed": [str],
      "transitions_added": [{"from": str, "to": str}],
      "transitions_removed": [{"from": str, "to": str}],
      "exclusions_added": [str],
      "exclusions_removed": [str],
      "reason_codes_added": {family: [str]},
      "reason_codes_removed": {family: [str]}
    }
    """
    validate_snapshot(a)
    validate_snapshot(b)

    ca = canonicalize_snapshot(a)
    cb = canonicalize_snapshot(b)

    # variables
    vars_a = set(ca["variables"])
    vars_b = set(cb["variables"])

    # transitions — represent as frozensets of (from, to) tuples
    def _transition_key(t):
        return (t["from"], t["to"])

    trans_a = {_transition_key(t): t for t in ca["allowed_transitions"]}
    trans_b = {_transition_key(t): t for t in cb["allowed_transitions"]}

    # exclusions
    excl_a = set(ca["exclusions"])
    excl_b = set(cb["exclusions"])

    # reason_code_families
    all_families = sorted(set(ca["reason_code_families"]) | set(cb["reason_code_families"]))
    reason_codes_added = {}
    reason_codes_removed = {}
    for family in all_families:
        codes_a = set(ca["reason_code_families"].get(family, []))
        codes_b = set(cb["reason_code_families"].get(family, []))
        added = sorted(codes_b - codes_a)
        removed = sorted(codes_a - codes_b)
        if added:
            reason_codes_added[family] = added
        if removed:
            reason_codes_removed[family] = removed

    return {
        "variables_added": sorted(vars_b - vars_a),
        "variables_removed": sorted(vars_a - vars_b),
        "transitions_added": sorted(
            [trans_b[k] for k in set(trans_b) - set(trans_a)],
            key=_transition_key,
        ),
        "transitions_removed": sorted(
            [trans_a[k] for k in set(trans_a) - set(trans_b)],
            key=_transition_key,
        ),
        "exclusions_added": sorted(excl_b - excl_a),
        "exclusions_removed": sorted(excl_a - excl_b),
        "reason_codes_added": reason_codes_added,
        "reason_codes_removed": reason_codes_removed,
    }
