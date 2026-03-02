"""commit_gate CLI — stdlib-only command-line interface.

Usage:
    python -m commit_gate evaluate --request REQUEST.json --ruleset RULESET.json [--output-dir DIR]
    python -m commit_gate drift --baseline BASELINE.json --ruleset RULESET.json --invariant-hash HASH [--current-invariant-hash HASH] [--acknowledge-expansion] [--output-dir DIR]
"""

import argparse
import json
import sys

from .canonicalise import canonicalise
from .drift import build_authority_graph, detect_drift, load_graph, write_authority_graph
from .engine import evaluate, load_ruleset, write_decision_report


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_evaluate(args):
    """Evaluate a commit request against a ruleset."""
    request = _load_json(args.request)
    ruleset = load_ruleset(args.ruleset)
    verdict = evaluate(request, ruleset)

    # Write report
    if args.output_dir:
        write_decision_report(verdict, verdict["request_hash"], args.output_dir)

    # Output canonical JSON to stdout
    sys.stdout.buffer.write(canonicalise(verdict))
    sys.stdout.buffer.write(b"\n")
    return 0 if verdict["verdict"] == "ALLOW" else 1


def cmd_drift(args):
    """Run drift detection between baseline and current ruleset."""
    ruleset = load_ruleset(args.ruleset)
    current_graph = build_authority_graph(ruleset)

    # Write current graph
    if args.output_dir:
        write_authority_graph(current_graph, ruleset, args.output_dir)

    # Load baseline
    baseline_graph = load_graph(args.baseline)

    result = detect_drift(
        baseline_graph=baseline_graph,
        current_graph=current_graph,
        baseline_invariant_hash=args.invariant_hash,
        current_invariant_hash=args.current_invariant_hash or args.invariant_hash,
        acknowledge_expansion=args.acknowledge_expansion,
    )

    sys.stdout.buffer.write(canonicalise(result))
    sys.stdout.buffer.write(b"\n")
    return 0 if result["pass"] else 1


def main():
    parser = argparse.ArgumentParser(prog="commit_gate", description="Deterministic Commit Gate Engine")
    sub = parser.add_subparsers(dest="command")

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Evaluate a commit request")
    p_eval.add_argument("--request", required=True, help="Path to request JSON")
    p_eval.add_argument("--ruleset", required=True, help="Path to ruleset JSON")
    p_eval.add_argument("--output-dir", default=None, help="Directory for report artefacts")

    # drift
    p_drift = sub.add_parser("drift", help="Detect authority drift")
    p_drift.add_argument("--baseline", required=True, help="Path to baseline authority graph JSON")
    p_drift.add_argument("--ruleset", required=True, help="Path to current ruleset JSON")
    p_drift.add_argument("--invariant-hash", required=True, help="Baseline invariant hash")
    p_drift.add_argument("--current-invariant-hash", default=None, help="Current invariant hash (defaults to baseline)")
    p_drift.add_argument("--acknowledge-expansion", action="store_true", help="Acknowledge expansion with contract revision")
    p_drift.add_argument("--output-dir", default=None, help="Directory for graph artefacts")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "evaluate":
        sys.exit(cmd_evaluate(args))
    elif args.command == "drift":
        sys.exit(cmd_drift(args))


if __name__ == "__main__":
    main()
