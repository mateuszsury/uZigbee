import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


def test_cluster_ids_and_legacy_aliases():
    zcl = importlib.import_module("uzigbee.zcl")
    assert zcl.CLUSTER_ID_BASIC == 0x0000
    assert zcl.CLUSTER_ID_ON_OFF == 0x0006
    assert zcl.CLUSTER_ID_LEVEL_CONTROL == 0x0008
    assert zcl.CLUSTER_ID_COLOR_CONTROL == 0x0300
    assert zcl.CLUSTER_ID_TEMP_MEASUREMENT == 0x0402
    assert zcl.CLUSTER_ID_IAS_ZONE == 0x0500
    assert zcl.CLUSTER_ID_ELECTRICAL_MEASUREMENT == 0x0B04
    assert zcl.CLUSTER_BASIC == zcl.CLUSTER_ID_BASIC
    assert zcl.CLUSTER_ON_OFF == zcl.CLUSTER_ID_ON_OFF


def test_basic_and_onoff_attributes_and_legacy_aliases():
    zcl = importlib.import_module("uzigbee.zcl")
    assert zcl.ATTR_BASIC_MANUFACTURER_NAME == 0x0004
    assert zcl.ATTR_BASIC_MODEL_IDENTIFIER == 0x0005
    assert zcl.ATTR_BASIC_SW_BUILD_ID == 0x4000
    assert zcl.ATTR_ON_OFF_ON_OFF == 0x0000
    assert zcl.ATTR_ON_OFF_START_UP_ON_OFF == 0x4003
    assert zcl.ATTR_MANUFACTURER_NAME == zcl.ATTR_BASIC_MANUFACTURER_NAME
    assert zcl.ATTR_MODEL_IDENTIFIER == zcl.ATTR_BASIC_MODEL_IDENTIFIER
    assert zcl.ATTR_SW_BUILD_ID == zcl.ATTR_BASIC_SW_BUILD_ID
    assert zcl.ATTR_ON_OFF == zcl.ATTR_ON_OFF_ON_OFF


def test_data_types_and_helpers():
    zcl = importlib.import_module("uzigbee.zcl")
    assert zcl.DATA_TYPE_BOOL == 0x10
    assert zcl.DATA_TYPE_U16 == 0x21
    assert zcl.DATA_TYPE_S32 == 0x2B
    assert zcl.DATA_TYPE_CHAR_STRING == 0x42
    assert zcl.DATA_TYPE_CLUSTER_ID == 0xE8
    assert zcl.DATA_TYPE_INVALID == 0xFF

    assert zcl.cluster_name(0x0006) == "on_off"
    assert zcl.cluster_name(0x9999) == "unknown"

    assert zcl.data_type_name(zcl.DATA_TYPE_BOOL) == "bool"
    assert zcl.data_type_name(zcl.DATA_TYPE_CHAR_STRING) == "char_string"
    assert zcl.data_type_name(0xAB) == "unknown"

    assert zcl.data_type_size(zcl.DATA_TYPE_BOOL) == 1
    assert zcl.data_type_size(zcl.DATA_TYPE_U16) == 2
    assert zcl.data_type_size(zcl.DATA_TYPE_IEEE_ADDR) == 8
    assert zcl.data_type_size(zcl.DATA_TYPE_CHAR_STRING) is None

    assert zcl.is_string_type(zcl.DATA_TYPE_CHAR_STRING) is True
    assert zcl.is_string_type(zcl.DATA_TYPE_LONG_CHAR_STRING) is True
    assert zcl.is_string_type(zcl.DATA_TYPE_U8) is False
