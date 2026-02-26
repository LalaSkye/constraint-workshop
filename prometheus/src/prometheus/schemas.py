"""Schema validation for DiagEvent and AnomalySummary.

Stdlib only. No third-party dependencies.
Tight schema: unknown keys are errors.
"""

import re

_VALID_SEVERITIES = frozenset({"INFO", "WARN", "ERROR", "CRITICAL"})
_DIAG_EVENT_KEYS = frozenset({"event_type", "ts", "source", "severity", "message", "context"})
_ISO8601_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def validate_diag_event(obj):
    """Validate a single DiagEvent dict.

    Returns (ok: bool, errors: list[str]).
    """
    errors = []
    if not isinstance(obj, dict):
        return False, ["event is not a dict"]

    extra = set(obj.keys()) - _DIAG_EVENT_KEYS
    if extra:
        errors.append(f"unknown keys: {sorted(extra)}")

    for key in ("event_type", "ts", "source", "severity", "message"):
        if key not in obj:
            errors.append(f"missing required key: {key}")

    if "context" not in obj:
        errors.append("missing required key: context")
    elif obj["context"] is not None and not isinstance(obj["context"], dict):
        errors.append("context must be dict or null")

    if "ts" in obj:
        if not isinstance(obj["ts"], str):
            errors.append("ts must be a string")
        elif not _ISO8601_Z_RE.match(obj["ts"]):
            errors.append("ts must be ISO8601 with trailing Z")

    if "severity" in obj:
        if not isinstance(obj["severity"], str):
            errors.append("severity must be a string")
        elif obj["severity"] not in _VALID_SEVERITIES:
            errors.append(f"severity must be one of {sorted(_VALID_SEVERITIES)}")

    for key in ("event_type", "source", "message"):
        if key in obj and not isinstance(obj[key], str):
            errors.append(f"{key} must be a string")

    return (len(errors) == 0, errors)


def validate_diag_events(objs):
    """Validate a list of DiagEvent dicts.

    Returns (valid: list[dict], invalid: list[tuple[dict, list[str]]]).
    """
    valid = []
    invalid = []
    for obj in objs:
        ok, errs = validate_diag_event(obj)
        if ok:
            valid.append(obj)
        else:
            invalid.append((obj, errs))
    return valid, invalid


_ANOMALY_SUMMARY_KEYS = frozenset({
    "window_start", "window_end", "counts_by_type",
    "counts_by_severity", "top_sources", "hash_of_inputs",
})


def validate_anomaly_summary(obj):
    """Validate an AnomalySummary dict.

    Returns (ok: bool, errors: list[str]).
    """
    errors = []
    if not isinstance(obj, dict):
        return False, ["summary is not a dict"]

    extra = set(obj.keys()) - _ANOMALY_SUMMARY_KEYS
    if extra:
        errors.append(f"unknown keys: {sorted(extra)}")

    for key in _ANOMALY_SUMMARY_KEYS:
        if key not in obj:
            errors.append(f"missing required key: {key}")

    for key in ("window_start", "window_end", "hash_of_inputs"):
        if key in obj and not isinstance(obj[key], str):
            errors.append(f"{key} must be a string")

    for key in ("counts_by_type", "counts_by_severity"):
        if key in obj:
            if not isinstance(obj[key], dict):
                errors.append(f"{key} must be a dict")
            else:
                for k, v in obj[key].items():
                    if not isinstance(v, int):
                        errors.append(f"{key}[{k!r}] must be int")

    if "top_sources" in obj:
        if not isinstance(obj["top_sources"], list):
            errors.append("top_sources must be a list")
        else:
            for i, entry in enumerate(obj["top_sources"]):
                if not isinstance(entry, dict):
                    errors.append(f"top_sources[{i}] must be a dict")
                elif set(entry.keys()) != {"source", "count"}:
                    errors.append(f"top_sources[{i}] keys must be source, count")

    return (len(errors) == 0, errors)
