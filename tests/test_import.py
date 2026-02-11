import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


def test_import():
    uzigbee = importlib.import_module("uzigbee")
    assert uzigbee.ROLE_COORDINATOR == 0
    assert uzigbee.zcl.CLUSTER_BASIC == 0x0000
    assert hasattr(uzigbee, "Light")
    assert hasattr(uzigbee, "DimmableLight")
    assert hasattr(uzigbee, "ColorLight")
    assert hasattr(uzigbee, "Switch")
    assert hasattr(uzigbee, "DimmableSwitch")
    assert hasattr(uzigbee, "DoorLock")
    assert hasattr(uzigbee, "DoorLockController")
    assert hasattr(uzigbee, "WindowCovering")
    assert hasattr(uzigbee, "TemperatureSensor")
    assert hasattr(uzigbee, "HumiditySensor")
    assert hasattr(uzigbee, "PressureSensor")
    assert hasattr(uzigbee, "ClimateSensor")
    assert hasattr(uzigbee, "PowerOutlet")
    assert hasattr(uzigbee, "Thermostat")
    assert hasattr(uzigbee, "OccupancySensor")
    assert hasattr(uzigbee, "IASZone")
    assert hasattr(uzigbee, "ContactSensor")
    assert hasattr(uzigbee, "MotionSensor")
    assert hasattr(uzigbee, "groups")
    assert hasattr(uzigbee, "scenes")
    assert hasattr(uzigbee, "reporting")
    assert hasattr(uzigbee, "security")
    assert hasattr(uzigbee, "custom")
    assert hasattr(uzigbee, "ota")
    assert hasattr(uzigbee, "greenpower")
    assert hasattr(uzigbee, "touchlink")
    assert hasattr(uzigbee, "ncp")
    assert hasattr(uzigbee, "network")
    assert hasattr(uzigbee, "node")
    assert hasattr(uzigbee, "Coordinator")
    assert hasattr(uzigbee, "DeviceRegistry")
    assert hasattr(uzigbee, "DiscoveredDevice")
    assert hasattr(uzigbee, "GreenPowerManager")
    assert hasattr(uzigbee, "TouchlinkManager")
    assert hasattr(uzigbee, "NcpRcpManager")
    assert hasattr(uzigbee, "Router")
    assert hasattr(uzigbee, "EndDevice")
    assert uzigbee.CLUSTER_ID_GROUPS == 0x0004
    assert uzigbee.CLUSTER_ID_SCENES == 0x0005
    assert uzigbee.CLUSTER_ID_OTA_UPGRADE == 0x0019
    assert uzigbee.CLUSTER_ID_DOOR_LOCK == 0x0101
    assert uzigbee.CLUSTER_ID_WINDOW_COVERING == 0x0102
    assert uzigbee.CLUSTER_ID_THERMOSTAT == 0x0201
    assert uzigbee.CLUSTER_ID_OCCUPANCY_SENSING == 0x0406
    assert uzigbee.CLUSTER_ID_IAS_ZONE == 0x0500
    assert uzigbee.CLUSTER_ID_COLOR_CONTROL == 0x0300
    assert uzigbee.CLUSTER_ID_TEMP_MEASUREMENT == 0x0402
    assert uzigbee.CLUSTER_ID_PRESSURE_MEASUREMENT == 0x0403
    assert uzigbee.CLUSTER_ID_REL_HUMIDITY_MEASUREMENT == 0x0405
    assert uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT == 0x0B04
    assert uzigbee.ATTR_COLOR_CONTROL_COLOR_TEMPERATURE == 0x0007
    assert uzigbee.ATTR_DOOR_LOCK_LOCK_STATE == 0x0000
    assert uzigbee.ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE == 0x0008
    assert uzigbee.ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE == 0x0009
    assert uzigbee.ATTR_THERMOSTAT_LOCAL_TEMPERATURE == 0x0000
    assert uzigbee.ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT == 0x0012
    assert uzigbee.ATTR_THERMOSTAT_SYSTEM_MODE == 0x001C
    assert uzigbee.ATTR_OCCUPANCY_SENSING_OCCUPANCY == 0x0000
    assert uzigbee.ATTR_IAS_ZONE_STATUS == 0x0002
    assert uzigbee.ATTR_IAS_ZONE_TYPE == 0x0001
    assert uzigbee.ATTR_TEMP_MEASUREMENT_VALUE == 0x0000
    assert uzigbee.ATTR_PRESSURE_MEASUREMENT_VALUE == 0x0000
    assert uzigbee.ATTR_REL_HUMIDITY_MEASUREMENT_VALUE == 0x0000
    assert uzigbee.ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER == 0x050B
    assert uzigbee.ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE == 0x0505
    assert uzigbee.ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT == 0x0508
    assert uzigbee.CMD_ON_OFF_TOGGLE == 0x02
    assert uzigbee.CMD_SCENES_ADD == 0x00
    assert uzigbee.CMD_SCENES_REMOVE == 0x02
    assert uzigbee.CMD_SCENES_REMOVE_ALL == 0x03
    assert uzigbee.CMD_SCENES_RECALL == 0x05
    assert uzigbee.IC_TYPE_48 == 0x00
    assert uzigbee.IC_TYPE_64 == 0x01
    assert uzigbee.IC_TYPE_96 == 0x02
    assert uzigbee.IC_TYPE_128 == 0x03
    assert uzigbee.CMD_DOOR_LOCK_LOCK_DOOR == 0x00
    assert uzigbee.CMD_DOOR_LOCK_UNLOCK_DOOR == 0x01
    assert uzigbee.CMD_WINDOW_COVERING_UP_OPEN == 0x00
    assert uzigbee.CMD_WINDOW_COVERING_DOWN_CLOSE == 0x01
    assert uzigbee.CMD_WINDOW_COVERING_STOP == 0x02
    assert uzigbee.CMD_WINDOW_COVERING_GO_TO_LIFT_PERCENTAGE == 0x05
    assert uzigbee.CMD_LEVEL_MOVE_TO_LEVEL_WITH_ONOFF == 0x04
    assert uzigbee.IAS_ZONE_TYPE_MOTION == 0x000D
    assert uzigbee.IAS_ZONE_TYPE_CONTACT_SWITCH == 0x0015
    assert uzigbee.CUSTOM_CLUSTER_ID_MIN == 0xFC00
    assert uzigbee.ATTR_ACCESS_READ_ONLY == 0x01
    assert uzigbee.ATTR_ACCESS_WRITE_ONLY == 0x02
    assert uzigbee.ATTR_ACCESS_READ_WRITE == 0x03
    assert uzigbee.ATTR_ACCESS_REPORTING == 0x04
    assert uzigbee.ATTR_ACCESS_SCENE == 0x10
    assert uzigbee.CMD_DIRECTION_TO_SERVER == 0x00
    assert uzigbee.CMD_DIRECTION_TO_CLIENT == 0x01
    assert uzigbee.SIGNAL_PANID_CONFLICT_DETECTED == 0x31
