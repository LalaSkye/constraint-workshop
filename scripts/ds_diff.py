#!/usr/bin/env python3
"""ds_diff — Decision-Space Diff CLI.

Usage:
    python scripts/ds_diff.py snapshot_a.json snapshot_b.json

Output:
    Hash A: <sha256>
    Hash B: <sha256>
    <deterministic JSON diff>

Exit codes:
    0  success
    1  validation failure or usage error
"""

import json
import sys
from pathlib import Path

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mgtp.decision_space import diff_snapshots, snapshot_hash, validate_snapshot


def _load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not load {path!r}: {exc}", file=sys.stderr)
        sys.exit(1)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        print("Usage: ds_diff.py snapshot_a.json snapshot_b.json", file=sys.stderr)
        sys.exit(1)

    path_a, path_b = argv

    snapshot_a = _load_json(path_a)
    snapshot_b = _load_json(path_b)

    try:
        validate_snapshot(snapshot_a)
    except ValueError as exc:
        print(f"ERROR: snapshot A validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        validate_snapshot(snapshot_b)
    except ValueError as exc:
        print(f"ERROR: snapshot B validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    hash_a = snapshot_hash(snapshot_a)
    hash_b = snapshot_hash(snapshot_b)

    diff = diff_snapshots(snapshot_a, snapshot_b)

    print(f"Hash A: {hash_a}")
    print(f"Hash B: {hash_b}")
    print(json.dumps(diff, sort_keys=True, indent=2, ensure_ascii=False))

    sys.exit(0)


if __name__ == "__main__":
    main()
