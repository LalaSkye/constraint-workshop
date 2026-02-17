"""stop_machine.py — A deterministic three-state stop machine.

States: GREEN -> AMBER -> RED (terminal).
RED is irreversible. No skipping backwards.
No global state. No time logic. No optimisation.
"""

from enum import Enum, auto


class State(Enum):
    GREEN = auto()
    AMBER = auto()
    RED = auto()


_FORWARD = {
    State.GREEN: State.AMBER,
    State.AMBER: State.RED,
}

_ORDER = {State.GREEN: 0, State.AMBER: 1, State.RED: 2}


class StopMachine:
    """Three-state machine. RED is terminal."""

    def __init__(self) -> None:
        self._state = State.GREEN

    @property
    def state(self) -> State:
        return self._state

    def advance(self) -> None:
        """Move forward one step: GREEN->AMBER->RED."""
        if self._state == State.RED:
            raise ValueError("Cannot advance from RED: terminal state.")
        self._state = _FORWARD[self._state]

    def transition_to(self, target: State) -> None:
        """Jump to *target* if it is strictly ahead of current state."""
        if _ORDER[target] <= _ORDER[self._state]:
            raise ValueError(
                f"Cannot transition from {self._state.name} to {target.name}: "
                "backwards or same-state transitions are forbidden."
            )
        self._state = target

    def reset(self) -> None:
        """Reset to GREEN. Forbidden once RED is reached."""
        if self._state == State.RED:
            raise ValueError("Cannot reset from RED: terminal state.")
        self._state = State.GREEN
