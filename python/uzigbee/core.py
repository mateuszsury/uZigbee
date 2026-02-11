"""Core API skeleton for uzigbee."""

try:
    import _uzigbee  # type: ignore
except ImportError:  # CPython or firmware without C module
    _uzigbee = None

try:
    import time as _time
except ImportError:
    _time = None

try:
    from micropython import const
except ImportError:
    def const(x):
        return x


def _uzb_const(name, default):
    if _uzigbee is not None and hasattr(_uzigbee, name):
        return const(getattr(_uzigbee, name))
    return const(default)


SIGNAL_DEFAULT_START = _uzb_const("SIGNAL_DEFAULT_START", 0x00)
SIGNAL_SKIP_STARTUP = _uzb_const("SIGNAL_SKIP_STARTUP", 0x01)
SIGNAL_DEVICE_ANNCE = _uzb_const("SIGNAL_DEVICE_ANNCE", 0x02)
SIGNAL_LEAVE = _uzb_const("SIGNAL_LEAVE", 0x03)
SIGNAL_ERROR = _uzb_const("SIGNAL_ERROR", 0x04)
SIGNAL_DEVICE_FIRST_START = _uzb_const("SIGNAL_DEVICE_FIRST_START", 0x05)
SIGNAL_DEVICE_REBOOT = _uzb_const("SIGNAL_DEVICE_REBOOT", 0x06)
SIGNAL_TOUCHLINK_NWK_STARTED = _uzb_const("SIGNAL_TOUCHLINK_NWK_STARTED", 0x07)
SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER = _uzb_const("SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER", 0x08)
SIGNAL_TOUCHLINK = _uzb_const("SIGNAL_TOUCHLINK", 0x09)
SIGNAL_STEERING = _uzb_const("SIGNAL_STEERING", 0x0A)
SIGNAL_FORMATION = _uzb_const("SIGNAL_FORMATION", 0x0B)
SIGNAL_FINDING_AND_BINDING_TARGET_FINISHED = _uzb_const("SIGNAL_FINDING_AND_BINDING_TARGET_FINISHED", 0x0C)
SIGNAL_FINDING_AND_BINDING_INITIATOR_FINISHED = _uzb_const("SIGNAL_FINDING_AND_BINDING_INITIATOR_FINISHED", 0x0D)
SIGNAL_TOUCHLINK_TARGET = _uzb_const("SIGNAL_TOUCHLINK_TARGET", 0x0E)
SIGNAL_TOUCHLINK_NWK = _uzb_const("SIGNAL_TOUCHLINK_NWK", 0x0F)
SIGNAL_TOUCHLINK_TARGET_FINISHED = _uzb_const("SIGNAL_TOUCHLINK_TARGET_FINISHED", 0x10)
SIGNAL_DEVICE_ASSOCIATED = _uzb_const("SIGNAL_DEVICE_ASSOCIATED", 0x12)
SIGNAL_LEAVE_INDICATION = _uzb_const("SIGNAL_LEAVE_INDICATION", 0x13)
SIGNAL_GPP_COMMISSIONING = _uzb_const("SIGNAL_GPP_COMMISSIONING", 0x15)
SIGNAL_CAN_SLEEP = _uzb_const("SIGNAL_CAN_SLEEP", 0x16)
SIGNAL_PRODUCTION_CONFIG_READY = _uzb_const("SIGNAL_PRODUCTION_CONFIG_READY", 0x17)
SIGNAL_NO_ACTIVE_LINKS_LEFT = _uzb_const("SIGNAL_NO_ACTIVE_LINKS_LEFT", 0x18)
SIGNAL_DEVICE_AUTHORIZED = _uzb_const("SIGNAL_DEVICE_AUTHORIZED", 0x2F)
SIGNAL_DEVICE_UPDATE = _uzb_const("SIGNAL_DEVICE_UPDATE", 0x30)
SIGNAL_PANID_CONFLICT_DETECTED = _uzb_const("SIGNAL_PANID_CONFLICT_DETECTED", 0x31)
SIGNAL_NWK_STATUS_INDICATION = _uzb_const("SIGNAL_NWK_STATUS_INDICATION", 0x32)
SIGNAL_TC_REJOIN_DONE = _uzb_const("SIGNAL_TC_REJOIN_DONE", 0x35)
SIGNAL_PERMIT_JOIN_STATUS = _uzb_const("SIGNAL_PERMIT_JOIN_STATUS", 0x36)
SIGNAL_STEERING_CANCELLED = _uzb_const("SIGNAL_STEERING_CANCELLED", 0x37)
SIGNAL_FORMATION_CANCELLED = _uzb_const("SIGNAL_FORMATION_CANCELLED", 0x38)
SIGNAL_GPP_MODE_CHANGE = _uzb_const("SIGNAL_GPP_MODE_CHANGE", 0x3B)
SIGNAL_GPP_APPROVE_COMMISSIONING = _uzb_const("SIGNAL_GPP_APPROVE_COMMISSIONING", 0x3D)
SIGNAL_END = _uzb_const("SIGNAL_END", 0x3E)
CLUSTER_ROLE_SERVER = _uzb_const("CLUSTER_ROLE_SERVER", 0x01)
CLUSTER_ROLE_CLIENT = _uzb_const("CLUSTER_ROLE_CLIENT", 0x02)
CLUSTER_ID_BASIC = _uzb_const("CLUSTER_ID_BASIC", 0x0000)
CLUSTER_ID_GROUPS = _uzb_const("CLUSTER_ID_GROUPS", 0x0004)
CLUSTER_ID_SCENES = _uzb_const("CLUSTER_ID_SCENES", 0x0005)
CLUSTER_ID_ON_OFF = _uzb_const("CLUSTER_ID_ON_OFF", 0x0006)
CLUSTER_ID_LEVEL_CONTROL = _uzb_const("CLUSTER_ID_LEVEL_CONTROL", 0x0008)
CLUSTER_ID_OTA_UPGRADE = _uzb_const("CLUSTER_ID_OTA_UPGRADE", 0x0019)
CLUSTER_ID_COLOR_CONTROL = _uzb_const("CLUSTER_ID_COLOR_CONTROL", 0x0300)
CLUSTER_ID_DOOR_LOCK = _uzb_const("CLUSTER_ID_DOOR_LOCK", 0x0101)
CLUSTER_ID_WINDOW_COVERING = _uzb_const("CLUSTER_ID_WINDOW_COVERING", 0x0102)
CLUSTER_ID_THERMOSTAT = _uzb_const("CLUSTER_ID_THERMOSTAT", 0x0201)
CLUSTER_ID_TEMP_MEASUREMENT = _uzb_const("CLUSTER_ID_TEMP_MEASUREMENT", 0x0402)
CLUSTER_ID_PRESSURE_MEASUREMENT = _uzb_const("CLUSTER_ID_PRESSURE_MEASUREMENT", 0x0403)
CLUSTER_ID_REL_HUMIDITY_MEASUREMENT = _uzb_const("CLUSTER_ID_REL_HUMIDITY_MEASUREMENT", 0x0405)
CLUSTER_ID_OCCUPANCY_SENSING = _uzb_const("CLUSTER_ID_OCCUPANCY_SENSING", 0x0406)
CLUSTER_ID_IAS_ZONE = _uzb_const("CLUSTER_ID_IAS_ZONE", 0x0500)
CLUSTER_ID_ELECTRICAL_MEASUREMENT = _uzb_const("CLUSTER_ID_ELECTRICAL_MEASUREMENT", 0x0B04)
ATTR_BASIC_MANUFACTURER_NAME = _uzb_const("ATTR_BASIC_MANUFACTURER_NAME", 0x0004)
ATTR_BASIC_MODEL_IDENTIFIER = _uzb_const("ATTR_BASIC_MODEL_IDENTIFIER", 0x0005)
ATTR_BASIC_DATE_CODE = _uzb_const("ATTR_BASIC_DATE_CODE", 0x0006)
ATTR_BASIC_POWER_SOURCE = _uzb_const("ATTR_BASIC_POWER_SOURCE", 0x0007)
ATTR_BASIC_SW_BUILD_ID = _uzb_const("ATTR_BASIC_SW_BUILD_ID", 0x4000)
ATTR_ON_OFF_ON_OFF = _uzb_const("ATTR_ON_OFF_ON_OFF", 0x0000)
ATTR_LEVEL_CONTROL_CURRENT_LEVEL = _uzb_const("ATTR_LEVEL_CONTROL_CURRENT_LEVEL", 0x0000)
ATTR_DOOR_LOCK_LOCK_STATE = _uzb_const("ATTR_DOOR_LOCK_LOCK_STATE", 0x0000)
ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE = _uzb_const("ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE", 0x0008)
ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE = _uzb_const("ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE", 0x0009)
ATTR_THERMOSTAT_LOCAL_TEMPERATURE = _uzb_const("ATTR_THERMOSTAT_LOCAL_TEMPERATURE", 0x0000)
ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT = _uzb_const("ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT", 0x0012)
ATTR_THERMOSTAT_SYSTEM_MODE = _uzb_const("ATTR_THERMOSTAT_SYSTEM_MODE", 0x001C)
ATTR_TEMP_MEASUREMENT_VALUE = _uzb_const("ATTR_TEMP_MEASUREMENT_VALUE", 0x0000)
ATTR_PRESSURE_MEASUREMENT_VALUE = _uzb_const("ATTR_PRESSURE_MEASUREMENT_VALUE", 0x0000)
ATTR_REL_HUMIDITY_MEASUREMENT_VALUE = _uzb_const("ATTR_REL_HUMIDITY_MEASUREMENT_VALUE", 0x0000)
ATTR_OCCUPANCY_SENSING_OCCUPANCY = _uzb_const("ATTR_OCCUPANCY_SENSING_OCCUPANCY", 0x0000)
ATTR_IAS_ZONE_STATE = _uzb_const("ATTR_IAS_ZONE_STATE", 0x0000)
ATTR_IAS_ZONE_TYPE = _uzb_const("ATTR_IAS_ZONE_TYPE", 0x0001)
ATTR_IAS_ZONE_STATUS = _uzb_const("ATTR_IAS_ZONE_STATUS", 0x0002)
ATTR_IAS_ZONE_IAS_CIE_ADDRESS = _uzb_const("ATTR_IAS_ZONE_IAS_CIE_ADDRESS", 0x0010)
ATTR_IAS_ZONE_ID = _uzb_const("ATTR_IAS_ZONE_ID", 0x0011)
ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE = _uzb_const("ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE", 0x0505)
ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT = _uzb_const("ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT", 0x0508)
ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER = _uzb_const("ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER", 0x050B)
ATTR_COLOR_CONTROL_CURRENT_X = _uzb_const("ATTR_COLOR_CONTROL_CURRENT_X", 0x0003)
ATTR_COLOR_CONTROL_CURRENT_Y = _uzb_const("ATTR_COLOR_CONTROL_CURRENT_Y", 0x0004)
ATTR_COLOR_CONTROL_COLOR_TEMPERATURE = _uzb_const("ATTR_COLOR_CONTROL_COLOR_TEMPERATURE", 0x0007)
BASIC_POWER_SOURCE_UNKNOWN = _uzb_const("BASIC_POWER_SOURCE_UNKNOWN", 0x00)
BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE = _uzb_const("BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE", 0x01)
BASIC_POWER_SOURCE_MAINS_THREE_PHASE = _uzb_const("BASIC_POWER_SOURCE_MAINS_THREE_PHASE", 0x02)
BASIC_POWER_SOURCE_BATTERY = _uzb_const("BASIC_POWER_SOURCE_BATTERY", 0x03)
BASIC_POWER_SOURCE_DC_SOURCE = _uzb_const("BASIC_POWER_SOURCE_DC_SOURCE", 0x04)
BASIC_POWER_SOURCE_EMERGENCY_MAINS_CONST = _uzb_const("BASIC_POWER_SOURCE_EMERGENCY_MAINS_CONST", 0x05)
BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF = _uzb_const("BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF", 0x06)
DEVICE_ID_ON_OFF_SWITCH = _uzb_const("DEVICE_ID_ON_OFF_SWITCH", 0x0000)
DEVICE_ID_LEVEL_CONTROL_SWITCH = _uzb_const("DEVICE_ID_LEVEL_CONTROL_SWITCH", 0x0001)
DEVICE_ID_DIMMER_SWITCH = _uzb_const("DEVICE_ID_DIMMER_SWITCH", 0x0104)
DEVICE_ID_SIMPLE_SENSOR = _uzb_const("DEVICE_ID_SIMPLE_SENSOR", 0x000C)
DEVICE_ID_HUMIDITY_SENSOR = _uzb_const("DEVICE_ID_HUMIDITY_SENSOR", 0x000C)
DEVICE_ID_PRESSURE_SENSOR = _uzb_const("DEVICE_ID_PRESSURE_SENSOR", 0x000C)
DEVICE_ID_CLIMATE_SENSOR = _uzb_const("DEVICE_ID_CLIMATE_SENSOR", 0x000C)
DEVICE_ID_MAINS_POWER_OUTLET = _uzb_const("DEVICE_ID_MAINS_POWER_OUTLET", 0x0009)
DEVICE_ID_SMART_PLUG = _uzb_const("DEVICE_ID_SMART_PLUG", 0x0051)
DEVICE_ID_DOOR_LOCK = _uzb_const("DEVICE_ID_DOOR_LOCK", 0x000A)
DEVICE_ID_DOOR_LOCK_CONTROLLER = _uzb_const("DEVICE_ID_DOOR_LOCK_CONTROLLER", 0x000B)
DEVICE_ID_WINDOW_COVERING = _uzb_const("DEVICE_ID_WINDOW_COVERING", 0x0202)
DEVICE_ID_THERMOSTAT = _uzb_const("DEVICE_ID_THERMOSTAT", 0x0301)
DEVICE_ID_OCCUPANCY_SENSOR = _uzb_const("DEVICE_ID_OCCUPANCY_SENSOR", 0x000C)
DEVICE_ID_IAS_ZONE = _uzb_const("DEVICE_ID_IAS_ZONE", 0x0402)
DEVICE_ID_CONTACT_SENSOR = _uzb_const("DEVICE_ID_CONTACT_SENSOR", 0x0402)
DEVICE_ID_MOTION_SENSOR = _uzb_const("DEVICE_ID_MOTION_SENSOR", 0x0402)
DEVICE_ID_DIMMABLE_LIGHT = _uzb_const("DEVICE_ID_DIMMABLE_LIGHT", 0x0101)
DEVICE_ID_COLOR_DIMMABLE_LIGHT = _uzb_const("DEVICE_ID_COLOR_DIMMABLE_LIGHT", 0x0102)
DEVICE_ID_TEMPERATURE_SENSOR = _uzb_const("DEVICE_ID_TEMPERATURE_SENSOR", 0x0302)
CMD_ON_OFF_OFF = _uzb_const("CMD_ON_OFF_OFF", 0x00)
CMD_ON_OFF_ON = _uzb_const("CMD_ON_OFF_ON", 0x01)
CMD_ON_OFF_TOGGLE = _uzb_const("CMD_ON_OFF_TOGGLE", 0x02)
CMD_SCENES_ADD = _uzb_const("CMD_SCENES_ADD", 0x00)
CMD_SCENES_REMOVE = _uzb_const("CMD_SCENES_REMOVE", 0x02)
CMD_SCENES_REMOVE_ALL = _uzb_const("CMD_SCENES_REMOVE_ALL", 0x03)
CMD_SCENES_STORE = _uzb_const("CMD_SCENES_STORE", 0x04)
CMD_SCENES_RECALL = _uzb_const("CMD_SCENES_RECALL", 0x05)
CMD_SCENES_GET_MEMBERSHIP = _uzb_const("CMD_SCENES_GET_MEMBERSHIP", 0x06)
IC_TYPE_48 = _uzb_const("IC_TYPE_48", 0x00)
IC_TYPE_64 = _uzb_const("IC_TYPE_64", 0x01)
IC_TYPE_96 = _uzb_const("IC_TYPE_96", 0x02)
IC_TYPE_128 = _uzb_const("IC_TYPE_128", 0x03)
CMD_DOOR_LOCK_LOCK_DOOR = _uzb_const("CMD_DOOR_LOCK_LOCK_DOOR", 0x00)
CMD_DOOR_LOCK_UNLOCK_DOOR = _uzb_const("CMD_DOOR_LOCK_UNLOCK_DOOR", 0x01)
CMD_WINDOW_COVERING_UP_OPEN = _uzb_const("CMD_WINDOW_COVERING_UP_OPEN", 0x00)
CMD_WINDOW_COVERING_DOWN_CLOSE = _uzb_const("CMD_WINDOW_COVERING_DOWN_CLOSE", 0x01)
CMD_WINDOW_COVERING_STOP = _uzb_const("CMD_WINDOW_COVERING_STOP", 0x02)
CMD_WINDOW_COVERING_GO_TO_LIFT_PERCENTAGE = _uzb_const("CMD_WINDOW_COVERING_GO_TO_LIFT_PERCENTAGE", 0x05)
CMD_LEVEL_MOVE_TO_LEVEL = _uzb_const("CMD_LEVEL_MOVE_TO_LEVEL", 0x00)
CMD_LEVEL_MOVE_TO_LEVEL_WITH_ONOFF = _uzb_const("CMD_LEVEL_MOVE_TO_LEVEL_WITH_ONOFF", 0x04)
CMD_COLOR_MOVE_TO_COLOR = _uzb_const("CMD_COLOR_MOVE_TO_COLOR", 0x07)
CMD_COLOR_MOVE_TO_COLOR_TEMPERATURE = _uzb_const("CMD_COLOR_MOVE_TO_COLOR_TEMPERATURE", 0x0A)
IAS_ZONE_TYPE_MOTION = _uzb_const("IAS_ZONE_TYPE_MOTION", 0x000D)
IAS_ZONE_TYPE_CONTACT_SWITCH = _uzb_const("IAS_ZONE_TYPE_CONTACT_SWITCH", 0x0015)
IAS_ZONE_STATUS_ALARM1 = _uzb_const("IAS_ZONE_STATUS_ALARM1", 0x0001)
IAS_ZONE_STATUS_ALARM2 = _uzb_const("IAS_ZONE_STATUS_ALARM2", 0x0002)
IAS_ZONE_STATUS_TAMPER = _uzb_const("IAS_ZONE_STATUS_TAMPER", 0x0004)
IAS_ZONE_STATUS_BATTERY = _uzb_const("IAS_ZONE_STATUS_BATTERY", 0x0008)
CUSTOM_CLUSTER_ID_MIN = _uzb_const("CUSTOM_CLUSTER_ID_MIN", 0xFC00)
ATTR_ACCESS_READ_ONLY = _uzb_const("ATTR_ACCESS_READ_ONLY", 0x01)
ATTR_ACCESS_WRITE_ONLY = _uzb_const("ATTR_ACCESS_WRITE_ONLY", 0x02)
ATTR_ACCESS_READ_WRITE = _uzb_const("ATTR_ACCESS_READ_WRITE", 0x03)
ATTR_ACCESS_REPORTING = _uzb_const("ATTR_ACCESS_REPORTING", 0x04)
ATTR_ACCESS_SCENE = _uzb_const("ATTR_ACCESS_SCENE", 0x10)
CMD_DIRECTION_TO_SERVER = _uzb_const("CMD_DIRECTION_TO_SERVER", 0x00)
CMD_DIRECTION_TO_CLIENT = _uzb_const("CMD_DIRECTION_TO_CLIENT", 0x01)

SIGNAL_NAMES = {
    SIGNAL_DEFAULT_START: "default_start",
    SIGNAL_SKIP_STARTUP: "skip_startup",
    SIGNAL_DEVICE_ANNCE: "device_announce",
    SIGNAL_LEAVE: "leave",
    SIGNAL_ERROR: "error",
    SIGNAL_DEVICE_FIRST_START: "device_first_start",
    SIGNAL_DEVICE_REBOOT: "device_reboot",
    SIGNAL_TOUCHLINK_NWK_STARTED: "touchlink_network_started",
    SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER: "touchlink_joined_router",
    SIGNAL_TOUCHLINK: "touchlink",
    SIGNAL_STEERING: "steering",
    SIGNAL_FORMATION: "formation",
    SIGNAL_FINDING_AND_BINDING_TARGET_FINISHED: "finding_binding_target_finished",
    SIGNAL_FINDING_AND_BINDING_INITIATOR_FINISHED: "finding_binding_initiator_finished",
    SIGNAL_TOUCHLINK_TARGET: "touchlink_target",
    SIGNAL_TOUCHLINK_NWK: "touchlink_network",
    SIGNAL_TOUCHLINK_TARGET_FINISHED: "touchlink_target_finished",
    SIGNAL_DEVICE_ASSOCIATED: "device_associated",
    SIGNAL_LEAVE_INDICATION: "leave_indication",
    SIGNAL_GPP_COMMISSIONING: "gpp_commissioning",
    SIGNAL_CAN_SLEEP: "can_sleep",
    SIGNAL_PRODUCTION_CONFIG_READY: "production_config_ready",
    SIGNAL_NO_ACTIVE_LINKS_LEFT: "no_active_links_left",
    SIGNAL_DEVICE_AUTHORIZED: "device_authorized",
    SIGNAL_DEVICE_UPDATE: "device_update",
    SIGNAL_PANID_CONFLICT_DETECTED: "panid_conflict_detected",
    SIGNAL_NWK_STATUS_INDICATION: "network_status_indication",
    SIGNAL_TC_REJOIN_DONE: "tc_rejoin_done",
    SIGNAL_PERMIT_JOIN_STATUS: "permit_join_status",
    SIGNAL_STEERING_CANCELLED: "steering_cancelled",
    SIGNAL_FORMATION_CANCELLED: "formation_cancelled",
    SIGNAL_GPP_MODE_CHANGE: "gpp_mode_change",
    SIGNAL_GPP_APPROVE_COMMISSIONING: "gpp_approve_commissioning",
}


def signal_name(signal_id):
    return SIGNAL_NAMES.get(int(signal_id), "unknown")


class ZigbeeError(Exception):
    pass


def _ticks_ms():
    if _time is None:
        return 0
    if hasattr(_time, "ticks_ms"):
        return int(_time.ticks_ms())
    return int(_time.time() * 1000)


def _ticks_add(base_ms, delta_ms):
    if _time is not None and hasattr(_time, "ticks_add"):
        return int(_time.ticks_add(int(base_ms), int(delta_ms)))
    return int(base_ms) + int(delta_ms)


def _ticks_diff(end_ms, now_ms):
    if _time is not None and hasattr(_time, "ticks_diff"):
        return int(_time.ticks_diff(int(end_ms), int(now_ms)))
    return int(end_ms) - int(now_ms)


def _sleep_ms(ms):
    ms = int(ms)
    if ms <= 0 or _time is None:
        return
    if hasattr(_time, "sleep_ms"):
        _time.sleep_ms(ms)
        return
    _time.sleep(ms / 1000.0)


def _coerce_ieee_addr(value):
    try:
        out = bytes(value)
    except Exception:
        raise ValueError("ieee address must be bytes-like with length 8")
    if len(out) != 8:
        raise ValueError("ieee address must be 8 bytes")
    return out


def _coerce_key16(value):
    try:
        out = bytes(value)
    except Exception:
        raise ValueError("network key must be bytes-like with length 16")
    if len(out) != 16:
        raise ValueError("network key must be 16 bytes")
    return out


class ZigbeeStack:
    """Singleton wrapper for the Zigbee stack."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init(self, role):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.init(role)

    def start(self, form_network=False):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.start(bool(form_network))

    def create_endpoint(self, endpoint_id, device_id, profile_id=None):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if profile_id is None:
            profile_id = PROFILE_ID_ZHA
        return _uzigbee.create_endpoint(int(endpoint_id), int(device_id), int(profile_id))

    def register_device(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.register_device()

    def create_on_off_light(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_on_off_light"):
            return _uzigbee.create_on_off_light(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_ON_OFF_LIGHT), int(PROFILE_ID_ZHA))

    def create_on_off_switch(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_on_off_switch"):
            return _uzigbee.create_on_off_switch(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_ON_OFF_SWITCH), int(PROFILE_ID_ZHA))

    def create_dimmable_switch(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_dimmable_switch"):
            return _uzigbee.create_dimmable_switch(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_DIMMER_SWITCH), int(PROFILE_ID_ZHA))

    def create_dimmable_light(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_dimmable_light"):
            return _uzigbee.create_dimmable_light(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_DIMMABLE_LIGHT), int(PROFILE_ID_ZHA))

    def create_color_light(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_color_light"):
            return _uzigbee.create_color_light(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_COLOR_DIMMABLE_LIGHT), int(PROFILE_ID_ZHA))

    def create_temperature_sensor(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_temperature_sensor"):
            return _uzigbee.create_temperature_sensor(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_TEMPERATURE_SENSOR), int(PROFILE_ID_ZHA))

    def create_humidity_sensor(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_humidity_sensor"):
            return _uzigbee.create_humidity_sensor(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_HUMIDITY_SENSOR), int(PROFILE_ID_ZHA))

    def create_pressure_sensor(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_pressure_sensor"):
            return _uzigbee.create_pressure_sensor(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_PRESSURE_SENSOR), int(PROFILE_ID_ZHA))

    def create_climate_sensor(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_climate_sensor"):
            return _uzigbee.create_climate_sensor(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_CLIMATE_SENSOR), int(PROFILE_ID_ZHA))

    def create_power_outlet(self, endpoint_id=1, with_metering=False):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_power_outlet"):
            return _uzigbee.create_power_outlet(int(endpoint_id), bool(with_metering))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_MAINS_POWER_OUTLET), int(PROFILE_ID_ZHA))

    def create_door_lock(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_door_lock"):
            return _uzigbee.create_door_lock(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_DOOR_LOCK), int(PROFILE_ID_ZHA))

    def create_door_lock_controller(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_door_lock_controller"):
            return _uzigbee.create_door_lock_controller(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_DOOR_LOCK_CONTROLLER), int(PROFILE_ID_ZHA))

    def create_thermostat(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_thermostat"):
            return _uzigbee.create_thermostat(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_THERMOSTAT), int(PROFILE_ID_ZHA))

    def create_occupancy_sensor(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_occupancy_sensor"):
            return _uzigbee.create_occupancy_sensor(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_OCCUPANCY_SENSOR), int(PROFILE_ID_ZHA))

    def create_window_covering(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_window_covering"):
            return _uzigbee.create_window_covering(int(endpoint_id))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_WINDOW_COVERING), int(PROFILE_ID_ZHA))

    def create_ias_zone(self, endpoint_id=1, zone_type=IAS_ZONE_TYPE_CONTACT_SWITCH):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_ias_zone"):
            return _uzigbee.create_ias_zone(int(endpoint_id), int(zone_type))
        return _uzigbee.create_endpoint(int(endpoint_id), int(DEVICE_ID_IAS_ZONE), int(PROFILE_ID_ZHA))

    def create_contact_sensor(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_contact_sensor"):
            return _uzigbee.create_contact_sensor(int(endpoint_id))
        return self.create_ias_zone(int(endpoint_id), IAS_ZONE_TYPE_CONTACT_SWITCH)

    def create_motion_sensor(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "create_motion_sensor"):
            return _uzigbee.create_motion_sensor(int(endpoint_id))
        return self.create_ias_zone(int(endpoint_id), IAS_ZONE_TYPE_MOTION)

    def set_basic_identity(self, endpoint_id=1, manufacturer="uzigbee", model="uzb_device", date_code=None, sw_build_id=None,
                           power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_basic_identity"):
            raise ZigbeeError("set_basic_identity not available in firmware")
        return _uzigbee.set_basic_identity(
            endpoint=int(endpoint_id),
            manufacturer=manufacturer,
            model=model,
            date_code=date_code,
            sw_build_id=sw_build_id,
            power_source=int(power_source),
        )

    def get_attribute(self, endpoint_id, cluster_id, attr_id, cluster_role=CLUSTER_ROLE_SERVER):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.get_attribute(int(endpoint_id), int(cluster_id), int(attr_id), int(cluster_role))

    def get_basic_identity(self, endpoint_id=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_basic_identity"):
            raise ZigbeeError("get_basic_identity not available in firmware")
        result = _uzigbee.get_basic_identity(int(endpoint_id))
        return {
            "manufacturer_name": result[0],
            "model_identifier": result[1],
            "date_code": result[2],
            "sw_build_id": result[3],
            "power_source": result[4],
        }

    def set_attribute(self, endpoint_id, cluster_id, attr_id, value, cluster_role=CLUSTER_ROLE_SERVER, check=False):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.set_attribute(int(endpoint_id), int(cluster_id), int(attr_id), value, int(cluster_role), bool(check))

    def configure_reporting(
        self,
        dst_short_addr,
        cluster_id,
        attr_id,
        attr_type,
        src_endpoint=1,
        dst_endpoint=1,
        min_interval=0,
        max_interval=300,
        reportable_change=None,
    ):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "configure_reporting"):
            raise ZigbeeError("configure_reporting not available in firmware")
        return _uzigbee.configure_reporting(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            cluster_id=int(cluster_id),
            attr_id=int(attr_id),
            attr_type=int(attr_type),
            min_interval=int(min_interval),
            max_interval=int(max_interval),
            reportable_change=None if reportable_change is None else int(reportable_change),
        )

    def send_on_off_cmd(self, dst_short_addr, dst_endpoint=1, src_endpoint=1, cmd_id=CMD_ON_OFF_TOGGLE):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_on_off_cmd"):
            raise ZigbeeError("send_on_off_cmd not available in firmware")
        return _uzigbee.send_on_off_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            cmd_id=int(cmd_id),
        )

    def send_level_cmd(
        self,
        dst_short_addr,
        level,
        dst_endpoint=1,
        src_endpoint=1,
        transition_ds=0,
        with_onoff=True,
    ):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_level_cmd"):
            raise ZigbeeError("send_level_cmd not available in firmware")
        return _uzigbee.send_level_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            level=int(level),
            transition_ds=int(transition_ds),
            with_onoff=bool(with_onoff),
        )

    def send_lock_cmd(self, dst_short_addr, lock=True, dst_endpoint=1, src_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_lock_cmd"):
            raise ZigbeeError("send_lock_cmd not available in firmware")
        return _uzigbee.send_lock_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            lock=bool(lock),
        )

    def send_color_move_to_color_cmd(
        self,
        dst_short_addr,
        color_x,
        color_y,
        dst_endpoint=1,
        src_endpoint=1,
        transition_ds=0,
    ):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_color_move_to_color_cmd"):
            raise ZigbeeError("send_color_move_to_color_cmd not available in firmware")
        return _uzigbee.send_color_move_to_color_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            color_x=int(color_x),
            color_y=int(color_y),
            transition_ds=int(transition_ds),
        )

    def send_color_move_to_color_temperature_cmd(
        self,
        dst_short_addr,
        color_temperature,
        dst_endpoint=1,
        src_endpoint=1,
        transition_ds=0,
    ):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_color_move_to_color_temperature_cmd"):
            raise ZigbeeError("send_color_move_to_color_temperature_cmd not available in firmware")
        return _uzigbee.send_color_move_to_color_temperature_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            color_temperature=int(color_temperature),
            transition_ds=int(transition_ds),
        )

    def send_group_add_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_group_add_cmd"):
            raise ZigbeeError("send_group_add_cmd not available in firmware")
        return _uzigbee.send_group_add_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            group_id=int(group_id),
        )

    def send_group_remove_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_group_remove_cmd"):
            raise ZigbeeError("send_group_remove_cmd not available in firmware")
        return _uzigbee.send_group_remove_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            group_id=int(group_id),
        )

    def send_group_remove_all_cmd(self, dst_short_addr, dst_endpoint=1, src_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_group_remove_all_cmd"):
            raise ZigbeeError("send_group_remove_all_cmd not available in firmware")
        return _uzigbee.send_group_remove_all_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
        )

    def send_scene_add_cmd(self, dst_short_addr, group_id, scene_id, dst_endpoint=1, src_endpoint=1, transition_ds=0):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_scene_add_cmd"):
            raise ZigbeeError("send_scene_add_cmd not available in firmware")
        return _uzigbee.send_scene_add_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            group_id=int(group_id),
            scene_id=int(scene_id),
            transition_ds=int(transition_ds),
        )

    def send_scene_remove_cmd(self, dst_short_addr, group_id, scene_id, dst_endpoint=1, src_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_scene_remove_cmd"):
            raise ZigbeeError("send_scene_remove_cmd not available in firmware")
        return _uzigbee.send_scene_remove_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            group_id=int(group_id),
            scene_id=int(scene_id),
        )

    def send_scene_remove_all_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_scene_remove_all_cmd"):
            raise ZigbeeError("send_scene_remove_all_cmd not available in firmware")
        return _uzigbee.send_scene_remove_all_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            group_id=int(group_id),
        )

    def send_scene_recall_cmd(self, dst_short_addr, group_id, scene_id, dst_endpoint=1, src_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_scene_recall_cmd"):
            raise ZigbeeError("send_scene_recall_cmd not available in firmware")
        return _uzigbee.send_scene_recall_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            group_id=int(group_id),
            scene_id=int(scene_id),
        )

    def clear_custom_clusters(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "clear_custom_clusters"):
            raise ZigbeeError("clear_custom_clusters not available in firmware")
        return _uzigbee.clear_custom_clusters()

    def add_custom_cluster(self, cluster_id, cluster_role=CLUSTER_ROLE_SERVER):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "add_custom_cluster"):
            raise ZigbeeError("add_custom_cluster not available in firmware")
        cluster_id = int(cluster_id)
        if cluster_id < CUSTOM_CLUSTER_ID_MIN or cluster_id > 0xFFFF:
            raise ValueError("custom cluster_id must be in range 0xFC00..0xFFFF")
        return _uzigbee.add_custom_cluster(
            cluster_id=cluster_id,
            cluster_role=int(cluster_role),
        )

    def add_custom_attr(self, cluster_id, attr_id, attr_type, attr_access=ATTR_ACCESS_READ_WRITE, initial_value=0):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "add_custom_attr"):
            raise ZigbeeError("add_custom_attr not available in firmware")
        cluster_id = int(cluster_id)
        if cluster_id < CUSTOM_CLUSTER_ID_MIN or cluster_id > 0xFFFF:
            raise ValueError("custom cluster_id must be in range 0xFC00..0xFFFF")
        return _uzigbee.add_custom_attr(
            cluster_id=cluster_id,
            attr_id=int(attr_id),
            attr_type=int(attr_type),
            attr_access=int(attr_access),
            initial_value=int(initial_value),
        )

    def send_custom_cmd(
        self,
        dst_short_addr,
        cluster_id,
        custom_cmd_id,
        payload=None,
        dst_endpoint=1,
        src_endpoint=1,
        profile_id=0x0104,
        direction=CMD_DIRECTION_TO_SERVER,
        disable_default_resp=False,
        manuf_specific=False,
        manuf_code=0,
        data_type=0x41,
    ):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_custom_cmd"):
            raise ZigbeeError("send_custom_cmd not available in firmware")
        cluster_id = int(cluster_id)
        if cluster_id < CUSTOM_CLUSTER_ID_MIN or cluster_id > 0xFFFF:
            raise ValueError("custom cluster_id must be in range 0xFC00..0xFFFF")
        payload_obj = None if payload is None else bytes(payload)
        return _uzigbee.send_custom_cmd(
            src_endpoint=int(src_endpoint),
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            profile_id=int(profile_id),
            cluster_id=cluster_id,
            custom_cmd_id=int(custom_cmd_id),
            direction=int(direction),
            disable_default_resp=bool(disable_default_resp),
            manuf_specific=bool(manuf_specific),
            manuf_code=int(manuf_code),
            data_type=int(data_type),
            payload=payload_obj,
        )

    def ota_client_query_interval_set(self, endpoint_id=1, interval_min=5):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "ota_client_query_interval_set"):
            raise ZigbeeError("ota_client_query_interval_set not available in firmware")
        return _uzigbee.ota_client_query_interval_set(
            endpoint=int(endpoint_id),
            interval_min=int(interval_min),
        )

    def ota_client_query_image_req(self, server_ep=1, server_addr=0x00):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "ota_client_query_image_req"):
            raise ZigbeeError("ota_client_query_image_req not available in firmware")
        return _uzigbee.ota_client_query_image_req(
            server_ep=int(server_ep),
            server_addr=int(server_addr),
        )

    def ota_client_query_image_stop(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "ota_client_query_image_stop"):
            raise ZigbeeError("ota_client_query_image_stop not available in firmware")
        return _uzigbee.ota_client_query_image_stop()

    def ota_client_control_supported(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "ota_client_control_supported"):
            return False
        return bool(_uzigbee.ota_client_control_supported())

    def set_install_code_policy(self, enabled=False):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_install_code_policy"):
            raise ZigbeeError("set_install_code_policy not available in firmware")
        return _uzigbee.set_install_code_policy(enabled=bool(enabled))

    def get_install_code_policy(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_install_code_policy"):
            raise ZigbeeError("get_install_code_policy not available in firmware")
        return bool(_uzigbee.get_install_code_policy())

    def set_network_security_enabled(self, enabled=True):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_network_security_enabled"):
            raise ZigbeeError("set_network_security_enabled not available in firmware")
        return _uzigbee.set_network_security_enabled(enabled=bool(enabled))

    def is_network_security_enabled(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "is_network_security_enabled"):
            raise ZigbeeError("is_network_security_enabled not available in firmware")
        return bool(_uzigbee.is_network_security_enabled())

    def set_network_key(self, key):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_network_key"):
            raise ZigbeeError("set_network_key not available in firmware")
        return _uzigbee.set_network_key(key=_coerce_key16(key))

    def get_primary_network_key(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_primary_network_key"):
            raise ZigbeeError("get_primary_network_key not available in firmware")
        return bytes(_uzigbee.get_primary_network_key())

    def switch_network_key(self, key, key_seq_num):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "switch_network_key"):
            raise ZigbeeError("switch_network_key not available in firmware")
        return _uzigbee.switch_network_key(
            key=_coerce_key16(key),
            key_seq_num=int(key_seq_num),
        )

    def broadcast_network_key(self, key, key_seq_num):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "broadcast_network_key"):
            raise ZigbeeError("broadcast_network_key not available in firmware")
        return _uzigbee.broadcast_network_key(
            key=_coerce_key16(key),
            key_seq_num=int(key_seq_num),
        )

    def broadcast_network_key_switch(self, key_seq_num):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "broadcast_network_key_switch"):
            raise ZigbeeError("broadcast_network_key_switch not available in firmware")
        return _uzigbee.broadcast_network_key_switch(key_seq_num=int(key_seq_num))

    def add_install_code(self, ieee_addr, ic_str):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "add_install_code"):
            raise ZigbeeError("add_install_code not available in firmware")
        return _uzigbee.add_install_code(
            ieee_addr=_coerce_ieee_addr(ieee_addr),
            ic_str=str(ic_str),
        )

    def set_local_install_code(self, ic_str):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_local_install_code"):
            raise ZigbeeError("set_local_install_code not available in firmware")
        return _uzigbee.set_local_install_code(ic_str=str(ic_str))

    def remove_install_code(self, ieee_addr):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "remove_install_code"):
            raise ZigbeeError("remove_install_code not available in firmware")
        return _uzigbee.remove_install_code(ieee_addr=_coerce_ieee_addr(ieee_addr))

    def remove_all_install_codes(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "remove_all_install_codes"):
            raise ZigbeeError("remove_all_install_codes not available in firmware")
        return _uzigbee.remove_all_install_codes()

    def send_bind_cmd(self, src_ieee_addr, cluster_id, dst_ieee_addr, req_dst_short_addr, src_endpoint=1, dst_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_bind_cmd"):
            raise ZigbeeError("send_bind_cmd not available in firmware")
        return _uzigbee.send_bind_cmd(
            src_ieee_addr=_coerce_ieee_addr(src_ieee_addr),
            src_endpoint=int(src_endpoint),
            cluster_id=int(cluster_id),
            dst_ieee_addr=_coerce_ieee_addr(dst_ieee_addr),
            dst_endpoint=int(dst_endpoint),
            req_dst_short_addr=int(req_dst_short_addr),
        )

    def send_unbind_cmd(self, src_ieee_addr, cluster_id, dst_ieee_addr, req_dst_short_addr, src_endpoint=1, dst_endpoint=1):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "send_unbind_cmd"):
            raise ZigbeeError("send_unbind_cmd not available in firmware")
        return _uzigbee.send_unbind_cmd(
            src_ieee_addr=_coerce_ieee_addr(src_ieee_addr),
            src_endpoint=int(src_endpoint),
            cluster_id=int(cluster_id),
            dst_ieee_addr=_coerce_ieee_addr(dst_ieee_addr),
            dst_endpoint=int(dst_endpoint),
            req_dst_short_addr=int(req_dst_short_addr),
        )

    def request_binding_table(self, dst_short_addr, start_index=0):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "request_binding_table"):
            raise ZigbeeError("request_binding_table not available in firmware")
        return _uzigbee.request_binding_table(
            dst_short_addr=int(dst_short_addr),
            start_index=int(start_index),
        )

    def get_binding_table_snapshot(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_binding_table_snapshot"):
            raise ZigbeeError("get_binding_table_snapshot not available in firmware")
        raw = _uzigbee.get_binding_table_snapshot()
        if raw is None:
            return None

        status, index, total, count, records = raw
        out_records = []
        for rec in records:
            src_ieee_addr, src_endpoint, cluster_id, dst_addr_mode, dst_short_addr, dst_ieee_addr, dst_endpoint = rec
            out_records.append(
                {
                    "src_ieee_addr": bytes(src_ieee_addr),
                    "src_endpoint": int(src_endpoint),
                    "cluster_id": int(cluster_id),
                    "dst_addr_mode": int(dst_addr_mode),
                    "dst_short_addr": None if dst_short_addr is None else int(dst_short_addr),
                    "dst_ieee_addr": None if dst_ieee_addr is None else bytes(dst_ieee_addr),
                    "dst_endpoint": None if dst_endpoint is None else int(dst_endpoint),
                }
            )

        return {
            "status": int(status),
            "index": int(index),
            "total": int(total),
            "count": int(count),
            "records": out_records,
        }

    def request_active_endpoints(self, dst_short_addr):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "request_active_endpoints"):
            raise ZigbeeError("request_active_endpoints not available in firmware")
        return _uzigbee.request_active_endpoints(
            dst_short_addr=int(dst_short_addr),
        )

    def get_active_endpoints_snapshot(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_active_endpoints_snapshot"):
            raise ZigbeeError("get_active_endpoints_snapshot not available in firmware")
        raw = _uzigbee.get_active_endpoints_snapshot()
        if raw is None:
            return None
        status, count, endpoints = raw
        return {
            "status": int(status),
            "count": int(count),
            "endpoints": [int(ep) for ep in endpoints],
        }

    def request_node_descriptor(self, dst_short_addr):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "request_node_descriptor"):
            raise ZigbeeError("request_node_descriptor not available in firmware")
        return _uzigbee.request_node_descriptor(
            dst_short_addr=int(dst_short_addr),
        )

    def get_node_descriptor_snapshot(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_node_descriptor_snapshot"):
            raise ZigbeeError("get_node_descriptor_snapshot not available in firmware")
        raw = _uzigbee.get_node_descriptor_snapshot()
        if raw is None:
            return None

        status, addr, desc = raw
        desc_out = None
        if desc is not None:
            (
                node_desc_flags,
                mac_capability_flags,
                manufacturer_code,
                max_buf_size,
                max_incoming_transfer_size,
                server_mask,
                max_outgoing_transfer_size,
                desc_capability_field,
            ) = desc
            desc_out = {
                "node_desc_flags": int(node_desc_flags),
                "mac_capability_flags": int(mac_capability_flags),
                "manufacturer_code": int(manufacturer_code),
                "max_buf_size": int(max_buf_size),
                "max_incoming_transfer_size": int(max_incoming_transfer_size),
                "server_mask": int(server_mask),
                "max_outgoing_transfer_size": int(max_outgoing_transfer_size),
                "desc_capability_field": int(desc_capability_field),
            }

        return {
            "status": int(status),
            "addr": int(addr),
            "node_desc": desc_out,
        }

    def request_simple_descriptor(self, dst_short_addr, endpoint):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "request_simple_descriptor"):
            raise ZigbeeError("request_simple_descriptor not available in firmware")
        return _uzigbee.request_simple_descriptor(
            dst_short_addr=int(dst_short_addr),
            endpoint=int(endpoint),
        )

    def get_simple_descriptor_snapshot(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_simple_descriptor_snapshot"):
            raise ZigbeeError("get_simple_descriptor_snapshot not available in firmware")
        raw = _uzigbee.get_simple_descriptor_snapshot()
        if raw is None:
            return None

        status, addr, simple_desc = raw
        desc_out = None
        if simple_desc is not None:
            endpoint, profile_id, device_id, device_version, input_clusters, output_clusters = simple_desc
            desc_out = {
                "endpoint": int(endpoint),
                "profile_id": int(profile_id),
                "device_id": int(device_id),
                "device_version": int(device_version),
                "input_clusters": [int(cluster_id) for cluster_id in input_clusters],
                "output_clusters": [int(cluster_id) for cluster_id in output_clusters],
            }

        return {
            "status": int(status),
            "addr": int(addr),
            "simple_desc": desc_out,
        }

    def request_power_descriptor(self, dst_short_addr):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "request_power_descriptor"):
            raise ZigbeeError("request_power_descriptor not available in firmware")
        return _uzigbee.request_power_descriptor(
            dst_short_addr=int(dst_short_addr),
        )

    def get_power_descriptor_snapshot(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_power_descriptor_snapshot"):
            raise ZigbeeError("get_power_descriptor_snapshot not available in firmware")
        raw = _uzigbee.get_power_descriptor_snapshot()
        if raw is None:
            return None

        status, addr, power_desc = raw
        desc_out = None
        if power_desc is not None:
            current_power_mode, available_power_sources, current_power_source, current_power_source_level = power_desc
            desc_out = {
                "current_power_mode": int(current_power_mode),
                "available_power_sources": int(available_power_sources),
                "current_power_source": int(current_power_source),
                "current_power_source_level": int(current_power_source_level),
            }

        return {
            "status": int(status),
            "addr": int(addr),
            "power_desc": desc_out,
        }

    def _poll_snapshot(self, getter, timeout_ms, poll_ms, validator=None):
        timeout_ms = int(timeout_ms)
        poll_ms = int(poll_ms)
        if poll_ms < 0:
            poll_ms = 0
        deadline_ms = _ticks_add(_ticks_ms(), timeout_ms if timeout_ms > 0 else 0)

        while True:
            snapshot = getter()
            if snapshot is not None:
                if validator is None or validator(snapshot):
                    return snapshot

            if timeout_ms <= 0:
                return None
            if _ticks_diff(deadline_ms, _ticks_ms()) <= 0:
                return None
            _sleep_ms(poll_ms)

    def discover_node_descriptors(
        self,
        dst_short_addr,
        endpoint_ids=None,
        include_power_desc=True,
        include_green_power=False,
        timeout_ms=5000,
        poll_ms=200,
        strict=True,
    ):
        dst_short_addr = int(dst_short_addr)
        result = {
            "short_addr": dst_short_addr,
            "endpoint_ids": [],
            "active_endpoints": None,
            "node_descriptor": None,
            "simple_descriptors": [],
            "power_descriptor": None,
            "errors": [],
        }

        def _on_error(message):
            if strict:
                raise ZigbeeError(message)
            result["errors"].append(message)

        if endpoint_ids is None:
            self.request_active_endpoints(dst_short_addr)
            active_snapshot = self._poll_snapshot(
                self.get_active_endpoints_snapshot,
                timeout_ms=timeout_ms,
                poll_ms=poll_ms,
            )
            if active_snapshot is None:
                _on_error("timeout waiting for active_endpoints snapshot")
                endpoint_ids = []
            else:
                result["active_endpoints"] = active_snapshot
                endpoint_ids = active_snapshot.get("endpoints", [])
        else:
            endpoint_ids = [int(endpoint_id) for endpoint_id in endpoint_ids]

        if not include_green_power:
            endpoint_ids = [endpoint_id for endpoint_id in endpoint_ids if int(endpoint_id) != 242]
        result["endpoint_ids"] = [int(endpoint_id) for endpoint_id in endpoint_ids]

        self.request_node_descriptor(dst_short_addr)
        node_snapshot = self._poll_snapshot(
            self.get_node_descriptor_snapshot,
            timeout_ms=timeout_ms,
            poll_ms=poll_ms,
            validator=lambda snapshot: int(snapshot.get("addr", -1)) == dst_short_addr,
        )
        if node_snapshot is None:
            _on_error("timeout waiting for node_descriptor snapshot")
        else:
            result["node_descriptor"] = node_snapshot

        for endpoint_id in result["endpoint_ids"]:
            self.request_simple_descriptor(dst_short_addr, endpoint_id)
            simple_snapshot = self._poll_snapshot(
                self.get_simple_descriptor_snapshot,
                timeout_ms=timeout_ms,
                poll_ms=poll_ms,
                validator=lambda snapshot, _ep=endpoint_id: int(snapshot.get("addr", -1)) == dst_short_addr
                and (
                    snapshot.get("simple_desc") is None
                    or int(snapshot["simple_desc"].get("endpoint", -1)) == int(_ep)
                ),
            )
            if simple_snapshot is None:
                _on_error("timeout waiting for simple_descriptor snapshot for endpoint {}".format(int(endpoint_id)))
                continue
            result["simple_descriptors"].append(
                {
                    "endpoint": int(endpoint_id),
                    "snapshot": simple_snapshot,
                }
            )

        if include_power_desc:
            self.request_power_descriptor(dst_short_addr)
            power_snapshot = self._poll_snapshot(
                self.get_power_descriptor_snapshot,
                timeout_ms=timeout_ms,
                poll_ms=poll_ms,
                validator=lambda snapshot: int(snapshot.get("addr", -1)) == dst_short_addr,
            )
            if power_snapshot is None:
                _on_error("timeout waiting for power_descriptor snapshot")
            else:
                result["power_descriptor"] = power_snapshot

        return result

    def permit_join(self, duration_s=60):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.permit_join(int(duration_s))

    def set_primary_channel_mask(self, channel_mask):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_primary_channel_mask"):
            raise ZigbeeError("set_primary_channel_mask not available in firmware")
        return _uzigbee.set_primary_channel_mask(int(channel_mask))

    def set_primary_channel(self, channel):
        channel = int(channel)
        if channel < 11 or channel > 26:
            raise ValueError("channel must be in range 11..26")
        return self.set_primary_channel_mask(1 << channel)

    def set_pan_id(self, pan_id):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_pan_id"):
            raise ZigbeeError("set_pan_id not available in firmware")
        pan_id = int(pan_id)
        if pan_id <= 0 or pan_id >= 0xFFFF:
            raise ValueError("pan_id must be in range 0x0001..0xFFFE")
        return _uzigbee.set_pan_id(pan_id)

    def set_extended_pan_id(self, ext_pan_id):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "set_extended_pan_id"):
            raise ZigbeeError("set_extended_pan_id not available in firmware")
        if isinstance(ext_pan_id, str):
            compact = ext_pan_id.strip().lower().replace(":", "").replace("-", "").replace(" ", "")
            if len(compact) != 16:
                raise ValueError("extended pan id hex string must have 16 chars")
            try:
                ext_pan_id = bytes.fromhex(compact)
            except Exception:
                raise ValueError("invalid extended pan id hex string")
        try:
            ext_pan_id = bytes(ext_pan_id)
        except Exception:
            raise ValueError("extended pan id must be bytes-like or hex string")
        if len(ext_pan_id) != 8:
            raise ValueError("extended pan id must be 8 bytes")
        return _uzigbee.set_extended_pan_id(ext_pan_id)

    def enable_wifi_i154_coex(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "enable_wifi_i154_coex"):
            raise ZigbeeError("enable_wifi_i154_coex not available in firmware")
        return _uzigbee.enable_wifi_i154_coex()

    def start_network_steering(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "start_network_steering"):
            raise ZigbeeError("start_network_steering not available in firmware")
        return _uzigbee.start_network_steering()

    def get_short_addr(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.get_short_addr()

    def get_last_joined_short_addr(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_last_joined_short_addr"):
            raise ZigbeeError("get_last_joined_short_addr not available in firmware")
        return _uzigbee.get_last_joined_short_addr()

    def get_ieee_addr(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.get_ieee_addr()

    def get_network_runtime(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_network_runtime"):
            raise ZigbeeError("get_network_runtime not available in firmware")
        raw = _uzigbee.get_network_runtime()
        if raw is None or len(raw) < 6:
            raise ZigbeeError("invalid get_network_runtime response")
        channel = int(raw[0]) & 0xFF
        pan_id = int(raw[1]) & 0xFFFF
        ext_pan_id = bytes(raw[2])
        if len(ext_pan_id) != 8:
            raise ZigbeeError("invalid extended_pan_id length in get_network_runtime response")
        short_addr = int(raw[3]) & 0xFFFF
        formed = bool(raw[4])
        joined = bool(raw[5])
        ext_pan_hex = "".join("{:02x}".format(int(b) & 0xFF) for b in ext_pan_id)
        return {
            "channel": channel,
            "pan_id": pan_id,
            "extended_pan_id": ext_pan_id,
            "extended_pan_id_hex": ext_pan_hex,
            "short_addr": short_addr,
            "formed": formed,
            "joined": joined,
        }

    def set_signal_callback(self, callback=None):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        return _uzigbee.set_signal_callback(callback)

    def on_signal(self, callback=None):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "on_signal"):
            return _uzigbee.on_signal(callback)
        return _uzigbee.set_signal_callback(callback)

    def set_attribute_callback(self, callback=None):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "set_attribute_callback"):
            return _uzigbee.set_attribute_callback(callback)
        return None

    def on_attribute(self, callback=None):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if hasattr(_uzigbee, "on_attribute"):
            return _uzigbee.on_attribute(callback)
        return self.set_attribute_callback(callback)

    def event_stats(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        stats = _uzigbee.get_event_stats()
        return {
            "enqueued": stats[0],
            "dropped_queue_full": stats[1],
            "dropped_schedule_fail": stats[2],
            "dispatched": stats[3],
            "max_depth": stats[4],
            "depth": stats[5],
        }

    def heap_stats(self):
        if _uzigbee is None:
            raise ZigbeeError("_uzigbee C module not available")
        if not hasattr(_uzigbee, "get_heap_stats"):
            raise ZigbeeError("get_heap_stats not available in firmware")
        stats = _uzigbee.get_heap_stats()
        return {
            "free_8bit": stats[0],
            "min_free_8bit": stats[1],
            "largest_free_8bit": stats[2],
            "free_internal": stats[3],
        }

    @property
    def short_address(self):
        return self.get_short_addr()

    @property
    def ieee_address(self):
        return self.get_ieee_addr()


class Attribute:
    __slots__ = ("attr_id", "value", "data_type")

    def __init__(self, attr_id, value=None, data_type=None):
        self.attr_id = attr_id
        self.value = value
        self.data_type = data_type


class Cluster:
    __slots__ = ("cluster_id", "attributes")

    def __init__(self, cluster_id):
        self.cluster_id = cluster_id
        self.attributes = {}

    def add_attribute(self, attr):
        self.attributes[attr.attr_id] = attr
        return attr


class Endpoint:
    __slots__ = (
        "endpoint_id",
        "profile_id",
        "device_id",
        "input_clusters",
        "output_clusters",
    )

    def __init__(self, endpoint_id, profile_id, device_id):
        self.endpoint_id = endpoint_id
        self.profile_id = profile_id
        self.device_id = device_id
        self.input_clusters = []
        self.output_clusters = []

    def add_input_cluster(self, cluster):
        self.input_clusters.append(cluster)
        return cluster

    def add_output_cluster(self, cluster):
        self.output_clusters.append(cluster)
        return cluster


# Common profile IDs
PROFILE_ID_ZHA = const(0x0104)
DEVICE_ID_ON_OFF_LIGHT = const(0x0100)
