"""Commit Gate Engine — deterministic verdict resolution.

Resolution order:
1. denylist match => REFUSE
2. explicit allowlist match => ALLOW
3. escalation match => ESCALATE
4. default => REFUSE
"""

import json
from pathlib import Path

from .canonicalise import canonical_hash, canonicalise


ARTEFACT_VERSION = "0.1"


def _scope_matches(rule_scope, request_scope):
    """Return True if all keys in rule_scope exist in request_scope with identical values."""
    for key, value in rule_scope.items():
        if request_scope.get(key) != value:
            return False
    return True


def _find_match(rules_list, actor_id, action_class, authority_scope):
    """Return True if any rule in rules_list matches the request."""
    for rule in rules_list:
        if rule.get("actor_id") is not None and rule["actor_id"] != actor_id:
            continue
        if rule.get("action_class") is not None and rule["action_class"] != action_class:
            continue
        scope_match = rule.get("scope_match", {})
        if _scope_matches(scope_match, authority_scope):
            return True
    return False


def load_ruleset(path):
    """Load ruleset JSON from path. Returns dict."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_request_obj(actor_id, action_class, context, authority_scope, invariant_hash):
    """Build the canonical request object (excluding timestamp)."""
    return {
        "actor_id": actor_id,
        "action_class": action_class,
        "context": context,
        "authority_scope": authority_scope,
        "invariant_hash": invariant_hash,
    }


def evaluate(commit_request, ruleset):
    """Evaluate a CommitRequest against a ruleset. Returns CommitVerdict dict.

    commit_request: dict with actor_id, action_class, context, authority_scope,
                    invariant_hash, and optional timestamp_utc.
    ruleset: dict with allowlist, denylist, escalation lists.
    """
    actor_id = commit_request["actor_id"]
    action_class = commit_request["action_class"]
    authority_scope = commit_request["authority_scope"]

    # Build hashable request (no timestamp)
    request_obj = build_request_obj(
        actor_id=actor_id,
        action_class=action_class,
        context=commit_request["context"],
        authority_scope=authority_scope,
        invariant_hash=commit_request["invariant_hash"],
    )
    request_hash = canonical_hash(request_obj)

    # Resolution order: deny -> allow -> escalate -> default REFUSE
    reasons = []

    if _find_match(ruleset.get("denylist", []), actor_id, action_class, authority_scope):
        verdict = "REFUSE"
        reasons.append("denylist_match")
    elif _find_match(ruleset.get("allowlist", []), actor_id, action_class, authority_scope):
        verdict = "ALLOW"
        reasons.append("allowlist_match")
    elif _find_match(ruleset.get("escalation", []), actor_id, action_class, authority_scope):
        verdict = "ESCALATE"
        reasons.append("escalation_match")
    else:
        verdict = "REFUSE"
        reasons.append("default_refuse")

    # Sort reasons lexicographically
    reasons = sorted(reasons)

    # Build decision hash: sha256(canonical_request + verdict + reasons)
    decision_obj = {
        "request": request_obj,
        "verdict": verdict,
        "reasons": reasons,
    }
    decision_hash = canonical_hash(decision_obj)

    return {
        "verdict": verdict,
        "reasons": reasons,
        "decision_hash": decision_hash,
        "request_hash": request_hash,
        "artefact_version": ARTEFACT_VERSION,
    }


def write_decision_report(verdict_dict, request_hash, output_dir):
    """Write decision artefact to reports dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"commit_decision_{request_hash}.json"
    canonical_bytes = canonicalise(verdict_dict)
    path.write_bytes(canonical_bytes)
    return path
