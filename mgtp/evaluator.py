"""mgtp/evaluator.py — Fail-closed MGTP verdict resolver.

Consumes authority_gate.AuthorityGate; does not redefine it.

Fail-closed rules (non-negotiable):
  1. verdict == ALLOW requires provided_evidence is not None.
  2. decision_time must fall within [request.timestamp, request.timestamp + window].
     Outside that window → REFUSED (fail-closed).
"""

from datetime import datetime, timezone
from typing import Optional

from authority_gate import Decision, Evidence, AuthorityGate

from .types import AuthorityContext, DecisionRecord, TransitionOutcome, TransitionRequest

# Authority window: maximum seconds between request timestamp and decision_time.
AUTHORITY_WINDOW_SECONDS = 3600  # 1 hour; conservative, never relaxed upward here

_ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _parse_utc(ts: str) -> datetime:
    """Parse an ISO-8601 UTC timestamp string to an aware datetime."""
    try:
        return datetime.strptime(ts, _ISO_FMT).replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"Timestamp must be ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ), got: {ts!r}")


def _within_authority_window(request_ts: str, decision_ts: str, window_seconds: int) -> bool:
    """Return True iff decision_ts is within [request_ts, request_ts + window_seconds]."""
    req_dt = _parse_utc(request_ts)
    dec_dt = _parse_utc(decision_ts)
    delta = (dec_dt - req_dt).total_seconds()
    return 0 <= delta <= window_seconds


def evaluate(
    request: TransitionRequest,
    context: AuthorityContext,
    provided_evidence: Optional[Evidence],
    decision_time: str,
    authority_window_seconds: int = AUTHORITY_WINDOW_SECONDS,
) -> DecisionRecord:
    """Evaluate a TransitionRequest and return a DecisionRecord.

    Fail-closed: any uncertainty or missing evidence yields REFUSED.
    """
    # --- Guard: decision_time within authority window ---
    if not _within_authority_window(request.timestamp, decision_time, authority_window_seconds):
        return DecisionRecord(
            transition_id=request.transition_id,
            verdict=TransitionOutcome.REFUSED,
            reasons=("decision_time_outside_authority_window",),
            decision_time=decision_time,
            authority_basis=context.authority_basis,
        )

    # --- Guard: evidence must not be None for any non-REFUSED path ---
    if provided_evidence is None:
        return DecisionRecord(
            transition_id=request.transition_id,
            verdict=TransitionOutcome.REFUSED,
            reasons=("missing_evidence",),
            decision_time=decision_time,
            authority_basis=context.authority_basis,
        )

    # --- Resolve required evidence level from authority_basis ---
    try:
        required = Evidence[context.authority_basis]
    except KeyError:
        return DecisionRecord(
            transition_id=request.transition_id,
            verdict=TransitionOutcome.REFUSED,
            reasons=("unknown_authority_basis",),
            decision_time=decision_time,
            authority_basis=context.authority_basis,
        )

    gate = AuthorityGate(required)
    gate_decision = gate.check(provided_evidence)

    if gate_decision is Decision.DENY:
        return DecisionRecord(
            transition_id=request.transition_id,
            verdict=TransitionOutcome.REFUSED,
            reasons=("insufficient_evidence",),
            decision_time=decision_time,
            authority_basis=context.authority_basis,
        )

    # Evidence is sufficient; apply risk-class supervision rules.
    if request.irreversible or request.trust_boundary_crossed:
        return DecisionRecord(
            transition_id=request.transition_id,
            verdict=TransitionOutcome.SUPERVISED,
            reasons=("irreversible_or_trust_boundary",),
            decision_time=decision_time,
            authority_basis=context.authority_basis,
        )

    return DecisionRecord(
        transition_id=request.transition_id,
        verdict=TransitionOutcome.APPROVED,
        reasons=("evidence_sufficient",),
        decision_time=decision_time,
        authority_basis=context.authority_basis,
    )
