"""Deterministic canonicalisation and SHA-256 hashing for decision_space_snapshot_v1.

Canonicalisation rules:
- ``variables``       — sorted lexicographically.
- ``allowed_transitions`` — sorted by (from, to).
- ``exclusions``      — sorted lexicographically.
- ``reason_code_families`` — each code list sorted lexicographically;
  the families object itself uses sorted keys (via json.dumps sort_keys=True).
- Final JSON: sort_keys=True, no whitespace, UTF-8 encoded.

The hash is SHA-256 of the canonical bytes, returned as a lowercase hex string
(64 characters).
"""

import hashlib
import json


def canonicalise(snapshot):
    """Return canonical JSON bytes of a validated snapshot.

    All order-independent arrays are sorted before serialisation so that
    logically equivalent snapshots produce byte-identical output regardless
    of insertion order.
    """
    canonical = {
        "version": snapshot["version"],
        "variables": sorted(snapshot["variables"]),
        "allowed_transitions": sorted(
            snapshot["allowed_transitions"],
            key=lambda t: (t["from"], t["to"]),
        ),
        "exclusions": sorted(snapshot["exclusions"]),
        "reason_code_families": {
            family: sorted(codes)
            for family, codes in snapshot["reason_code_families"].items()
        },
    }
    return json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_hash(snapshot):
    """Return SHA-256 hex digest (lowercase, 64 chars) of the canonical snapshot."""
    return hashlib.sha256(canonicalise(snapshot)).hexdigest()
