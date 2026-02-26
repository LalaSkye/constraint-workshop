"""JSONL I/O utilities.

Reads JSONL files and writes deterministic JSON output.
"""

import json
import os


def read_jsonl(path):
    """Read a JSONL file and return a list of dicts."""
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                items.append(json.loads(stripped))
    return items


def write_json(path, obj):
    """Write a dict to a JSON file with deterministic formatting.

    Uses sort_keys=True and indent=2 for byte-stable output.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, indent=2)
        f.write("\n")
