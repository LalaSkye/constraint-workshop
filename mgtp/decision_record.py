"""mgtp.decision_record — Re-exports the canonical DecisionRecord.

The sole DecisionRecord implementation lives in mgtp.types.
This module exists so that ``from mgtp.decision_record import DecisionRecord``
continues to work without introducing a duplicate or competing class.
"""

from mgtp.types import DecisionRecord  # noqa: F401

__all__ = ["DecisionRecord"]
