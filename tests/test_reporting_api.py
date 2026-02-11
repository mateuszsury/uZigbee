import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStack:
    def __init__(self):
        self.calls = []

    def configure_reporting(
        self,
        src_endpoint,
        dst_short_addr,
        dst_endpoint,
        cluster_id,
        attr_id,
        attr_type,
        min_interval,
        max_interval,
        reportable_change,
    ):
        self.calls.append(
            (
                src_endpoint,
                dst_short_addr,
                dst_endpoint,
                cluster_id,
                attr_id,
                attr_type,
                min_interval,
                max_interval,
                reportable_change,
            )
        )


def test_reporting_presets_apply_expected_entries():
    reporting = importlib.import_module("uzigbee.reporting")
    core = importlib.import_module("uzigbee.core")
    zcl = importlib.import_module("uzigbee.zcl")

    stack = _FakeStack()
    applied = reporting.configure_thermostat(stack, dst_short_addr=0x1234, src_endpoint=2, dst_endpoint=3)
    assert applied == reporting.PRESET_THERMOSTAT
    assert stack.calls == [
        (2, 0x1234, 3, core.CLUSTER_ID_THERMOSTAT, core.ATTR_THERMOSTAT_LOCAL_TEMPERATURE, zcl.DATA_TYPE_S16, 10, 300, 50),
        (2, 0x1234, 3, core.CLUSTER_ID_THERMOSTAT, core.ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT, zcl.DATA_TYPE_S16, 5, 600, 50),
        (2, 0x1234, 3, core.CLUSTER_ID_THERMOSTAT, core.ATTR_THERMOSTAT_SYSTEM_MODE, zcl.DATA_TYPE_8BIT_ENUM, 1, 3600, 1),
    ]


def test_reporting_contact_and_motion_presets_are_equivalent():
    reporting = importlib.import_module("uzigbee.reporting")
    assert reporting.PRESET_MOTION_SENSOR == reporting.PRESET_CONTACT_SENSOR

    stack = _FakeStack()
    contact = reporting.configure_contact_sensor(stack, dst_short_addr=0x2222)
    motion = reporting.configure_motion_sensor(stack, dst_short_addr=0x3333)

    assert contact == reporting.PRESET_CONTACT_SENSOR
    assert motion == reporting.PRESET_MOTION_SENSOR
    assert len(stack.calls) == 2
    assert stack.calls[0][1] == 0x2222
    assert stack.calls[1][1] == 0x3333


def test_reporting_door_lock_and_occupancy_presets():
    reporting = importlib.import_module("uzigbee.reporting")
    core = importlib.import_module("uzigbee.core")
    zcl = importlib.import_module("uzigbee.zcl")

    stack = _FakeStack()
    reporting.configure_door_lock(stack, dst_short_addr=0x1111)
    reporting.configure_occupancy(stack, dst_short_addr=0x1111)

    assert stack.calls[0][3:9] == (
        core.CLUSTER_ID_DOOR_LOCK,
        core.ATTR_DOOR_LOCK_LOCK_STATE,
        zcl.DATA_TYPE_8BIT_ENUM,
        0,
        3600,
        1,
    )
    assert stack.calls[1][3:9] == (
        core.CLUSTER_ID_OCCUPANCY_SENSING,
        core.ATTR_OCCUPANCY_SENSING_OCCUPANCY,
        zcl.DATA_TYPE_8BITMAP,
        1,
        300,
        1,
    )
