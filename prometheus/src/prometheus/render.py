"""Prometheus render entrypoints.

Orchestrates loading, validation, aggregation, scanning, and reporting.
"""

import json
import os

from prometheus.schemas import validate_diag_events
from prometheus.io_jsonl import read_jsonl, write_json
from prometheus.hashing import list_files_deterministically, sha256_file_bytes
from prometheus.aggregate import compute_window_from_events, summarise
from prometheus.redlines import scan_prometheus_redlines
from prometheus.fit_report import build_fit_report


def _contains_forbidden(obj, forbidden_paths, forbidden_tokens, case_insensitive=True):
    """Check if a serialised event object contains forbidden content.

    Used to compute invalid_with_forbidden_count for classification.
    """
    text = json.dumps(obj, sort_keys=True)
    check = text.lower() if case_insensitive else text
    for fp in forbidden_paths:
        fp_check = fp.lower() if case_insensitive else fp
        if fp_check in check:
            return True
    for ft in forbidden_tokens:
        ft_check = ft.lower() if case_insensitive else ft
        if ft_check in check:
            return True
    return False


def run_from_fixture_set(prometheus_dir, rules):
    """Run Prometheus against fixture JSONL files.

    Does NOT write outputs. Returns (summary, redlines, fit_report) dicts.
    """
    fixtures_dir = os.path.join(prometheus_dir, "fixtures")
    forbidden_paths = rules.get("forbidden_paths", [])
    forbidden_tokens = rules.get("forbidden_tokens", [])
    case_insensitive = rules.get("case_insensitive", True)

    paths = list_files_deterministically(fixtures_dir, suffix=".jsonl")
    input_hash = sha256_file_bytes(paths)

    all_events = []
    for p in paths:
        all_events.extend(read_jsonl(p))

    valid, invalid = validate_diag_events(all_events)

    invalid_with_forbidden = sum(
        1 for obj, _errs in invalid
        if _contains_forbidden(obj, forbidden_paths, forbidden_tokens, case_insensitive)
    )

    window_start, window_end = compute_window_from_events(valid)
    summary = summarise(valid, window_start, window_end, input_hash)

    redlines = scan_prometheus_redlines(prometheus_dir, rules)

    fit = build_fit_report(
        input_hash=input_hash,
        valid_count=len(valid),
        invalid_count=len(invalid),
        redline_finding_count=len(redlines["findings"]),
        invalid_with_forbidden=invalid_with_forbidden,
    )

    return summary, redlines, fit


def run_from_diag_dir(prometheus_dir, rules):
    """Run Prometheus against runtime diag JSONL files.

    Writes outputs to agg/, lint/, reports/ under prometheus_dir.
    Returns (summary, redlines, fit_report) dicts.
    """
    diag_dir = os.path.join(prometheus_dir, "diag")
    forbidden_paths = rules.get("forbidden_paths", [])
    forbidden_tokens = rules.get("forbidden_tokens", [])
    case_insensitive = rules.get("case_insensitive", True)

    paths = list_files_deterministically(diag_dir, suffix=".jsonl")
    input_hash = sha256_file_bytes(paths)

    all_events = []
    for p in paths:
        all_events.extend(read_jsonl(p))

    valid, invalid = validate_diag_events(all_events)

    invalid_with_forbidden = sum(
        1 for obj, _errs in invalid
        if _contains_forbidden(obj, forbidden_paths, forbidden_tokens, case_insensitive)
    )

    window_start, window_end = compute_window_from_events(valid)
    summary = summarise(valid, window_start, window_end, input_hash)

    redlines = scan_prometheus_redlines(prometheus_dir, rules)

    fit = build_fit_report(
        input_hash=input_hash,
        valid_count=len(valid),
        invalid_count=len(invalid),
        redline_finding_count=len(redlines["findings"]),
        invalid_with_forbidden=invalid_with_forbidden,
    )

    write_json(os.path.join(prometheus_dir, "agg", "anomaly_summary.json"), summary)
    write_json(os.path.join(prometheus_dir, "lint", "prometheus_redlines.json"), redlines)
    write_json(os.path.join(prometheus_dir, "reports", "prometheus_fit_report.json"), fit)

    return summary, redlines, fit
