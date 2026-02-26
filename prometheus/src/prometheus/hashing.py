"""Deterministic file hashing.

Provides stable, repeatable SHA-256 hashes over ordered file sets.
"""

import hashlib
import os


def list_files_deterministically(dir_path, suffix=".jsonl"):
    """List files in dir_path with given suffix, sorted lexicographically.

    Returns list of absolute paths.
    """
    results = []
    for name in sorted(os.listdir(dir_path)):
        if name.endswith(suffix):
            results.append(os.path.join(dir_path, name))
    return results


def sha256_file_bytes(paths):
    """Compute SHA-256 hex digest over concatenated file bytes.

    Files are read in the order given (caller must sort).
    """
    h = hashlib.sha256()
    for path in paths:
        with open(path, "rb") as f:
            h.update(f.read())
    return h.hexdigest()
