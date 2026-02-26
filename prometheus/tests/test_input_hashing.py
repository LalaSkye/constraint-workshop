"""Tests for deterministic input hashing."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prometheus.hashing import list_files_deterministically, sha256_file_bytes

_FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def test_sha256_stable_across_runs():
    paths = list_files_deterministically(_FIXTURES, suffix=".jsonl")
    h1 = sha256_file_bytes(paths)
    h2 = sha256_file_bytes(paths)
    assert h1 == h2
    assert len(h1) == 64  # hex sha256


def test_file_list_is_sorted():
    paths = list_files_deterministically(_FIXTURES, suffix=".jsonl")
    basenames = [os.path.basename(p) for p in paths]
    assert basenames == sorted(basenames)


def test_file_list_contains_all_fixtures():
    paths = list_files_deterministically(_FIXTURES, suffix=".jsonl")
    basenames = [os.path.basename(p) for p in paths]
    assert "normal_events.jsonl" in basenames
    assert "bad_events_schema.jsonl" in basenames
    assert "bad_events_tokens.jsonl" in basenames
    assert "bad_events_paths.jsonl" in basenames
