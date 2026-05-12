"""Tests P4-5 — validateur YAML weights + écriture atomique.

Le module `scoring.weights_editor` est utilisé par la page Gouvernance pour
permettre une édition live des pondérations sans redémarrage.
"""

from __future__ import annotations

import pytest

from p2p_fraud.scoring.weights_editor import validate_weights_yaml, write_weights

_VALID_YAML = """
detector_weights:
  duplicates: 1.0
  thresholds: 0.7
  benford: 0.0
  sirene: 1.2
  isolation_forest: 0.8
  graph: 1.5
  master_data: 1.5
  sanctions: 1.6

severity_multiplier:
  low: 0.1
  medium: 0.3
  high: 0.6
  critical: 1.0
"""


def test_validate_accepts_canonical_weights():
    result = validate_weights_yaml(_VALID_YAML)
    assert result.ok is True
    assert result.parsed is not None
    assert result.parsed["detector_weights"]["sanctions"] == 1.6


def test_validate_rejects_invalid_yaml_syntax():
    result = validate_weights_yaml("foo:\n  - bar\n  baz: qux")
    assert result.ok is False
    assert "YAML invalide" in result.message


def test_validate_rejects_non_dict_root():
    result = validate_weights_yaml("- just a list")
    assert result.ok is False


def test_validate_rejects_unknown_detector():
    yaml_bad = _VALID_YAML.replace("sanctions: 1.6", "sanctions: 1.6\n  exotic_detector: 1.0")
    result = validate_weights_yaml(yaml_bad)
    assert result.ok is False
    assert "Détecteur inconnu" in result.message
    assert "exotic_detector" in result.message


def test_validate_rejects_negative_weight():
    yaml_bad = _VALID_YAML.replace("sanctions: 1.6", "sanctions: -0.5")
    result = validate_weights_yaml(yaml_bad)
    assert result.ok is False
    assert "sanctions" in result.message


def test_validate_rejects_non_numeric_weight():
    yaml_bad = _VALID_YAML.replace("duplicates: 1.0", 'duplicates: "high"')
    result = validate_weights_yaml(yaml_bad)
    assert result.ok is False


def test_validate_rejects_missing_severity():
    yaml_bad = _VALID_YAML.replace("low: 0.1", "")
    result = validate_weights_yaml(yaml_bad)
    assert result.ok is False
    assert "severity_multiplier" in result.message


def test_validate_rejects_multiplier_outside_unit_range():
    yaml_bad = _VALID_YAML.replace("critical: 1.0", "critical: 1.5")
    result = validate_weights_yaml(yaml_bad)
    assert result.ok is False


def test_validate_rejects_missing_detector_weights_section():
    result = validate_weights_yaml(
        """
        severity_multiplier:
          low: 0.1
          medium: 0.3
          high: 0.6
          critical: 1.0
        """
    )
    assert result.ok is False
    assert "detector_weights" in result.message


def test_write_weights_persists_valid_yaml(tmp_path):
    target = tmp_path / "weights.yaml"
    result = write_weights(target, _VALID_YAML)
    assert result.ok is True
    assert target.read_text(encoding="utf-8") == _VALID_YAML


def test_write_weights_does_not_persist_invalid(tmp_path):
    target = tmp_path / "weights.yaml"
    target.write_text("PREVIOUS", encoding="utf-8")
    result = write_weights(target, "not: a: valid: yaml: file")
    assert result.ok is False
    # Le fichier n'a PAS été écrasé
    assert target.read_text(encoding="utf-8") == "PREVIOUS"


@pytest.mark.parametrize(
    "broken_field,bad_value",
    [
        ("duplicates: 1.0", "duplicates: null"),
        ("sanctions: 1.6", "sanctions: [1, 2, 3]"),
    ],
)
def test_validate_rejects_various_type_errors(broken_field, bad_value):
    yaml_bad = _VALID_YAML.replace(broken_field, bad_value)
    result = validate_weights_yaml(yaml_bad)
    assert result.ok is False
