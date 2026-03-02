"""CLI entry point for the decision_space_ledger.

Usage::

    python -m decision_space_ledger <snapshot_a.json> <snapshot_b.json>

Validates both snapshots, computes their canonical SHA-256 hashes, produces a
structured diff, and writes the result as JSON to stdout.

Exit codes:
    0  — success
    1  — file I/O or validation error
    2  — incorrect usage
"""

import json
import sys

from .canonicalise import canonical_hash
from .diff import diff
from .schema import validate


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print(
            "Usage: python -m decision_space_ledger <snapshot_a.json> <snapshot_b.json>",
            file=sys.stderr,
        )
        return 2

    path_a, path_b = argv[0], argv[1]

    try:
        with open(path_a, encoding="utf-8") as fh:
            snap_a = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading {path_a}: {exc}", file=sys.stderr)
        return 1

    try:
        with open(path_b, encoding="utf-8") as fh:
            snap_b = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading {path_b}: {exc}", file=sys.stderr)
        return 1

    try:
        validate(snap_a)
    except ValueError as exc:
        print(f"Validation error in {path_a}: {exc}", file=sys.stderr)
        return 1

    try:
        validate(snap_b)
    except ValueError as exc:
        print(f"Validation error in {path_b}: {exc}", file=sys.stderr)
        return 1

    result = {
        "snapshot_a": {"path": path_a, "hash": canonical_hash(snap_a)},
        "snapshot_b": {"path": path_b, "hash": canonical_hash(snap_b)},
        "diff": diff(snap_a, snap_b),
    }

    print(json.dumps(result, indent=2))
    return 0
