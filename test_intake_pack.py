"""Tests for intake_pack v0.1 — schema, reason-code families, status envelope."""

import pytest

from intake_pack import (
    ENVELOPE_VERSION,
    SCHEMA_VERSION,
    AllowFamily,
    EscalateFamily,
    IntakeRequestSchema,
    IntakeVerdictSchema,
    RefuseFamily,
    StatusEnvelope,
    VERDICT_FAMILY,
)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_schema_version():
    assert SCHEMA_VERSION == "0.1"


def test_intake_request_schema_required_fields():
    assert "actor_id" in IntakeRequestSchema.REQUIRED_FIELDS
    assert "action_class" in IntakeRequestSchema.REQUIRED_FIELDS
    assert "context" in IntakeRequestSchema.REQUIRED_FIELDS
    assert "authority_scope" in IntakeRequestSchema.REQUIRED_FIELDS
    assert "invariant_hash" in IntakeRequestSchema.REQUIRED_FIELDS


def test_intake_request_schema_optional_fields():
    assert "timestamp_utc" in IntakeRequestSchema.OPTIONAL_FIELDS


def test_intake_request_schema_all_fields():
    assert set(IntakeRequestSchema.ALL_FIELDS) == set(
        IntakeRequestSchema.REQUIRED_FIELDS + IntakeRequestSchema.OPTIONAL_FIELDS
    )


def test_intake_verdict_schema_verdict_values():
    assert set(IntakeVerdictSchema.VERDICT_VALUES) == {"ALLOW", "REFUSE", "ESCALATE"}


def test_intake_verdict_schema_required_fields():
    assert "verdict" in IntakeVerdictSchema.REQUIRED_FIELDS
    assert "reasons" in IntakeVerdictSchema.REQUIRED_FIELDS
    assert "decision_hash" in IntakeVerdictSchema.REQUIRED_FIELDS
    assert "request_hash" in IntakeVerdictSchema.REQUIRED_FIELDS
    assert "artefact_version" in IntakeVerdictSchema.REQUIRED_FIELDS


# ---------------------------------------------------------------------------
# Reason-code family tests
# ---------------------------------------------------------------------------


def test_allow_family_values():
    assert AllowFamily.ALLOWLIST_MATCH.value == "allowlist_match"
    assert AllowFamily.EXPLICIT_GRANT.value == "explicit_grant"


def test_refuse_family_values():
    assert RefuseFamily.DENYLIST_MATCH.value == "denylist_match"
    assert RefuseFamily.DEFAULT_REFUSE.value == "default_refuse"
    assert RefuseFamily.MISSING_EVIDENCE.value == "missing_evidence"


def test_escalate_family_values():
    assert EscalateFamily.ESCALATION_MATCH.value == "escalation_match"
    assert EscalateFamily.SCOPE_AMBIGUOUS.value == "scope_ambiguous"


def test_verdict_family_mapping_keys():
    assert set(VERDICT_FAMILY.keys()) == {"ALLOW", "REFUSE", "ESCALATE"}


def test_verdict_family_mapping_types():
    assert VERDICT_FAMILY["ALLOW"] is AllowFamily
    assert VERDICT_FAMILY["REFUSE"] is RefuseFamily
    assert VERDICT_FAMILY["ESCALATE"] is EscalateFamily


def test_engine_reason_codes_are_in_families():
    """Engine-emitted reason codes must exist in the appropriate family."""
    engine_allow = "allowlist_match"
    engine_refuse_denylist = "denylist_match"
    engine_refuse_default = "default_refuse"
    engine_escalate = "escalation_match"

    allow_values = {m.value for m in AllowFamily}
    refuse_values = {m.value for m in RefuseFamily}
    escalate_values = {m.value for m in EscalateFamily}

    assert engine_allow in allow_values
    assert engine_refuse_denylist in refuse_values
    assert engine_refuse_default in refuse_values
    assert engine_escalate in escalate_values


# ---------------------------------------------------------------------------
# Status envelope tests
# ---------------------------------------------------------------------------


def test_envelope_version():
    assert ENVELOPE_VERSION == "0.1"


def test_status_envelope_allow():
    env = StatusEnvelope(
        ok=True,
        status="ALLOW",
        reason_codes=["allowlist_match"],
        payload={"verdict": "ALLOW"},
    )
    assert env.ok is True
    assert env.status == "ALLOW"
    assert env.reason_codes == ["allowlist_match"]
    assert env.payload == {"verdict": "ALLOW"}
    assert env.envelope_version == ENVELOPE_VERSION
    assert env.error is None


def test_status_envelope_refuse():
    env = StatusEnvelope(
        ok=False,
        status="REFUSE",
        reason_codes=["default_refuse"],
        payload=None,
        error="No matching rule found.",
    )
    assert env.ok is False
    assert env.status == "REFUSE"
    assert env.error == "No matching rule found."
    assert env.payload is None


def test_status_envelope_escalate():
    env = StatusEnvelope(
        ok=True,
        status="ESCALATE",
        reason_codes=["escalation_match"],
        payload={"verdict": "ESCALATE"},
    )
    assert env.status == "ESCALATE"
    assert env.reason_codes == ["escalation_match"]


def test_status_envelope_is_immutable():
    """StatusEnvelope is a NamedTuple and therefore immutable."""
    env = StatusEnvelope(
        ok=True,
        status="ALLOW",
        reason_codes=[],
        payload=None,
    )
    with pytest.raises(AttributeError):
        env.ok = False  # type: ignore[misc]


def test_status_envelope_default_version():
    """envelope_version defaults to ENVELOPE_VERSION constant."""
    env = StatusEnvelope(ok=True, status="ALLOW", reason_codes=[], payload=None)
    assert env.envelope_version == "0.1"
