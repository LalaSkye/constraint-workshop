"""Tests for mgtp.registry — integrity validation of the transition registry."""

import os
import textwrap

import pytest
import yaml

from mgtp.registry import load_registry

_REAL_REGISTRY = os.path.join(
    os.path.dirname(__file__), "..", "registry", "TRANSITION_REGISTRY_v0.2.yaml"
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _write_yaml(tmp_path, content: str) -> str:
    p = tmp_path / "registry.yaml"
    p.write_text(textwrap.dedent(content))
    return str(p)


# ---------------------------------------------------------------------------
# Happy-path: real registry loads cleanly
# ---------------------------------------------------------------------------

def test_real_registry_loads():
    reg = load_registry(_REAL_REGISTRY)
    assert isinstance(reg, dict)
    assert len(reg) >= 1


def test_real_registry_contains_tool_call_http():
    reg = load_registry(_REAL_REGISTRY)
    assert "TOOL_CALL_HTTP" in reg


def test_real_registry_entry_has_required_fields():
    reg = load_registry(_REAL_REGISTRY)
    entry = reg["TOOL_CALL_HTTP"]
    for field in ("id", "irreversible", "risk_class", "required_authority", "gate_version"):
        assert field in entry


# ---------------------------------------------------------------------------
# Version field required
# ---------------------------------------------------------------------------

def test_missing_version_raises(tmp_path):
    path = _write_yaml(tmp_path, """
        transitions:
          - id: T1
            irreversible: false
            risk_class: LOW
            required_authority: USER
            gate_version: v0.1
    """)
    with pytest.raises(ValueError, match="version"):
        load_registry(path)


# ---------------------------------------------------------------------------
# Duplicate IDs rejected
# ---------------------------------------------------------------------------

def test_duplicate_id_raises(tmp_path):
    path = _write_yaml(tmp_path, """
        version: 0.2
        transitions:
          - id: T1
            irreversible: false
            risk_class: LOW
            required_authority: USER
            gate_version: v0.1
          - id: T1
            irreversible: true
            risk_class: HIGH
            required_authority: ADMIN
            gate_version: v0.1
    """)
    with pytest.raises(ValueError, match="Duplicate"):
        load_registry(path)


# ---------------------------------------------------------------------------
# Missing required fields rejected
# ---------------------------------------------------------------------------

def test_missing_risk_class_raises(tmp_path):
    path = _write_yaml(tmp_path, """
        version: 0.2
        transitions:
          - id: T1
            irreversible: false
            required_authority: USER
            gate_version: v0.1
    """)
    with pytest.raises(ValueError, match="risk_class"):
        load_registry(path)


def test_missing_required_authority_raises(tmp_path):
    path = _write_yaml(tmp_path, """
        version: 0.2
        transitions:
          - id: T1
            irreversible: false
            risk_class: LOW
            gate_version: v0.1
    """)
    with pytest.raises(ValueError, match="required_authority"):
        load_registry(path)


# ---------------------------------------------------------------------------
# Invalid enum values rejected
# ---------------------------------------------------------------------------

def test_invalid_risk_class_raises(tmp_path):
    path = _write_yaml(tmp_path, """
        version: 0.2
        transitions:
          - id: T1
            irreversible: false
            risk_class: EXTREME
            required_authority: USER
            gate_version: v0.1
    """)
    with pytest.raises(ValueError, match="risk_class"):
        load_registry(path)


def test_invalid_required_authority_raises(tmp_path):
    path = _write_yaml(tmp_path, """
        version: 0.2
        transitions:
          - id: T1
            irreversible: false
            risk_class: LOW
            required_authority: SUPERUSER
            gate_version: v0.1
    """)
    with pytest.raises(ValueError, match="required_authority"):
        load_registry(path)


@pytest.mark.parametrize("ra", ["NONE", "USER", "OWNER", "ADMIN"])
def test_all_valid_required_authority_values_accepted(tmp_path, ra):
    path = _write_yaml(tmp_path, f"""
        version: 0.2
        transitions:
          - id: T1
            irreversible: false
            risk_class: LOW
            required_authority: {ra}
            gate_version: v0.1
    """)
    reg = load_registry(path)
    assert "T1" in reg


@pytest.mark.parametrize("rc", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
def test_all_valid_risk_class_values_accepted(tmp_path, rc):
    path = _write_yaml(tmp_path, f"""
        version: 0.2
        transitions:
          - id: T1
            irreversible: false
            risk_class: {rc}
            required_authority: USER
            gate_version: v0.1
    """)
    reg = load_registry(path)
    assert "T1" in reg
