from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / "tools" / "ha_discovery_suite.py"
    spec = importlib.util.spec_from_file_location("ha_discovery_suite", mod_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_run_validation_converter_ok():
    module = _load_module()
    root = Path(__file__).resolve().parents[1]
    converter = root / "z2m_converters" / "uzigbee.js"
    result = module.run_validation(converter)
    assert result["ok"] is True
    assert result["missing_models"] == []
    assert result["missing_domain"] == []
    assert len(result["cases"]) >= 10


def test_parse_converter_has_extends():
    module = _load_module()
    root = Path(__file__).resolve().parents[1]
    text = (root / "z2m_converters" / "uzigbee.js").read_text(encoding="utf-8")
    parsed = module.parse_converter_definitions(text)
    assert parsed
    assert any(entry["model"] == "uzb_Light" for entry in parsed)
    for entry in parsed:
        assert isinstance(entry["extends"], tuple)
