"""Tests for authority_gate primitive."""

import pytest
from authority_gate import Evidence, Decision, AuthorityGate


# --- Construction ---

def test_gate_stores_required_level():
    gate = AuthorityGate(Evidence.OWNER)
    assert gate.required_level is Evidence.OWNER


def test_gate_rejects_non_evidence_required():
    with pytest.raises(TypeError):
        AuthorityGate(2)


# --- ALLOW cases ---

def test_exact_match_allows():
    gate = AuthorityGate(Evidence.USER)
    assert gate.check(Evidence.USER) is Decision.ALLOW


def test_higher_than_required_allows():
    gate = AuthorityGate(Evidence.USER)
    assert gate.check(Evidence.ADMIN) is Decision.ALLOW


def test_admin_always_passes_any_gate():
    for level in Evidence:
        gate = AuthorityGate(level)
        assert gate.check(Evidence.ADMIN) is Decision.ALLOW


# --- DENY cases ---

def test_none_denied_by_user_gate():
    gate = AuthorityGate(Evidence.USER)
    assert gate.check(Evidence.NONE) is Decision.DENY


def test_user_denied_by_admin_gate():
    gate = AuthorityGate(Evidence.ADMIN)
    assert gate.check(Evidence.USER) is Decision.DENY


def test_owner_denied_by_admin_gate():
    gate = AuthorityGate(Evidence.ADMIN)
    assert gate.check(Evidence.OWNER) is Decision.DENY


# --- Edge cases ---

def test_none_gate_allows_everything():
    gate = AuthorityGate(Evidence.NONE)
    for level in Evidence:
        assert gate.check(level) is Decision.ALLOW


def test_check_rejects_non_evidence_provided():
    gate = AuthorityGate(Evidence.USER)
    with pytest.raises(TypeError):
        gate.check(1)


# --- Determinism ---

def test_deterministic_across_calls():
    gate = AuthorityGate(Evidence.OWNER)
    results = [gate.check(Evidence.USER) for _ in range(100)]
    assert all(r is Decision.DENY for r in results)


# --- Evidence ordering ---

def test_evidence_ordering_is_total():
    levels = list(Evidence)
    for i in range(len(levels) - 1):
        assert levels[i] < levels[i + 1]
