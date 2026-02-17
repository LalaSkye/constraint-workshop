"""Tests for stop_machine.py"""

import pytest
from stop_machine import State, StopMachine


def test_initial_state_is_green():
    m = StopMachine()
    assert m.state is State.GREEN


def test_advance_twice_reaches_red():
    m = StopMachine()
    m.advance()  # GREEN -> AMBER
    assert m.state is State.AMBER
    m.advance()  # AMBER -> RED
    assert m.state is State.RED


def test_advance_from_red_raises():
    m = StopMachine()
    m.advance()
    m.advance()
    with pytest.raises(ValueError):
        m.advance()


def test_transition_to_red_from_green():
    m = StopMachine()
    m.transition_to(State.RED)
    assert m.state is State.RED


def test_backward_transition_raises():
    m = StopMachine()
    m.advance()  # -> AMBER
    with pytest.raises(ValueError):
        m.transition_to(State.GREEN)


def test_reset_from_red_raises():
    m = StopMachine()
    m.transition_to(State.RED)
    with pytest.raises(ValueError):
        m.reset()


def test_reset_from_amber_returns_to_green():
    m = StopMachine()
    m.advance()  # -> AMBER
    m.reset()
    assert m.state is State.GREEN


def test_same_state_transition_raises():
    m = StopMachine()
    with pytest.raises(ValueError):
        m.transition_to(State.GREEN)


def test_deterministic_across_runs():
    results = []
    for _ in range(100):
        m = StopMachine()
        m.advance()
        m.advance()
        results.append(m.state)
    assert all(s is State.RED for s in results)
