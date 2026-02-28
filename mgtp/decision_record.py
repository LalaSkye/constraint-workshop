"""decision_record — Deterministic, time-bounded, evidenced decision artefact.

Canonical serialisation rules:
- Fixed field order (explicit tuple _CANONICAL_FIELDS).
- Stable JSON: UTF-8, separators=(",", ":"), sort_keys=True.
- Stable list ordering: reason_codes and evidence refs sorted before serialisation.
- decision_hash = sha256(canonical_bytes()) as lowercase hex.

Fail-closed rules (enforced by evaluate()):
- decision_time outside [authority_window_start, authority_window_end]
  => verdict forced to REFUSE, reason_code "outside_authority_window" appended.
- verdict == ALLOW and provided_evidence is None
  => verdict forced to REFUSE, reason_code "evidence_missing" appended.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .types import EvidenceRef, Verdict

_CANONICAL_FIELDS = (
    "record_id",
    "decision_time",
    "authority_window_start",
    "authority_window_end",
    "verdict",
    "reason_codes",
    "provided_evidence",
)

OUTSIDE_WINDOW_REASON = "outside_authority_window"
EVIDENCE_MISSING_REASON = "evidence_missing"


def _parse_rfc3339(ts: str) -> datetime:
    """Parse an RFC3339 / ISO-8601 timestamp string; 'Z' suffix accepted."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@dataclass(frozen=True)
class DecisionRecord:
    """Immutable decision artefact with deterministic serialisation.

    Fields
    ------
    record_id              Unique identifier for this decision.
    decision_time          UTC timestamp of the decision (RFC3339).
    authority_window_start Start of the valid authority window (RFC3339).
    authority_window_end   End of the valid authority window (RFC3339).
    verdict                One of Verdict.{ALLOW, REFUSE, SUPERVISED}.
    reason_codes           Sorted tuple of reason strings.
    provided_evidence      Sorted tuple of EvidenceRef, or None.
    """

    record_id: str
    decision_time: str
    authority_window_start: str
    authority_window_end: str
    verdict: str
    reason_codes: tuple
    provided_evidence: Optional[tuple]

    def canonical_bytes(self) -> bytes:
        """Return deterministic UTF-8 JSON bytes for this record.

        - Keys in sort_keys order (alphabetical).
        - reason_codes sorted.
        - provided_evidence list sorted by ref_id (or None).
        - No whitespace in separators.
        """
        evidence_json: Optional[list] = None
        if self.provided_evidence is not None:
            evidence_json = sorted(
                [{"description": e.description, "ref_id": e.ref_id} for e in self.provided_evidence],
                key=lambda x: x["ref_id"],
            )
        obj = {
            "record_id": self.record_id,
            "decision_time": self.decision_time,
            "authority_window_start": self.authority_window_start,
            "authority_window_end": self.authority_window_end,
            "verdict": self.verdict,
            "reason_codes": sorted(self.reason_codes),
            "provided_evidence": evidence_json,
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    @property
    def decision_hash(self) -> str:
        """SHA-256 hex digest (lowercase) of canonical_bytes()."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def evaluate(
    record_id: str,
    decision_time: str,
    authority_window_start: str,
    authority_window_end: str,
    requested_verdict: str,
    reason_codes: list,
    provided_evidence: Optional[list],
) -> "DecisionRecord":
    """Build a DecisionRecord, applying fail-closed enforcement.

    Enforcement (in order):
    1. If decision_time is outside [authority_window_start, authority_window_end]
       the verdict is forced to REFUSE and OUTSIDE_WINDOW_REASON is appended.
    2. If the resulting verdict is ALLOW and provided_evidence is None
       the verdict is forced to REFUSE and EVIDENCE_MISSING_REASON is appended.

    Parameters
    ----------
    record_id               Unique record identifier.
    decision_time           UTC timestamp of decision (RFC3339).
    authority_window_start  Window start (RFC3339).
    authority_window_end    Window end (RFC3339).
    requested_verdict       Caller-supplied verdict string (Verdict member value).
    reason_codes            List of reason strings.
    provided_evidence       List of EvidenceRef, or None.

    Returns
    -------
    DecisionRecord with final, enforced verdict.
    """
    verdict = requested_verdict
    codes = list(reason_codes)

    dt = _parse_rfc3339(decision_time)
    window_start = _parse_rfc3339(authority_window_start)
    window_end = _parse_rfc3339(authority_window_end)

    if not (window_start <= dt <= window_end):
        verdict = Verdict.REFUSE.value
        if OUTSIDE_WINDOW_REASON not in codes:
            codes.append(OUTSIDE_WINDOW_REASON)

    if verdict == Verdict.ALLOW.value and provided_evidence is None:
        verdict = Verdict.REFUSE.value
        if EVIDENCE_MISSING_REASON not in codes:
            codes.append(EVIDENCE_MISSING_REASON)

    evidence_tuple: Optional[tuple] = None
    if provided_evidence is not None:
        evidence_tuple = tuple(sorted(provided_evidence, key=lambda e: e.ref_id))

    return DecisionRecord(
        record_id=record_id,
        decision_time=decision_time,
        authority_window_start=authority_window_start,
        authority_window_end=authority_window_end,
        verdict=verdict,
        reason_codes=tuple(sorted(codes)),
        provided_evidence=evidence_tuple,
    )
