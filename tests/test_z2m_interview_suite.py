import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
TOOLS_DIR = ROOT / "tools"

for p in (PYTHON_DIR, TOOLS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import uzigbee.devices as devices  # noqa: E402
import z2m_interview_suite as suite  # noqa: E402


def _expected_models():
    class_names = (
        "Light",
        "DimmableLight",
        "ColorLight",
        "Switch",
        "DimmableSwitch",
        "PowerOutlet",
        "TemperatureSensor",
        "HumiditySensor",
        "PressureSensor",
        "ClimateSensor",
        "DoorLock",
        "DoorLockController",
        "Thermostat",
        "OccupancySensor",
        "IASZone",
        "ContactSensor",
        "MotionSensor",
        "WindowCovering",
    )
    return {getattr(devices, name).Z2M_MODEL_ID for name in class_names}


def test_interview_suite_matrix_matches_all_predefined_models():
    matrix_models = {c.model for c in suite.DEVICE_CASES}
    assert matrix_models == _expected_models()


def test_interview_suite_matrix_has_unique_entries_and_required_flags():
    names = [c.name for c in suite.DEVICE_CASES]
    models = [c.model for c in suite.DEVICE_CASES]
    assert len(names) == len(set(names))
    assert len(models) == len(set(models))
    assert all(c.dashboard_expose for c in suite.DEVICE_CASES)
    assert all(c.read_attr_ok for c in suite.DEVICE_CASES)
    assert all(c.reports_ok for c in suite.DEVICE_CASES)


def test_interview_suite_hil_files_exist():
    assert suite.validate_test_files(ROOT) == []


def test_interview_suite_converter_coverage_complete():
    converter = ROOT / "z2m_converters/uzigbee.js"
    assert suite.validate_converter_coverage(converter) == []


def test_interview_suite_test_list_contains_mandatory_basics():
    tests = suite.build_hil_test_list()
    assert "tests/hil_basic_identity_smoke.py" in tests
    assert "tests/hil_z2m_validate_smoke.py" in tests
    assert "tests/hil_z2m_setters_smoke.py" in tests
    assert "tests/hil_zigbee_bridge_addr_smoke.py" in tests
    assert "tests/hil_ias_zone_smoke.py" in tests
