"""Red-line scanner for Prometheus code.

Scans source files for forbidden paths and tokens.
CRITICAL: Only scans src/**/*.py by default.
Never scans README, fixtures/, or expected/ directories.
"""

import fnmatch
import os


def scan_text_files(root, include_globs):
    """Walk root and return (path, text) pairs matching include_globs.

    Results are sorted lexicographically by path for determinism.
    """
    matched = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            for glob in include_globs:
                if fnmatch.fnmatch(rel, glob):
                    with open(full, "r", encoding="utf-8") as f:
                        matched.append((rel, f.read()))
                    break
    return sorted(matched, key=lambda x: x[0])


def find_forbidden(text, forbidden_paths, forbidden_tokens, case_insensitive=True):
    """Find forbidden paths and tokens in a text string.

    Returns list of RedlineFinding dicts.
    """
    findings = []
    lines = text.splitlines()
    check_text = text.lower() if case_insensitive else text

    for line_num, line in enumerate(lines, start=1):
        check_line = line.lower() if case_insensitive else line
        for fp in forbidden_paths:
            fp_check = fp.lower() if case_insensitive else fp
            if fp_check in check_line:
                findings.append({
                    "path": "",
                    "kind": "FORBIDDEN_PATH",
                    "match": fp,
                    "line": line_num,
                })
        for ft in forbidden_tokens:
            ft_check = ft.lower() if case_insensitive else ft
            if ft_check in check_line:
                findings.append({
                    "path": "",
                    "kind": "FORBIDDEN_TOKEN",
                    "match": ft,
                    "line": line_num,
                })
    return findings


def scan_prometheus_redlines(prometheus_root, rules):
    """Scan Prometheus source code for red-line violations.

    Args:
        prometheus_root: Path to the prometheus/ directory.
        rules: Dict with keys:
            - forbidden_paths: list[str]
            - forbidden_tokens: list[str]
            - case_insensitive: bool (default True)
            - include_globs: list[str] (default ["src/**/*.py"])

    Returns dict with key "findings" containing list of RedlineFinding.
    """
    include_globs = rules.get("include_globs", ["src/**/*.py"])
    forbidden_paths = rules.get("forbidden_paths", [])
    forbidden_tokens = rules.get("forbidden_tokens", [])
    case_insensitive = rules.get("case_insensitive", True)

    files = scan_text_files(prometheus_root, include_globs)
    all_findings = []

    for rel_path, text in files:
        file_findings = find_forbidden(
            text, forbidden_paths, forbidden_tokens, case_insensitive
        )
        for f in file_findings:
            f["path"] = rel_path
        all_findings.extend(file_findings)

    return {"findings": all_findings}
