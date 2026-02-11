import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeUZigbee:
    def __init__(self):
        self.calls = []
        self.on_signal = self.set_signal_callback
        self.on_attribute = self.set_attribute_callback
        self.SIGNAL_STEERING = 0x0A
        self.CLUSTER_ROLE_SERVER = 1
        self.CLUSTER_ID_BASIC = 0x0000
        self.CLUSTER_ID_GROUPS = 0x0004
        self.CLUSTER_ID_ON_OFF = 0x0006
        self.CLUSTER_ID_LEVEL_CONTROL = 0x0008
        self.CLUSTER_ID_OTA_UPGRADE = 0x0019
        self.CLUSTER_ID_COLOR_CONTROL = 0x0300
        self.CLUSTER_ID_DOOR_LOCK = 0x0101
        self.CLUSTER_ID_WINDOW_COVERING = 0x0102
        self.CLUSTER_ID_THERMOSTAT = 0x0201
        self.CLUSTER_ID_TEMP_MEASUREMENT = 0x0402
        self.CLUSTER_ID_PRESSURE_MEASUREMENT = 0x0403
        self.CLUSTER_ID_REL_HUMIDITY_MEASUREMENT = 0x0405
        self.CLUSTER_ID_OCCUPANCY_SENSING = 0x0406
        self.CLUSTER_ID_IAS_ZONE = 0x0500
        self.CLUSTER_ID_ELECTRICAL_MEASUREMENT = 0x0B04
        self.ATTR_BASIC_POWER_SOURCE = 0x0007
        self.ATTR_ON_OFF_ON_OFF = 0x0000
        self.ATTR_LEVEL_CONTROL_CURRENT_LEVEL = 0x0000
        self.ATTR_DOOR_LOCK_LOCK_STATE = 0x0000
        self.ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE = 0x0008
        self.ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE = 0x0009
        self.ATTR_THERMOSTAT_LOCAL_TEMPERATURE = 0x0000
        self.ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT = 0x0012
        self.ATTR_THERMOSTAT_SYSTEM_MODE = 0x001C
        self.ATTR_TEMP_MEASUREMENT_VALUE = 0x0000
        self.ATTR_PRESSURE_MEASUREMENT_VALUE = 0x0000
        self.ATTR_REL_HUMIDITY_MEASUREMENT_VALUE = 0x0000
        self.ATTR_OCCUPANCY_SENSING_OCCUPANCY = 0x0000
        self.ATTR_IAS_ZONE_STATE = 0x0000
        self.ATTR_IAS_ZONE_TYPE = 0x0001
        self.ATTR_IAS_ZONE_STATUS = 0x0002
        self.ATTR_IAS_ZONE_IAS_CIE_ADDRESS = 0x0010
        self.ATTR_IAS_ZONE_ID = 0x0011
        self.ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE = 0x0505
        self.ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT = 0x0508
        self.ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER = 0x050B
        self.ATTR_COLOR_CONTROL_CURRENT_X = 0x0003
        self.ATTR_COLOR_CONTROL_CURRENT_Y = 0x0004
        self.ATTR_COLOR_CONTROL_COLOR_TEMPERATURE = 0x0007
        self.CMD_ON_OFF_OFF = 0x00
        self.CMD_ON_OFF_ON = 0x01
        self.CMD_ON_OFF_TOGGLE = 0x02
        self.CMD_DOOR_LOCK_LOCK_DOOR = 0x00
        self.CMD_DOOR_LOCK_UNLOCK_DOOR = 0x01
        self.CMD_WINDOW_COVERING_UP_OPEN = 0x00
        self.CMD_WINDOW_COVERING_DOWN_CLOSE = 0x01
        self.CMD_WINDOW_COVERING_STOP = 0x02
        self.CMD_WINDOW_COVERING_GO_TO_LIFT_PERCENTAGE = 0x05
        self.DEVICE_ID_ON_OFF_SWITCH = 0x0000
        self.DEVICE_ID_LEVEL_CONTROL_SWITCH = 0x0001
        self.DEVICE_ID_DIMMER_SWITCH = 0x0104
        self.DEVICE_ID_SIMPLE_SENSOR = 0x000C
        self.DEVICE_ID_HUMIDITY_SENSOR = 0x000C
        self.DEVICE_ID_PRESSURE_SENSOR = 0x000C
        self.DEVICE_ID_CLIMATE_SENSOR = 0x000C
        self.DEVICE_ID_MAINS_POWER_OUTLET = 0x0009
        self.DEVICE_ID_SMART_PLUG = 0x0051
        self.DEVICE_ID_DOOR_LOCK = 0x000A
        self.DEVICE_ID_DOOR_LOCK_CONTROLLER = 0x000B
        self.DEVICE_ID_WINDOW_COVERING = 0x0202
        self.DEVICE_ID_THERMOSTAT = 0x0301
        self.DEVICE_ID_OCCUPANCY_SENSOR = 0x000C
        self.DEVICE_ID_IAS_ZONE = 0x0402
        self.DEVICE_ID_CONTACT_SENSOR = 0x0402
        self.DEVICE_ID_MOTION_SENSOR = 0x0402
        self.DEVICE_ID_TEMPERATURE_SENSOR = 0x0302
        self.CMD_LEVEL_MOVE_TO_LEVEL = 0x00
        self.CMD_LEVEL_MOVE_TO_LEVEL_WITH_ONOFF = 0x04
        self.IAS_ZONE_TYPE_MOTION = 0x000D
        self.IAS_ZONE_TYPE_CONTACT_SWITCH = 0x0015
        self.IAS_ZONE_STATUS_ALARM1 = 0x0001
        self.IAS_ZONE_STATUS_ALARM2 = 0x0002
        self.IAS_ZONE_STATUS_TAMPER = 0x0004
        self.IAS_ZONE_STATUS_BATTERY = 0x0008
        self.CUSTOM_CLUSTER_ID_MIN = 0xFC00
        self.ATTR_ACCESS_READ_ONLY = 0x01
        self.ATTR_ACCESS_WRITE_ONLY = 0x02
        self.ATTR_ACCESS_READ_WRITE = 0x03
        self.ATTR_ACCESS_REPORTING = 0x04
        self.ATTR_ACCESS_SCENE = 0x10
        self.CMD_DIRECTION_TO_SERVER = 0x00
        self.CMD_DIRECTION_TO_CLIENT = 0x01
        self.BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE = 0x01
        self.DEVICE_ID_DIMMABLE_LIGHT = 0x0101
        self.DEVICE_ID_COLOR_DIMMABLE_LIGHT = 0x0102

    def init(self, role):
        self.calls.append(("init", role))
        return None

    def start(self, form_network):
        self.calls.append(("start", form_network))
        return None

    def create_endpoint(self, endpoint, device_id, profile_id):
        self.calls.append(("create_endpoint", endpoint, device_id, profile_id))
        return None

    def create_on_off_light(self, endpoint):
        self.calls.append(("create_on_off_light", endpoint))
        return None

    def create_on_off_switch(self, endpoint):
        self.calls.append(("create_on_off_switch", endpoint))
        return None

    def create_dimmable_switch(self, endpoint):
        self.calls.append(("create_dimmable_switch", endpoint))
        return None

    def create_dimmable_light(self, endpoint):
        self.calls.append(("create_dimmable_light", endpoint))
        return None

    def create_color_light(self, endpoint):
        self.calls.append(("create_color_light", endpoint))
        return None

    def create_temperature_sensor(self, endpoint):
        self.calls.append(("create_temperature_sensor", endpoint))
        return None

    def create_humidity_sensor(self, endpoint):
        self.calls.append(("create_humidity_sensor", endpoint))
        return None

    def create_pressure_sensor(self, endpoint):
        self.calls.append(("create_pressure_sensor", endpoint))
        return None

    def create_climate_sensor(self, endpoint):
        self.calls.append(("create_climate_sensor", endpoint))
        return None

    def create_power_outlet(self, endpoint, with_metering=False):
        self.calls.append(("create_power_outlet", endpoint, with_metering))
        return None

    def create_door_lock(self, endpoint):
        self.calls.append(("create_door_lock", endpoint))
        return None

    def create_door_lock_controller(self, endpoint):
        self.calls.append(("create_door_lock_controller", endpoint))
        return None

    def create_thermostat(self, endpoint):
        self.calls.append(("create_thermostat", endpoint))
        return None

    def create_occupancy_sensor(self, endpoint):
        self.calls.append(("create_occupancy_sensor", endpoint))
        return None

    def create_window_covering(self, endpoint):
        self.calls.append(("create_window_covering", endpoint))
        return None

    def create_ias_zone(self, endpoint, zone_type):
        self.calls.append(("create_ias_zone", endpoint, zone_type))
        return None

    def create_contact_sensor(self, endpoint):
        self.calls.append(("create_contact_sensor", endpoint))
        return None

    def create_motion_sensor(self, endpoint):
        self.calls.append(("create_motion_sensor", endpoint))
        return None

    def clear_custom_clusters(self):
        self.calls.append(("clear_custom_clusters",))
        return None

    def add_custom_cluster(self, cluster_id, cluster_role):
        self.calls.append(("add_custom_cluster", cluster_id, cluster_role))
        return None

    def add_custom_attr(self, cluster_id, attr_id, attr_type, attr_access, initial_value):
        self.calls.append(("add_custom_attr", cluster_id, attr_id, attr_type, attr_access, initial_value))
        return None

    def register_device(self):
        self.calls.append(("register_device",))
        return None

    def set_basic_identity(self, endpoint, manufacturer, model, date_code, sw_build_id, power_source):
        self.calls.append(("set_basic_identity", endpoint, manufacturer, model, date_code, sw_build_id, power_source))
        return None

    def get_attribute(self, endpoint, cluster_id, attr_id, cluster_role):
        self.calls.append(("get_attribute", endpoint, cluster_id, attr_id, cluster_role))
        return True

    def get_basic_identity(self, endpoint):
        self.calls.append(("get_basic_identity", endpoint))
        return ("uzigbee", "uzb_light_01", "20260206", "1.0.0", 1)

    def set_attribute(self, endpoint, cluster_id, attr_id, value, cluster_role, check):
        self.calls.append(("set_attribute", endpoint, cluster_id, attr_id, value, cluster_role, check))
        return None

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
                "configure_reporting",
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
        return None

    def send_on_off_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, cmd_id):
        self.calls.append(("send_on_off_cmd", src_endpoint, dst_short_addr, dst_endpoint, cmd_id))
        return None

    def send_level_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, level, transition_ds, with_onoff):
        self.calls.append(("send_level_cmd", src_endpoint, dst_short_addr, dst_endpoint, level, transition_ds, with_onoff))
        return None

    def send_lock_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, lock):
        self.calls.append(("send_lock_cmd", src_endpoint, dst_short_addr, dst_endpoint, lock))
        return None

    def send_group_add_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, group_id):
        self.calls.append(("send_group_add_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))
        return None

    def send_group_remove_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, group_id):
        self.calls.append(("send_group_remove_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))
        return None

    def send_group_remove_all_cmd(self, src_endpoint, dst_short_addr, dst_endpoint):
        self.calls.append(("send_group_remove_all_cmd", src_endpoint, dst_short_addr, dst_endpoint))
        return None

    def send_custom_cmd(
        self,
        src_endpoint,
        dst_short_addr,
        dst_endpoint,
        profile_id,
        cluster_id,
        custom_cmd_id,
        direction,
        disable_default_resp,
        manuf_specific,
        manuf_code,
        data_type,
        payload,
    ):
        self.calls.append(
            (
                "send_custom_cmd",
                src_endpoint,
                dst_short_addr,
                dst_endpoint,
                profile_id,
                cluster_id,
                custom_cmd_id,
                direction,
                disable_default_resp,
                manuf_specific,
                manuf_code,
                data_type,
                payload,
            )
        )
        return None

    def ota_client_query_interval_set(self, endpoint, interval_min):
        self.calls.append(("ota_client_query_interval_set", endpoint, interval_min))
        return None

    def ota_client_query_image_req(self, server_ep, server_addr):
        self.calls.append(("ota_client_query_image_req", server_ep, server_addr))
        return None

    def ota_client_query_image_stop(self):
        self.calls.append(("ota_client_query_image_stop",))
        return None

    def ota_client_control_supported(self):
        self.calls.append(("ota_client_control_supported",))
        return False

    def send_bind_cmd(self, src_ieee_addr, src_endpoint, cluster_id, dst_ieee_addr, dst_endpoint, req_dst_short_addr):
        self.calls.append(("send_bind_cmd", src_ieee_addr, src_endpoint, cluster_id, dst_ieee_addr, dst_endpoint, req_dst_short_addr))
        return None

    def send_unbind_cmd(self, src_ieee_addr, src_endpoint, cluster_id, dst_ieee_addr, dst_endpoint, req_dst_short_addr):
        self.calls.append(("send_unbind_cmd", src_ieee_addr, src_endpoint, cluster_id, dst_ieee_addr, dst_endpoint, req_dst_short_addr))
        return None

    def request_binding_table(self, dst_short_addr, start_index):
        self.calls.append(("request_binding_table", dst_short_addr, start_index))
        return None

    def get_binding_table_snapshot(self):
        self.calls.append(("get_binding_table_snapshot",))
        return (
            0,
            0,
            1,
            1,
            (
                (
                    b"\x01\x02\x03\x04\x05\x06\x07\x08",
                    1,
                    0x0006,
                    3,
                    None,
                    b"\x11\x12\x13\x14\x15\x16\x17\x18",
                    1,
                ),
            ),
        )

    def request_active_endpoints(self, dst_short_addr):
        self.calls.append(("request_active_endpoints", dst_short_addr))
        return None

    def get_active_endpoints_snapshot(self):
        self.calls.append(("get_active_endpoints_snapshot",))
        return (0, 2, (1, 242))

    def request_node_descriptor(self, dst_short_addr):
        self.calls.append(("request_node_descriptor", dst_short_addr))
        return None

    def get_node_descriptor_snapshot(self):
        self.calls.append(("get_node_descriptor_snapshot",))
        return (
            0,
            0x1234,
            (
                0x0042,
                0x8E,
                0x1234,
                82,
                128,
                0x1122,
                128,
                0x01,
            ),
        )

    def request_simple_descriptor(self, dst_short_addr, endpoint):
        self.calls.append(("request_simple_descriptor", dst_short_addr, endpoint))
        return None

    def get_simple_descriptor_snapshot(self):
        self.calls.append(("get_simple_descriptor_snapshot",))
        return (
            0,
            0x1234,
            (
                1,
                0x0104,
                0x0100,
                0,
                (0x0000, 0x0003, 0x0004, 0x0005, 0x0006),
                (0x0019,),
            ),
        )

    def request_power_descriptor(self, dst_short_addr):
        self.calls.append(("request_power_descriptor", dst_short_addr))
        return None

    def get_power_descriptor_snapshot(self):
        self.calls.append(("get_power_descriptor_snapshot",))
        return (
            0,
            0x1234,
            (
                0,
                0x01,
                0x01,
                0x0C,
            ),
        )

    def permit_join(self, duration_s):
        self.calls.append(("permit_join", duration_s))
        return None

    def set_primary_channel_mask(self, channel_mask):
        self.calls.append(("set_primary_channel_mask", int(channel_mask)))
        return None

    def set_pan_id(self, pan_id):
        self.calls.append(("set_pan_id", int(pan_id)))
        return None

    def set_extended_pan_id(self, ext_pan_id):
        self.calls.append(("set_extended_pan_id", bytes(ext_pan_id)))
        return None

    def enable_wifi_i154_coex(self):
        self.calls.append(("enable_wifi_i154_coex",))
        return None

    def start_network_steering(self):
        self.calls.append(("start_network_steering",))
        return None

    def get_short_addr(self):
        self.calls.append(("get_short_addr",))
        return 0x1234

    def get_last_joined_short_addr(self):
        self.calls.append(("get_last_joined_short_addr",))
        return 0x2345

    def get_ieee_addr(self):
        self.calls.append(("get_ieee_addr",))
        return b"\x01\x02\x03\x04\x05\x06\x07\x08"

    def get_network_runtime(self):
        self.calls.append(("get_network_runtime",))
        return (15, 0x1A62, b"\x00\x12\x4b\x00\x01\xc6\xc6\xc6", 0x1234, True, True)

    def set_signal_callback(self, callback):
        self.calls.append(("set_signal_callback", callback))
        return None

    def set_attribute_callback(self, callback):
        self.calls.append(("set_attribute_callback", callback))
        return None

    def get_event_stats(self):
        return (7, 1, 0, 6, 2, 1)

    def get_heap_stats(self):
        self.calls.append(("get_heap_stats",))
        return (123456, 120000, 110000, 123000)


def test_core_wrapper_calls():
    core = importlib.import_module("uzigbee.core")
    fake = _FakeUZigbee()
    core._uzigbee = fake

    stack = core.ZigbeeStack()
    stack.init(0)
    stack.create_on_off_light(1)
    stack.create_on_off_switch(5)
    stack.create_dimmable_switch(6)
    stack.create_dimmable_light(2)
    stack.create_color_light(3)
    stack.create_temperature_sensor(4)
    stack.create_humidity_sensor(5)
    stack.create_pressure_sensor(6)
    stack.create_climate_sensor(7)
    stack.create_power_outlet(8, with_metering=True)
    stack.create_door_lock(9)
    stack.create_door_lock_controller(10)
    stack.create_thermostat(11)
    stack.create_occupancy_sensor(12)
    stack.create_window_covering(13)
    stack.create_ias_zone(14, core.IAS_ZONE_TYPE_CONTACT_SWITCH)
    stack.create_contact_sensor(15)
    stack.create_motion_sensor(16)
    stack.set_basic_identity(
        endpoint_id=1,
        manufacturer="uzigbee",
        model="uzb_light_01",
        date_code="20260206",
        sw_build_id="1.0.0",
        power_source=core.BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    )
    stack.create_endpoint(1, core.DEVICE_ID_ON_OFF_LIGHT, core.PROFILE_ID_ZHA)
    stack.register_device()
    attr_before = stack.get_attribute(1, core.CLUSTER_ID_ON_OFF, core.ATTR_ON_OFF_ON_OFF, core.CLUSTER_ROLE_SERVER)
    basic = stack.get_basic_identity(1)
    stack.set_attribute(1, core.CLUSTER_ID_ON_OFF, core.ATTR_ON_OFF_ON_OFF, False, core.CLUSTER_ROLE_SERVER, False)
    stack.configure_reporting(
        dst_short_addr=0x1234,
        cluster_id=core.CLUSTER_ID_TEMP_MEASUREMENT,
        attr_id=core.ATTR_TEMP_MEASUREMENT_VALUE,
        attr_type=0x29,
        src_endpoint=1,
        dst_endpoint=1,
        min_interval=10,
        max_interval=300,
        reportable_change=50,
    )
    stack.send_on_off_cmd(dst_short_addr=0x1234, dst_endpoint=1, src_endpoint=5, cmd_id=core.CMD_ON_OFF_TOGGLE)
    stack.send_level_cmd(dst_short_addr=0x1234, level=180, dst_endpoint=1, src_endpoint=6, transition_ds=5, with_onoff=True)
    stack.send_lock_cmd(dst_short_addr=0x1234, lock=True, dst_endpoint=1, src_endpoint=10)
    stack.send_lock_cmd(dst_short_addr=0x1234, lock=False, dst_endpoint=1, src_endpoint=10)
    stack.send_group_add_cmd(dst_short_addr=0x1234, dst_endpoint=1, src_endpoint=7, group_id=0x3344)
    stack.send_group_remove_cmd(dst_short_addr=0x1234, dst_endpoint=1, src_endpoint=7, group_id=0x3344)
    stack.send_group_remove_all_cmd(dst_short_addr=0x1234, dst_endpoint=1, src_endpoint=7)
    stack.send_bind_cmd(
        src_ieee_addr=b"\x01\x02\x03\x04\x05\x06\x07\x08",
        cluster_id=core.CLUSTER_ID_ON_OFF,
        dst_ieee_addr=b"\x11\x12\x13\x14\x15\x16\x17\x18",
        req_dst_short_addr=0x1234,
        src_endpoint=1,
        dst_endpoint=1,
    )
    stack.send_unbind_cmd(
        src_ieee_addr=b"\x01\x02\x03\x04\x05\x06\x07\x08",
        cluster_id=core.CLUSTER_ID_ON_OFF,
        dst_ieee_addr=b"\x11\x12\x13\x14\x15\x16\x17\x18",
        req_dst_short_addr=0x1234,
        src_endpoint=1,
        dst_endpoint=1,
    )
    stack.request_binding_table(0x1234, start_index=0)
    binding_snapshot = stack.get_binding_table_snapshot()
    stack.request_active_endpoints(0x1234)
    active_ep_snapshot = stack.get_active_endpoints_snapshot()
    stack.request_node_descriptor(0x1234)
    node_desc_snapshot = stack.get_node_descriptor_snapshot()
    stack.request_simple_descriptor(0x1234, 1)
    simple_desc_snapshot = stack.get_simple_descriptor_snapshot()
    stack.request_power_descriptor(0x1234)
    power_desc_snapshot = stack.get_power_descriptor_snapshot()
    stack.start(True)
    stack.permit_join(12)
    short_addr = stack.get_short_addr()
    last_joined_short = stack.get_last_joined_short_addr()
    ieee_addr = stack.get_ieee_addr()
    runtime = stack.get_network_runtime()
    stack.set_signal_callback(None)
    stack.on_signal(None)
    stack.set_attribute_callback(None)
    stack.on_attribute(None)
    stats = stack.event_stats()
    heap = stack.heap_stats()

    assert fake.calls == [
        ("init", 0),
        ("create_on_off_light", 1),
        ("create_on_off_switch", 5),
        ("create_dimmable_switch", 6),
        ("create_dimmable_light", 2),
        ("create_color_light", 3),
        ("create_temperature_sensor", 4),
        ("create_humidity_sensor", 5),
        ("create_pressure_sensor", 6),
        ("create_climate_sensor", 7),
        ("create_power_outlet", 8, True),
        ("create_door_lock", 9),
        ("create_door_lock_controller", 10),
        ("create_thermostat", 11),
        ("create_occupancy_sensor", 12),
        ("create_window_covering", 13),
        ("create_ias_zone", 14, 0x0015),
        ("create_contact_sensor", 15),
        ("create_motion_sensor", 16),
        ("set_basic_identity", 1, "uzigbee", "uzb_light_01", "20260206", "1.0.0", 1),
        ("create_endpoint", 1, 0x0100, 0x0104),
        ("register_device",),
        ("get_attribute", 1, 0x0006, 0x0000, 1),
        ("get_basic_identity", 1),
        ("set_attribute", 1, 0x0006, 0x0000, False, 1, False),
        ("configure_reporting", 1, 0x1234, 1, 0x0402, 0x0000, 0x29, 10, 300, 50),
        ("send_on_off_cmd", 5, 0x1234, 1, 0x02),
        ("send_level_cmd", 6, 0x1234, 1, 180, 5, True),
        ("send_lock_cmd", 10, 0x1234, 1, True),
        ("send_lock_cmd", 10, 0x1234, 1, False),
        ("send_group_add_cmd", 7, 0x1234, 1, 0x3344),
        ("send_group_remove_cmd", 7, 0x1234, 1, 0x3344),
        ("send_group_remove_all_cmd", 7, 0x1234, 1),
        ("send_bind_cmd", b"\x01\x02\x03\x04\x05\x06\x07\x08", 1, 0x0006, b"\x11\x12\x13\x14\x15\x16\x17\x18", 1, 0x1234),
        ("send_unbind_cmd", b"\x01\x02\x03\x04\x05\x06\x07\x08", 1, 0x0006, b"\x11\x12\x13\x14\x15\x16\x17\x18", 1, 0x1234),
        ("request_binding_table", 0x1234, 0),
        ("get_binding_table_snapshot",),
        ("request_active_endpoints", 0x1234),
        ("get_active_endpoints_snapshot",),
        ("request_node_descriptor", 0x1234),
        ("get_node_descriptor_snapshot",),
        ("request_simple_descriptor", 0x1234, 1),
        ("get_simple_descriptor_snapshot",),
        ("request_power_descriptor", 0x1234),
        ("get_power_descriptor_snapshot",),
        ("start", True),
        ("permit_join", 12),
        ("get_short_addr",),
        ("get_last_joined_short_addr",),
        ("get_ieee_addr",),
        ("get_network_runtime",),
        ("set_signal_callback", None),
        ("set_signal_callback", None),
        ("set_attribute_callback", None),
        ("set_attribute_callback", None),
        ("get_heap_stats",),
    ]
    assert short_addr == 0x1234
    assert last_joined_short == 0x2345
    assert ieee_addr == b"\x01\x02\x03\x04\x05\x06\x07\x08"
    assert runtime["channel"] == 15
    assert runtime["pan_id"] == 0x1A62
    assert runtime["extended_pan_id"] == b"\x00\x12\x4b\x00\x01\xc6\xc6\xc6"
    assert runtime["extended_pan_id_hex"] == "00124b0001c6c6c6"
    assert runtime["short_addr"] == 0x1234
    assert runtime["formed"] is True
    assert runtime["joined"] is True
    assert attr_before is True
    assert basic["manufacturer_name"] == "uzigbee"
    assert basic["model_identifier"] == "uzb_light_01"
    assert basic["power_source"] == 1
    assert binding_snapshot["status"] == 0
    assert binding_snapshot["count"] == 1
    assert len(binding_snapshot["records"]) == 1
    assert binding_snapshot["records"][0]["cluster_id"] == 0x0006
    assert active_ep_snapshot["status"] == 0
    assert active_ep_snapshot["count"] == 2
    assert active_ep_snapshot["endpoints"] == [1, 242]
    assert node_desc_snapshot["status"] == 0
    assert node_desc_snapshot["addr"] == 0x1234
    assert node_desc_snapshot["node_desc"]["manufacturer_code"] == 0x1234
    assert node_desc_snapshot["node_desc"]["mac_capability_flags"] == 0x8E
    assert simple_desc_snapshot["status"] == 0
    assert simple_desc_snapshot["addr"] == 0x1234
    assert simple_desc_snapshot["simple_desc"]["endpoint"] == 1
    assert simple_desc_snapshot["simple_desc"]["profile_id"] == 0x0104
    assert simple_desc_snapshot["simple_desc"]["device_id"] == 0x0100
    assert simple_desc_snapshot["simple_desc"]["input_clusters"] == [0x0000, 0x0003, 0x0004, 0x0005, 0x0006]
    assert simple_desc_snapshot["simple_desc"]["output_clusters"] == [0x0019]
    assert power_desc_snapshot["status"] == 0
    assert power_desc_snapshot["addr"] == 0x1234
    assert power_desc_snapshot["power_desc"]["current_power_mode"] == 0
    assert power_desc_snapshot["power_desc"]["available_power_sources"] == 0x01
    assert power_desc_snapshot["power_desc"]["current_power_source"] == 0x01
    assert power_desc_snapshot["power_desc"]["current_power_source_level"] == 0x0C
    assert stats["enqueued"] == 7
    assert stats["dropped_queue_full"] == 1
    assert stats["dispatched"] == 6
    assert heap["free_8bit"] == 123456
    assert heap["min_free_8bit"] == 120000
    assert heap["largest_free_8bit"] == 110000
    assert heap["free_internal"] == 123000


def test_signal_name_helpers():
    core = importlib.import_module("uzigbee.core")
    fake = _FakeUZigbee()
    core._uzigbee = fake

    assert core.signal_name(core.SIGNAL_STEERING) == "steering"
    assert core.signal_name(0x7FFF) == "unknown"


def test_configure_reporting_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoReporting:
        pass

    core._uzigbee = _NoReporting()
    with pytest.raises(core.ZigbeeError, match="configure_reporting not available in firmware"):
        core.ZigbeeStack().configure_reporting(
            dst_short_addr=0x1234,
            cluster_id=0x0402,
            attr_id=0x0000,
            attr_type=0x29,
        )


def test_group_command_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoGroupCommands:
        pass

    core._uzigbee = _NoGroupCommands()
    with pytest.raises(core.ZigbeeError, match="send_group_add_cmd not available in firmware"):
        core.ZigbeeStack().send_group_add_cmd(
            dst_short_addr=0x1234,
            dst_endpoint=1,
            src_endpoint=1,
            group_id=0x0101,
        )


def test_bind_command_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoBind:
        pass

    core._uzigbee = _NoBind()
    with pytest.raises(core.ZigbeeError, match="send_bind_cmd not available in firmware"):
        core.ZigbeeStack().send_bind_cmd(
            src_ieee_addr=b"\x01\x02\x03\x04\x05\x06\x07\x08",
            cluster_id=core.CLUSTER_ID_ON_OFF,
            dst_ieee_addr=b"\x11\x12\x13\x14\x15\x16\x17\x18",
            req_dst_short_addr=0x1234,
        )


def test_binding_table_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoBindTable:
        pass

    core._uzigbee = _NoBindTable()
    with pytest.raises(core.ZigbeeError, match="request_binding_table not available in firmware"):
        core.ZigbeeStack().request_binding_table(0x1234)
    with pytest.raises(core.ZigbeeError, match="get_binding_table_snapshot not available in firmware"):
        core.ZigbeeStack().get_binding_table_snapshot()


def test_active_endpoints_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoActiveEp:
        pass

    core._uzigbee = _NoActiveEp()
    with pytest.raises(core.ZigbeeError, match="request_active_endpoints not available in firmware"):
        core.ZigbeeStack().request_active_endpoints(0x1234)
    with pytest.raises(core.ZigbeeError, match="get_active_endpoints_snapshot not available in firmware"):
        core.ZigbeeStack().get_active_endpoints_snapshot()


def test_node_descriptor_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoNodeDesc:
        pass

    core._uzigbee = _NoNodeDesc()
    with pytest.raises(core.ZigbeeError, match="request_node_descriptor not available in firmware"):
        core.ZigbeeStack().request_node_descriptor(0x1234)
    with pytest.raises(core.ZigbeeError, match="get_node_descriptor_snapshot not available in firmware"):
        core.ZigbeeStack().get_node_descriptor_snapshot()


def test_simple_descriptor_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoSimpleDesc:
        pass

    core._uzigbee = _NoSimpleDesc()
    with pytest.raises(core.ZigbeeError, match="request_simple_descriptor not available in firmware"):
        core.ZigbeeStack().request_simple_descriptor(0x1234, 1)
    with pytest.raises(core.ZigbeeError, match="get_simple_descriptor_snapshot not available in firmware"):
        core.ZigbeeStack().get_simple_descriptor_snapshot()


def test_power_descriptor_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoPowerDesc:
        pass

    core._uzigbee = _NoPowerDesc()
    with pytest.raises(core.ZigbeeError, match="request_power_descriptor not available in firmware"):
        core.ZigbeeStack().request_power_descriptor(0x1234)
    with pytest.raises(core.ZigbeeError, match="get_power_descriptor_snapshot not available in firmware"):
        core.ZigbeeStack().get_power_descriptor_snapshot()


def test_scene_command_wrappers():
    core = importlib.import_module("uzigbee.core")

    class _SceneOnly:
        def __init__(self):
            self.calls = []

        def send_scene_add_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id, transition_ds):
            self.calls.append(("send_scene_add_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id, transition_ds))

        def send_scene_remove_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id):
            self.calls.append(("send_scene_remove_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id))

        def send_scene_remove_all_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, group_id):
            self.calls.append(("send_scene_remove_all_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))

        def send_scene_recall_cmd(self, src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id):
            self.calls.append(("send_scene_recall_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id))

    fake = _SceneOnly()
    core._uzigbee = fake
    stack = core.ZigbeeStack()

    stack.send_scene_add_cmd(dst_short_addr=0x1234, group_id=0x1111, scene_id=0x22, dst_endpoint=2, src_endpoint=3, transition_ds=15)
    stack.send_scene_remove_cmd(dst_short_addr=0x1234, group_id=0x1111, scene_id=0x22, dst_endpoint=2, src_endpoint=3)
    stack.send_scene_remove_all_cmd(dst_short_addr=0x1234, group_id=0x1111, dst_endpoint=2, src_endpoint=3)
    stack.send_scene_recall_cmd(dst_short_addr=0x1234, group_id=0x1111, scene_id=0x22, dst_endpoint=2, src_endpoint=3)

    assert fake.calls == [
        ("send_scene_add_cmd", 3, 0x1234, 2, 0x1111, 0x22, 15),
        ("send_scene_remove_cmd", 3, 0x1234, 2, 0x1111, 0x22),
        ("send_scene_remove_all_cmd", 3, 0x1234, 2, 0x1111),
        ("send_scene_recall_cmd", 3, 0x1234, 2, 0x1111, 0x22),
    ]


def test_scene_command_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoScenes:
        pass

    core._uzigbee = _NoScenes()
    with pytest.raises(core.ZigbeeError, match="send_scene_add_cmd not available in firmware"):
        core.ZigbeeStack().send_scene_add_cmd(0x1234, 0x1111, 0x22)
    with pytest.raises(core.ZigbeeError, match="send_scene_remove_cmd not available in firmware"):
        core.ZigbeeStack().send_scene_remove_cmd(0x1234, 0x1111, 0x22)
    with pytest.raises(core.ZigbeeError, match="send_scene_remove_all_cmd not available in firmware"):
        core.ZigbeeStack().send_scene_remove_all_cmd(0x1234, 0x1111)
    with pytest.raises(core.ZigbeeError, match="send_scene_recall_cmd not available in firmware"):
        core.ZigbeeStack().send_scene_recall_cmd(0x1234, 0x1111, 0x22)


def test_security_wrappers():
    core = importlib.import_module("uzigbee.core")

    class _SecurityOnly:
        def __init__(self):
            self.calls = []

        def set_install_code_policy(self, enabled):
            self.calls.append(("set_install_code_policy", bool(enabled)))

        def get_install_code_policy(self):
            self.calls.append(("get_install_code_policy",))
            return True

        def set_network_security_enabled(self, enabled):
            self.calls.append(("set_network_security_enabled", bool(enabled)))

        def is_network_security_enabled(self):
            self.calls.append(("is_network_security_enabled",))
            return True

        def set_network_key(self, key):
            self.calls.append(("set_network_key", bytes(key)))

        def get_primary_network_key(self):
            self.calls.append(("get_primary_network_key",))
            return b"\x00" * 16

        def switch_network_key(self, key, key_seq_num):
            self.calls.append(("switch_network_key", bytes(key), int(key_seq_num)))

        def broadcast_network_key(self, key, key_seq_num):
            self.calls.append(("broadcast_network_key", bytes(key), int(key_seq_num)))

        def broadcast_network_key_switch(self, key_seq_num):
            self.calls.append(("broadcast_network_key_switch", int(key_seq_num)))

        def add_install_code(self, ieee_addr, ic_str):
            self.calls.append(("add_install_code", bytes(ieee_addr), str(ic_str)))

        def set_local_install_code(self, ic_str):
            self.calls.append(("set_local_install_code", str(ic_str)))

        def remove_install_code(self, ieee_addr):
            self.calls.append(("remove_install_code", bytes(ieee_addr)))

        def remove_all_install_codes(self):
            self.calls.append(("remove_all_install_codes",))

    fake = _SecurityOnly()
    core._uzigbee = fake
    stack = core.ZigbeeStack()
    key = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
    ieee = b"\x11\x22\x33\x44\x55\x66\x77\x88"
    ic_str = "83FED3407A939723A5C639B26916D5054195"

    stack.set_install_code_policy(True)
    assert stack.get_install_code_policy() is True
    stack.set_network_security_enabled(True)
    assert stack.is_network_security_enabled() is True
    stack.set_network_key(key)
    assert stack.get_primary_network_key() == b"\x00" * 16
    stack.switch_network_key(key, 3)
    stack.broadcast_network_key(key, 4)
    stack.broadcast_network_key_switch(4)
    stack.add_install_code(ieee, ic_str)
    stack.set_local_install_code(ic_str)
    stack.remove_install_code(ieee)
    stack.remove_all_install_codes()

    assert fake.calls == [
        ("set_install_code_policy", True),
        ("get_install_code_policy",),
        ("set_network_security_enabled", True),
        ("is_network_security_enabled",),
        ("set_network_key", key),
        ("get_primary_network_key",),
        ("switch_network_key", key, 3),
        ("broadcast_network_key", key, 4),
        ("broadcast_network_key_switch", 4),
        ("add_install_code", ieee, ic_str),
        ("set_local_install_code", ic_str),
        ("remove_install_code", ieee),
        ("remove_all_install_codes",),
    ]


def test_security_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoSecurity:
        pass

    core._uzigbee = _NoSecurity()
    stack = core.ZigbeeStack()
    key = b"\x01" * 16
    ieee = b"\x11\x22\x33\x44\x55\x66\x77\x88"

    with pytest.raises(core.ZigbeeError, match="set_install_code_policy not available in firmware"):
        stack.set_install_code_policy(True)
    with pytest.raises(core.ZigbeeError, match="get_install_code_policy not available in firmware"):
        stack.get_install_code_policy()
    with pytest.raises(core.ZigbeeError, match="set_network_security_enabled not available in firmware"):
        stack.set_network_security_enabled(True)
    with pytest.raises(core.ZigbeeError, match="is_network_security_enabled not available in firmware"):
        stack.is_network_security_enabled()
    with pytest.raises(core.ZigbeeError, match="set_network_key not available in firmware"):
        stack.set_network_key(key)
    with pytest.raises(core.ZigbeeError, match="get_primary_network_key not available in firmware"):
        stack.get_primary_network_key()
    with pytest.raises(core.ZigbeeError, match="switch_network_key not available in firmware"):
        stack.switch_network_key(key, 3)
    with pytest.raises(core.ZigbeeError, match="broadcast_network_key not available in firmware"):
        stack.broadcast_network_key(key, 4)
    with pytest.raises(core.ZigbeeError, match="broadcast_network_key_switch not available in firmware"):
        stack.broadcast_network_key_switch(4)
    with pytest.raises(core.ZigbeeError, match="add_install_code not available in firmware"):
        stack.add_install_code(ieee, "0011")
    with pytest.raises(core.ZigbeeError, match="set_local_install_code not available in firmware"):
        stack.set_local_install_code("0011")
    with pytest.raises(core.ZigbeeError, match="remove_install_code not available in firmware"):
        stack.remove_install_code(ieee)
    with pytest.raises(core.ZigbeeError, match="remove_all_install_codes not available in firmware"):
        stack.remove_all_install_codes()


def test_discover_node_descriptors_flow():
    core = importlib.import_module("uzigbee.core")
    fake = _FakeUZigbee()
    core._uzigbee = fake

    result = core.ZigbeeStack().discover_node_descriptors(
        0x1234,
        endpoint_ids=[1],
        include_power_desc=True,
        include_green_power=False,
        timeout_ms=50,
        poll_ms=0,
        strict=True,
    )

    assert result["short_addr"] == 0x1234
    assert result["endpoint_ids"] == [1]
    assert result["active_endpoints"] is None
    assert result["node_descriptor"] is not None
    assert len(result["simple_descriptors"]) == 1
    assert result["simple_descriptors"][0]["endpoint"] == 1
    assert result["power_descriptor"] is not None
    assert result["errors"] == []

    assert fake.calls == [
        ("request_node_descriptor", 0x1234),
        ("get_node_descriptor_snapshot",),
        ("request_simple_descriptor", 0x1234, 1),
        ("get_simple_descriptor_snapshot",),
        ("request_power_descriptor", 0x1234),
        ("get_power_descriptor_snapshot",),
    ]


def test_discover_node_descriptors_timeout_strict():
    core = importlib.import_module("uzigbee.core")

    class _NoNodeSnapshot(_FakeUZigbee):
        def get_node_descriptor_snapshot(self):
            self.calls.append(("get_node_descriptor_snapshot",))
            return None

    fake = _NoNodeSnapshot()
    core._uzigbee = fake

    with pytest.raises(core.ZigbeeError, match="timeout waiting for node_descriptor snapshot"):
        core.ZigbeeStack().discover_node_descriptors(
            0x1234,
            endpoint_ids=[],
            include_power_desc=False,
            timeout_ms=0,
            poll_ms=0,
            strict=True,
        )


def test_discover_node_descriptors_non_strict_collects_errors():
    core = importlib.import_module("uzigbee.core")

    class _NoSimpleSnapshot(_FakeUZigbee):
        def get_simple_descriptor_snapshot(self):
            self.calls.append(("get_simple_descriptor_snapshot",))
            return None

    fake = _NoSimpleSnapshot()
    core._uzigbee = fake

    result = core.ZigbeeStack().discover_node_descriptors(
        0x1234,
        endpoint_ids=[1],
        include_power_desc=False,
        timeout_ms=0,
        poll_ms=0,
        strict=False,
    )

    assert result["short_addr"] == 0x1234
    assert result["node_descriptor"] is not None
    assert result["simple_descriptors"] == []
    assert result["power_descriptor"] is None
    assert result["errors"] == ["timeout waiting for simple_descriptor snapshot for endpoint 1"]


def test_last_joined_short_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoLastJoined:
        pass

    core._uzigbee = _NoLastJoined()
    with pytest.raises(core.ZigbeeError, match="get_last_joined_short_addr not available in firmware"):
        core.ZigbeeStack().get_last_joined_short_addr()


def test_network_runtime_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoRuntime:
        pass

    core._uzigbee = _NoRuntime()
    with pytest.raises(core.ZigbeeError, match="get_network_runtime not available in firmware"):
        core.ZigbeeStack().get_network_runtime()


def test_start_network_steering_wrapper_and_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")
    fake = _FakeUZigbee()
    core._uzigbee = fake

    stack = core.ZigbeeStack()
    stack.start_network_steering()
    assert ("start_network_steering",) in fake.calls

    class _NoSteering:
        pass

    core._uzigbee = _NoSteering()
    with pytest.raises(core.ZigbeeError, match="start_network_steering not available in firmware"):
        core.ZigbeeStack().start_network_steering()


def test_pan_and_extended_pan_wrappers_and_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")
    fake = _FakeUZigbee()
    core._uzigbee = fake

    stack = core.ZigbeeStack()
    stack.set_pan_id(0x6C6C)
    stack.set_extended_pan_id("00124b0001c6c6c6")
    stack.enable_wifi_i154_coex()

    assert ("set_pan_id", 0x6C6C) in fake.calls
    assert ("set_extended_pan_id", bytes.fromhex("00124b0001c6c6c6")) in fake.calls
    assert ("enable_wifi_i154_coex",) in fake.calls

    with pytest.raises(ValueError, match="pan_id must be in range"):
        stack.set_pan_id(0x0000)
    with pytest.raises(ValueError, match="extended pan id must be 8 bytes"):
        stack.set_extended_pan_id(b"\x01\x02")

    class _NoPan:
        pass

    core._uzigbee = _NoPan()
    with pytest.raises(core.ZigbeeError, match="set_pan_id not available in firmware"):
        core.ZigbeeStack().set_pan_id(0x6C6C)
    with pytest.raises(core.ZigbeeError, match="set_extended_pan_id not available in firmware"):
        core.ZigbeeStack().set_extended_pan_id(bytes.fromhex("00124b0001c6c6c6"))
    with pytest.raises(core.ZigbeeError, match="enable_wifi_i154_coex not available in firmware"):
        core.ZigbeeStack().enable_wifi_i154_coex()


def test_custom_cluster_wrappers():
    core = importlib.import_module("uzigbee.core")
    fake = _FakeUZigbee()
    core._uzigbee = fake
    stack = core.ZigbeeStack()

    stack.clear_custom_clusters()
    stack.add_custom_cluster(0xFC00, cluster_role=core.CLUSTER_ROLE_SERVER)
    stack.add_custom_attr(
        cluster_id=0xFC00,
        attr_id=0x0001,
        attr_type=0x21,
        attr_access=core.ATTR_ACCESS_READ_WRITE,
        initial_value=7,
    )
    stack.send_custom_cmd(
        dst_short_addr=0x1234,
        cluster_id=0xFC00,
        custom_cmd_id=0x0001,
        payload=b"\x01\x02",
        dst_endpoint=2,
        src_endpoint=3,
        profile_id=0x0104,
        direction=core.CMD_DIRECTION_TO_SERVER,
        disable_default_resp=True,
        manuf_specific=True,
        manuf_code=0x1234,
        data_type=0x41,
    )

    assert ("clear_custom_clusters",) in fake.calls
    assert ("add_custom_cluster", 0xFC00, core.CLUSTER_ROLE_SERVER) in fake.calls
    assert ("add_custom_attr", 0xFC00, 0x0001, 0x21, core.ATTR_ACCESS_READ_WRITE, 7) in fake.calls
    assert (
        "send_custom_cmd",
        3,
        0x1234,
        2,
        0x0104,
        0xFC00,
        0x0001,
        core.CMD_DIRECTION_TO_SERVER,
        True,
        True,
        0x1234,
        0x41,
        b"\x01\x02",
    ) in fake.calls


def test_custom_cluster_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoCustom:
        pass

    core._uzigbee = _NoCustom()
    stack = core.ZigbeeStack()
    with pytest.raises(core.ZigbeeError, match="clear_custom_clusters not available in firmware"):
        stack.clear_custom_clusters()
    with pytest.raises(core.ZigbeeError, match="add_custom_cluster not available in firmware"):
        stack.add_custom_cluster(0xFC00)
    with pytest.raises(core.ZigbeeError, match="add_custom_attr not available in firmware"):
        stack.add_custom_attr(0xFC00, 0x0001, 0x21)
    with pytest.raises(core.ZigbeeError, match="send_custom_cmd not available in firmware"):
        stack.send_custom_cmd(0x1234, 0xFC00, 0x0001)


def test_ota_client_wrappers():
    core = importlib.import_module("uzigbee.core")
    fake = _FakeUZigbee()
    core._uzigbee = fake
    stack = core.ZigbeeStack()

    stack.ota_client_query_interval_set(endpoint_id=1, interval_min=15)
    stack.ota_client_query_image_req(server_ep=1, server_addr=0x00)
    stack.ota_client_query_image_stop()
    assert stack.ota_client_control_supported() is False

    assert ("ota_client_query_interval_set", 1, 15) in fake.calls
    assert ("ota_client_query_image_req", 1, 0x00) in fake.calls
    assert ("ota_client_query_image_stop",) in fake.calls
    assert ("ota_client_control_supported",) in fake.calls


def test_ota_client_helpers_missing_in_firmware():
    core = importlib.import_module("uzigbee.core")

    class _NoOta:
        pass

    core._uzigbee = _NoOta()
    stack = core.ZigbeeStack()
    with pytest.raises(core.ZigbeeError, match="ota_client_query_interval_set not available in firmware"):
        stack.ota_client_query_interval_set()
    with pytest.raises(core.ZigbeeError, match="ota_client_query_image_req not available in firmware"):
        stack.ota_client_query_image_req()
    with pytest.raises(core.ZigbeeError, match="ota_client_query_image_stop not available in firmware"):
        stack.ota_client_query_image_stop()
    assert stack.ota_client_control_supported() is False
