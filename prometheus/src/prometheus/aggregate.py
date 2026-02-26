"""Anomaly aggregation.

Produces deterministic AnomalySummary from validated DiagEvents.
"""

from collections import Counter

_EMPTY_WINDOW = ("1970-01-01T00:00:00Z", "1970-01-01T00:00:00Z")


def compute_window_from_events(events):
    """Return (min_ts, max_ts) from event timestamps.

    Returns deterministic empty window if no events.
    """
    if not events:
        return _EMPTY_WINDOW
    timestamps = [e["ts"] for e in events]
    return (min(timestamps), max(timestamps))


def summarise(events, window_start, window_end, input_hash):
    """Build an AnomalySummary dict from validated events.

    Keys are sorted for deterministic JSON output.
    top_sources is sorted by (count desc, source asc).
    """
    type_counter = Counter(e["event_type"] for e in events)
    severity_counter = Counter(e["severity"] for e in events)
    source_counter = Counter(e["source"] for e in events)

    top_sources = sorted(
        [{"source": src, "count": cnt} for src, cnt in source_counter.items()],
        key=lambda x: (-x["count"], x["source"]),
    )

    return {
        "window_start": window_start,
        "window_end": window_end,
        "counts_by_type": dict(sorted(type_counter.items())),
        "counts_by_severity": dict(sorted(severity_counter.items())),
        "top_sources": top_sources,
        "hash_of_inputs": input_hash,
    }
