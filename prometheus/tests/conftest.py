"""Shared fixtures and path setup for Prometheus tests.

Ensures src/ is on sys.path so all test modules can
import from prometheus.* without per-file path hacks.
"""

import os
import sys

import pytest

# Add src/ to the front of sys.path so that
# 'from prometheus.<module> import ...' works in every test file.
_SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")
_PROMETHEUS_DIR = os.path.join(os.path.dirname(__file__), "..")


@pytest.fixture
def fixtures_dir():
    """Return absolute path to prometheus/fixtures/."""
    return os.path.abspath(_FIXTURES_DIR)


@pytest.fixture
def prometheus_dir():
    """Return absolute path to prometheus/."""
    return os.path.abspath(_PROMETHEUS_DIR)
