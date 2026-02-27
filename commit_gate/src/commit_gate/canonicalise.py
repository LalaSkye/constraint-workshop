"""Canonical JSON serialisation for deterministic hashing.

Rules:
- UTF-8 encoding
- Sorted keys (recursive)
- No whitespace
- Stable list ordering (preserved as-is; lists must be pre-sorted by caller)
- sha256 hex lower-case
"""

import hashlib
import json


def canonicalise(obj):
    """Return canonical JSON bytes for the given object.

    Keys sorted recursively, no whitespace, UTF-8.
    Lists are preserved in caller-provided order.
    """
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_hash(obj):
    """Return sha256 hex digest (lower-case) of canonical JSON."""
    return hashlib.sha256(canonicalise(obj)).hexdigest()
