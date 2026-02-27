"""Authority graph builder and drift detector.

Builds an adjacency-list graph from a ruleset and detects
reachability expansion between baseline and current graphs.
"""

import json
from pathlib import Path

from .canonicalise import canonical_hash, canonicalise


def build_authority_graph(ruleset):
    """Build authority graph (adjacency list) from ruleset.

    Graph structure:
        {actor_id: [action_class, ...], ...}

    Only allowlist entries produce edges (permitted actions).
    Denylist and escalation do not grant reachable actions.
    """
    graph = {}
    for entry in ruleset.get("allowlist", []):
        actor = entry.get("actor_id", "*")
        action = entry.get("action_class", "*")
        if actor not in graph:
            graph[actor] = []
        if action not in graph[actor]:
            graph[actor].append(action)
    # Sort edges for determinism
    for actor in graph:
        graph[actor] = sorted(graph[actor])
    return graph


def write_authority_graph(graph, ruleset, output_dir):
    """Write authority graph artefact to output dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ruleset_hash = canonical_hash(ruleset)
    artefact = {
        "authority_graph": graph,
        "ruleset_hash": ruleset_hash,
        "artefact_version": "0.1",
    }
    path = output_dir / f"authority_graph_{ruleset_hash}.json"
    path.write_bytes(canonicalise(artefact))
    return path


def _edges_set(graph):
    """Return set of (actor, action) tuples from graph."""
    edges = set()
    for actor, actions in graph.items():
        for action in actions:
            edges.add((actor, action))
    return edges


def detect_drift(baseline_graph, current_graph, baseline_invariant_hash,
                 current_invariant_hash, acknowledge_expansion=False):
    """Compare baseline vs current authority graph.

    Returns dict with:
        pass: bool
        added_edges: list of (actor, action)
        removed_edges: list of (actor, action)
        reason: str
    """
    baseline_edges = _edges_set(baseline_graph)
    current_edges = _edges_set(current_graph)

    added = sorted(current_edges - baseline_edges)
    removed = sorted(baseline_edges - current_edges)

    # No new edges => always PASS
    if not added:
        return {
            "pass": True,
            "added_edges": [],
            "removed_edges": [list(e) for e in removed],
            "reason": "no_expansion",
        }

    # New edges exist
    if baseline_invariant_hash == current_invariant_hash:
        # Invariant hash unchanged => FAIL (reachability expansion)
        return {
            "pass": False,
            "added_edges": [list(e) for e in added],
            "removed_edges": [list(e) for e in removed],
            "reason": "reachability_expansion_without_contract_revision",
        }

    # Invariant hash changed => expansion allowed only with acknowledgement
    if acknowledge_expansion:
        return {
            "pass": True,
            "added_edges": [list(e) for e in added],
            "removed_edges": [list(e) for e in removed],
            "reason": "expansion_acknowledged_with_contract_revision",
        }

    return {
        "pass": False,
        "added_edges": [list(e) for e in added],
        "removed_edges": [list(e) for e in removed],
        "reason": "expansion_with_contract_revision_but_not_acknowledged",
    }


def load_graph(path):
    """Load authority graph JSON from file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("authority_graph", data)
