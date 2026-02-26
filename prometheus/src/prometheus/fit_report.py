"""Fit report generation.

Classifies Prometheus health as FIT_CLEAN, FIT_WITH_WARNINGS, or DRIFT_RISK.
"""


def classify(valid_count, invalid_count, redline_finding_count, invalid_with_forbidden):
    """Determine the verdict based on counts.

    Returns one of: FIT_CLEAN, FIT_WITH_WARNINGS, DRIFT_RISK.
    """
    if redline_finding_count > 0 or invalid_with_forbidden > 0:
        return "DRIFT_RISK"
    if invalid_count > 0:
        return "FIT_WITH_WARNINGS"
    return "FIT_CLEAN"


def build_fit_report(input_hash, valid_count, invalid_count,
                     redline_finding_count, invalid_with_forbidden, notes=None):
    """Build a PrometheusFitReport dict.

    All fields are deterministic given the same inputs.
    """
    verdict = classify(
        valid_count, invalid_count,
        redline_finding_count, invalid_with_forbidden,
    )
    return {
        "verdict": verdict,
        "input_hash": input_hash,
        "schema_invalid_count": invalid_count,
        "redline_finding_count": redline_finding_count,
        "invalid_with_forbidden_count": invalid_with_forbidden,
        "notes": notes or [],
    }
