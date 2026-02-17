"""Tests for invariant_litmus primitive."""

import pytest
from invariant_litmus import classify, Posture, LitmusResult


# --- Hard invariant detections (score >= 0.5) ---

def test_landauer_principle():
    r = classify("Landauer principle defines a fundamental limit independent of hardware")
    assert r.posture is Posture.HARD_INVARIANT
    assert r.score >= 0.5


def test_shannon_limit():
    r = classify("Shannon limit provides an upper bound of 1.4 bits per Hz")
    assert r.posture is Posture.HARD_INVARIANT
    assert r.score >= 0.5


def test_energy_per_bit():
    text = "Energy per bit cannot fall below kT ln(2)"
    r = classify(text)
    assert r.posture is Posture.HARD_INVARIANT


# --- Cost curve detections (score < 0) ---

def test_gpu_optimisation():
    r = classify("Current GPU implementation can be optimised with better scheduling")
    assert r.posture is Posture.COST_CURVE
    assert r.score < 0


def test_throughput_scaling():
    r = classify("This architecture's throughput can be improved by scaling")
    assert r.posture is Posture.COST_CURVE


def test_chip_upgrades():
    r = classify("Present hardware admits mitigation through chip upgrades")
    assert r.posture is Posture.COST_CURVE


# --- Negation handling ---

def test_negation_prevents_false_hard():
    r = classify("This is not optimised for production use")
    # "not" before "optimised" should prevent cost signal
    assert r.posture is Posture.EDGE


# --- Edge cases ---

def test_empty_string_is_edge():
    r = classify("")
    assert r.posture is Posture.EDGE
    assert r.score == 0.0
    assert r.signals == []


def test_neutral_text_is_edge():
    r = classify("The weather is nice today.")
    assert r.posture is Posture.EDGE


def test_non_string_raises():
    with pytest.raises(TypeError):
        classify(42)


# --- Result structure ---

def test_result_is_litmus_result():
    r = classify("fundamental limit")
    assert isinstance(r, LitmusResult)
    assert hasattr(r, "posture")
    assert hasattr(r, "score")
    assert hasattr(r, "signals")


def test_signals_contain_tuples():
    r = classify("Shannon limit is a fundamental limit")
    assert len(r.signals) >= 2
    for sig in r.signals:
        assert isinstance(sig, tuple)
        assert len(sig) == 2


# --- Determinism ---

def test_deterministic_across_calls():
    text = "Energy per bit cannot fall below kT ln(2)"
    results = [classify(text) for _ in range(100)]
    assert all(r == results[0] for r in results)
