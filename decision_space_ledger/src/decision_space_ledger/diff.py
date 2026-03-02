"""Structured diff between two decision_space_snapshot_v1 instances.

All diff results are deterministic: lists are sorted lexicographically so the
same logical change always produces identical output.
"""


def diff(snapshot_a, snapshot_b):
    """Compute a structured diff between two validated snapshots.

    Both snapshots must already have been validated with ``schema.validate``.

    Returns a dict with the following keys:

    ``is_identical``
        True if the two snapshots are logically equivalent.

    ``variables_added`` / ``variables_removed``
        Sorted lists of variable names present in b but not a (or vice versa).

    ``transitions_added`` / ``transitions_removed``
        Sorted lists of ``{"from": ..., "to": ...}`` dicts present in b but
        not a (or vice versa).  Sorted by (from, to).

    ``exclusions_added`` / ``exclusions_removed``
        Sorted lists of exclusion strings.

    ``reason_code_families_added`` / ``reason_code_families_removed``
        Sorted lists of family names new in b / absent from b.

    ``reason_code_families_changed``
        Dict mapping each changed family name to
        ``{"codes_added": [...], "codes_removed": [...]}``.
    """
    vars_a = set(snapshot_a["variables"])
    vars_b = set(snapshot_b["variables"])

    trans_a = {(t["from"], t["to"]) for t in snapshot_a["allowed_transitions"]}
    trans_b = {(t["from"], t["to"]) for t in snapshot_b["allowed_transitions"]}

    excl_a = set(snapshot_a["exclusions"])
    excl_b = set(snapshot_b["exclusions"])

    fam_a = snapshot_a["reason_code_families"]
    fam_b = snapshot_b["reason_code_families"]

    families_added = sorted(set(fam_b) - set(fam_a))
    families_removed = sorted(set(fam_a) - set(fam_b))

    families_changed = {}
    for family in sorted(set(fam_a) & set(fam_b)):
        codes_a = set(fam_a[family])
        codes_b = set(fam_b[family])
        added = sorted(codes_b - codes_a)
        removed = sorted(codes_a - codes_b)
        if added or removed:
            families_changed[family] = {"codes_added": added, "codes_removed": removed}

    variables_added = sorted(vars_b - vars_a)
    variables_removed = sorted(vars_a - vars_b)

    transitions_added = sorted(trans_b - trans_a, key=lambda t: (t[0], t[1]))
    transitions_removed = sorted(trans_a - trans_b, key=lambda t: (t[0], t[1]))

    exclusions_added = sorted(excl_b - excl_a)
    exclusions_removed = sorted(excl_a - excl_b)

    is_identical = not any([
        variables_added,
        variables_removed,
        transitions_added,
        transitions_removed,
        exclusions_added,
        exclusions_removed,
        families_added,
        families_removed,
        families_changed,
    ])

    return {
        "is_identical": is_identical,
        "variables_added": variables_added,
        "variables_removed": variables_removed,
        "transitions_added": [
            {"from": t[0], "to": t[1]} for t in transitions_added
        ],
        "transitions_removed": [
            {"from": t[0], "to": t[1]} for t in transitions_removed
        ],
        "exclusions_added": exclusions_added,
        "exclusions_removed": exclusions_removed,
        "reason_code_families_added": families_added,
        "reason_code_families_removed": families_removed,
        "reason_code_families_changed": families_changed,
    }
