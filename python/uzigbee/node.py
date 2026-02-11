"""High-level local node API for Router and EndDevice roles."""

import time
try:
    import ujson as json
except ImportError:
    import json

from .core import (
    ATTR_DOOR_LOCK_LOCK_STATE,
    ATTR_IAS_ZONE_IAS_CIE_ADDRESS,
    ATTR_LEVEL_CONTROL_CURRENT_LEVEL,
    ATTR_ON_OFF_ON_OFF,
    ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
    ATTR_THERMOSTAT_SYSTEM_MODE,
    ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE,
    ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE,
    CLUSTER_ID_COLOR_CONTROL,
    CLUSTER_ID_DOOR_LOCK,
    CLUSTER_ID_IAS_ZONE,
    CLUSTER_ID_LEVEL_CONTROL,
    CLUSTER_ID_OCCUPANCY_SENSING,
    CLUSTER_ID_ON_OFF,
    CLUSTER_ID_PRESSURE_MEASUREMENT,
    CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
    CLUSTER_ID_TEMP_MEASUREMENT,
    CLUSTER_ID_THERMOSTAT,
    CLUSTER_ID_WINDOW_COVERING,
    CLUSTER_ID_ELECTRICAL_MEASUREMENT,
    IAS_ZONE_TYPE_CONTACT_SWITCH,
    SIGNAL_DEVICE_FIRST_START,
    SIGNAL_FORMATION,
    SIGNAL_PANID_CONFLICT_DETECTED,
    SIGNAL_DEVICE_REBOOT,
    SIGNAL_STEERING,
    SIGNAL_STEERING_CANCELLED,
    ZigbeeError,
    ZigbeeStack,
)
from .reporting import (
    PRESET_CONTACT_SENSOR,
    PRESET_DOOR_LOCK,
    PRESET_MOTION_SENSOR,
    PRESET_OCCUPANCY,
    PRESET_THERMOSTAT,
)
from .commissioning import (
    NETWORK_MODE_AUTO,
    NETWORK_MODE_FIXED,
    NETWORK_MODE_GUIDED,
    NetworkProfile,
    infer_mode as _infer_commissioning_mode,
    mode_profile_source as _mode_profile_source,
)

ROLE_ROUTER = 1
ROLE_END_DEVICE = 2
ESP_ERR_INVALID_STATE = 259
_CHANNEL_MASK_ALLOWED = 0
for _ch in range(11, 27):
    _CHANNEL_MASK_ALLOWED |= 1 << _ch
_DEFAULT_AUTO_JOIN_CHANNEL_MASK = _CHANNEL_MASK_ALLOWED
_JOIN_RETRY_MAX_DEFAULT = 4
_JOIN_RETRY_BASE_MS_DEFAULT = 25
_JOIN_RETRY_MAX_BACKOFF_MS_DEFAULT = 400
_JOIN_PROFILE_SYNC_SIGNALS = (
    int(SIGNAL_STEERING),
    int(SIGNAL_DEVICE_FIRST_START),
    int(SIGNAL_DEVICE_REBOOT),
)
_SELF_HEAL_STEERING_SIGNALS = (
    int(SIGNAL_STEERING),
    int(SIGNAL_STEERING_CANCELLED),
)
_SELF_HEAL_RETRY_MAX_DEFAULT = 2
_SELF_HEAL_RETRY_BASE_MS_DEFAULT = 100
_SELF_HEAL_RETRY_MAX_BACKOFF_MS_DEFAULT = 1000
_COMMISSIONING_TIMEOUT_STATUSES = (110, 116, -110, -116)

_ENDPOINT_MIN = 1
_ENDPOINT_MAX = 239

_CAPABILITY_TEMPLATES = {
    "light": {"kind": "light", "create_method": "create_on_off_light"},
    "dimmable_light": {"kind": "dimmable_light", "create_method": "create_dimmable_light"},
    "color_light": {"kind": "color_light", "create_method": "create_color_light"},
    "switch": {"kind": "switch", "create_method": "create_on_off_switch"},
    "dimmable_switch": {"kind": "dimmable_switch", "create_method": "create_dimmable_switch"},
    "temperature_sensor": {"kind": "temperature_sensor", "create_method": "create_temperature_sensor"},
    "humidity_sensor": {"kind": "humidity_sensor", "create_method": "create_humidity_sensor"},
    "pressure_sensor": {"kind": "pressure_sensor", "create_method": "create_pressure_sensor"},
    "climate_sensor": {"kind": "climate_sensor", "create_method": "create_climate_sensor"},
    "occupancy_sensor": {"kind": "occupancy_sensor", "create_method": "create_occupancy_sensor"},
    "contact_sensor": {"kind": "contact_sensor", "create_method": "create_contact_sensor"},
    "motion_sensor": {"kind": "motion_sensor", "create_method": "create_motion_sensor"},
    "power_outlet": {"kind": "power_outlet", "create_method": "create_power_outlet"},
    "door_lock": {"kind": "door_lock", "create_method": "create_door_lock"},
    "thermostat": {"kind": "thermostat", "create_method": "create_thermostat"},
    "window_covering": {"kind": "window_covering", "create_method": "create_window_covering"},
    "ias_zone": {"kind": "ias_zone", "create_method": "create_ias_zone"},
}

_CANONICAL_CAPABILITIES = (
    "light",
    "switch",
    "temperature_sensor",
    "humidity_sensor",
    "pressure_sensor",
    "climate_sensor",
    "occupancy_sensor",
    "contact_sensor",
    "motion_sensor",
    "power_outlet",
    "door_lock",
    "thermostat",
    "window_covering",
    "ias_zone",
)

_CAPABILITY_ALIASES = {
    "temperature": "temperature_sensor",
    "temp_sensor": "temperature_sensor",
    "humidity": "humidity_sensor",
    "pressure": "pressure_sensor",
    "occupancy": "occupancy_sensor",
    "contact": "contact_sensor",
    "motion": "motion_sensor",
    "outlet": "power_outlet",
    "plug": "power_outlet",
    "cover": "window_covering",
    "lock": "door_lock",
    "ias": "ias_zone",
}

_UPDATE_CAPABILITY_ALIASES = {
    "temperature": "temperature",
    "temp": "temperature",
    "temp_sensor": "temperature",
    "temperature_sensor": "temperature",
    "humidity": "humidity",
    "humidity_sensor": "humidity",
    "pressure": "pressure",
    "pressure_sensor": "pressure",
    "occupancy": "occupancy",
    "occupancy_sensor": "occupancy",
    "contact": "contact",
    "contact_sensor": "contact",
    "motion": "motion",
    "motion_sensor": "motion",
    "ias": "ias_zone",
    "ias_zone": "ias_zone",
    "climate": "climate",
    "climate_sensor": "climate",
}

_UPDATE_ALLOWED_KINDS = {
    "temperature": ("temperature_sensor", "climate_sensor"),
    "humidity": ("humidity_sensor", "climate_sensor"),
    "pressure": ("pressure_sensor", "climate_sensor"),
    "occupancy": ("occupancy_sensor",),
    "contact": ("contact_sensor",),
    "motion": ("motion_sensor",),
    "ias_zone": ("ias_zone",),
    "climate": ("climate_sensor",),
}

_ACTUATOR_ON_OFF_KINDS = (
    "light",
    "dimmable_light",
    "color_light",
    "switch",
    "dimmable_switch",
    "power_outlet",
)

_ACTUATOR_LEVEL_KINDS = (
    "dimmable_light",
    "color_light",
    "dimmable_switch",
)

_ACTUATOR_LOCK_KINDS = ("door_lock",)
_ACTUATOR_COVER_KINDS = ("window_covering",)
_ACTUATOR_THERMOSTAT_KINDS = ("thermostat",)
_ACTUATOR_KINDS = (
    _ACTUATOR_ON_OFF_KINDS
    + _ACTUATOR_LEVEL_KINDS
    + _ACTUATOR_LOCK_KINDS
    + _ACTUATOR_COVER_KINDS
    + _ACTUATOR_THERMOSTAT_KINDS
)

_THERMOSTAT_MODE_MAP = {
    "off": 0,
    "auto": 1,
    "cool": 3,
    "heat": 4,
    "emergency_heat": 5,
    "pre_cooling": 6,
    "fan_only": 7,
}

_REPORTING_PRESET_BY_KIND = {
    "door_lock": PRESET_DOOR_LOCK,
    "thermostat": PRESET_THERMOSTAT,
    "occupancy_sensor": PRESET_OCCUPANCY,
    "contact_sensor": PRESET_CONTACT_SENSOR,
    "motion_sensor": PRESET_MOTION_SENSOR,
    "ias_zone": PRESET_CONTACT_SENSOR,
}

_REPORTING_PRESET_BY_NAME = {
    "door_lock": PRESET_DOOR_LOCK,
    "thermostat": PRESET_THERMOSTAT,
    "occupancy": PRESET_OCCUPANCY,
    "occupancy_sensor": PRESET_OCCUPANCY,
    "contact": PRESET_CONTACT_SENSOR,
    "contact_sensor": PRESET_CONTACT_SENSOR,
    "motion": PRESET_MOTION_SENSOR,
    "motion_sensor": PRESET_MOTION_SENSOR,
    "ias_zone": PRESET_CONTACT_SENSOR,
}

_REPORTING_CAPABILITY_KIND_MAP = {
    "door_lock": ("door_lock",),
    "thermostat": ("thermostat",),
    "occupancy": ("occupancy_sensor",),
    "occupancy_sensor": ("occupancy_sensor",),
    "contact": ("contact_sensor", "ias_zone"),
    "contact_sensor": ("contact_sensor",),
    "motion": ("motion_sensor", "ias_zone"),
    "motion_sensor": ("motion_sensor",),
    "ias_zone": ("ias_zone",),
}

_BIND_DEFAULT_CLUSTERS_BY_KIND = {
    "light": (CLUSTER_ID_ON_OFF,),
    "dimmable_light": (CLUSTER_ID_ON_OFF, CLUSTER_ID_LEVEL_CONTROL),
    "color_light": (CLUSTER_ID_ON_OFF, CLUSTER_ID_LEVEL_CONTROL, CLUSTER_ID_COLOR_CONTROL),
    "switch": (CLUSTER_ID_ON_OFF,),
    "dimmable_switch": (CLUSTER_ID_ON_OFF, CLUSTER_ID_LEVEL_CONTROL),
    "power_outlet": (CLUSTER_ID_ON_OFF, CLUSTER_ID_ELECTRICAL_MEASUREMENT),
    "door_lock": (CLUSTER_ID_DOOR_LOCK,),
    "thermostat": (CLUSTER_ID_THERMOSTAT,),
    "window_covering": (CLUSTER_ID_WINDOW_COVERING,),
    "occupancy_sensor": (CLUSTER_ID_OCCUPANCY_SENSING,),
    "contact_sensor": (CLUSTER_ID_IAS_ZONE,),
    "motion_sensor": (CLUSTER_ID_IAS_ZONE,),
    "ias_zone": (CLUSTER_ID_IAS_ZONE,),
    "temperature_sensor": (CLUSTER_ID_TEMP_MEASUREMENT,),
    "humidity_sensor": (CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,),
    "pressure_sensor": (CLUSTER_ID_PRESSURE_MEASUREMENT,),
    "climate_sensor": (
        CLUSTER_ID_TEMP_MEASUREMENT,
        CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
        CLUSTER_ID_PRESSURE_MEASUREMENT,
    ),
}

_BIND_CAPABILITY_KIND_MAP = {
    "light": ("light", "dimmable_light", "color_light"),
    "switch": ("switch", "dimmable_switch"),
    "power_outlet": ("power_outlet",),
    "door_lock": ("door_lock",),
    "thermostat": ("thermostat",),
    "window_covering": ("window_covering",),
    "cover": ("window_covering",),
    "occupancy": ("occupancy_sensor",),
    "occupancy_sensor": ("occupancy_sensor",),
    "contact": ("contact_sensor", "ias_zone"),
    "contact_sensor": ("contact_sensor",),
    "motion": ("motion_sensor", "ias_zone"),
    "motion_sensor": ("motion_sensor",),
    "ias_zone": ("ias_zone",),
    "temperature": ("temperature_sensor", "climate_sensor"),
    "temperature_sensor": ("temperature_sensor",),
    "humidity": ("humidity_sensor", "climate_sensor"),
    "humidity_sensor": ("humidity_sensor",),
    "pressure": ("pressure_sensor", "climate_sensor"),
    "pressure_sensor": ("pressure_sensor",),
    "climate": ("climate_sensor",),
    "climate_sensor": ("climate_sensor",),
}


def _ignore_invalid_state(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except OSError as exc:
        if exc.args and int(exc.args[0]) == ESP_ERR_INVALID_STATE:
            return None
        raise


def _ignore_invalid_state_or_steering_busy(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        return True
    except OSError as exc:
        if exc.args:
            code = int(exc.args[0])
            if code == ESP_ERR_INVALID_STATE or code == -1:
                return False
        raise


def _normalize_endpoint(endpoint_id):
    endpoint_id = int(endpoint_id)
    if endpoint_id < _ENDPOINT_MIN or endpoint_id > _ENDPOINT_MAX:
        raise ValueError("invalid endpoint id: {}".format(endpoint_id))
    return endpoint_id


def _normalize_channel_mask(channel=None, channel_mask=None):
    if channel is not None and channel_mask is not None:
        raise ValueError("use either channel or channel_mask")
    if channel is not None:
        channel = int(channel)
        if channel < 11 or channel > 26:
            raise ValueError("channel must be in range 11..26")
        return int(1 << channel)
    if channel_mask is None:
        return None
    channel_mask = int(channel_mask)
    if channel_mask <= 0:
        raise ValueError("invalid channel_mask")
    if (channel_mask & ~_CHANNEL_MASK_ALLOWED) != 0:
        raise ValueError("channel_mask must include only channels 11..26")
    return int(channel_mask)


def _channels_from_mask(channel_mask):
    channel_mask = int(channel_mask)
    if channel_mask <= 0:
        return ()
    channels = []
    for channel in range(11, 27):
        if channel_mask & (1 << channel):
            channels.append(int(channel))
    return tuple(channels)


def _normalize_pan_id(pan_id):
    if pan_id is None:
        return None
    pan_id = int(pan_id)
    if pan_id <= 0 or pan_id >= 0xFFFF:
        raise ValueError("pan_id must be in range 0x0001..0xFFFE")
    return int(pan_id)


def _normalize_capability_name(capability):
    return str(capability).strip().lower().replace("-", "_").replace(" ", "_")


def _supported_capabilities_str():
    return ", ".join(_CANONICAL_CAPABILITIES)


def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return int(time.ticks_ms())
    return int(time.time() * 1000)


def _sleep_ms(ms):
    ms = int(ms)
    if ms <= 0:
        return
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
        return
    time.sleep(ms / 1000.0)


def _is_timeout_status(status):
    try:
        status = int(status)
    except Exception:
        return False
    return bool(status in _COMMISSIONING_TIMEOUT_STATUSES)


def _new_commissioning_stats():
    return {
        "start_count": 0,
        "last_start_ms": 0,
        "form_attempts": 0,
        "form_success": 0,
        "form_failures": 0,
        "join_attempts": 0,
        "join_success": 0,
        "join_failures": 0,
        "timeout_events": 0,
        "conflict_events": 0,
        "last_signal": None,
        "last_status": None,
        "last_event_ms": 0,
        "form_started_ms": None,
        "join_started_ms": None,
        "last_form_success_ms": 0,
        "last_join_success_ms": 0,
        "time_to_form_ms": None,
        "time_to_join_ms": None,
    }


def _clamp_int(value, min_value, max_value):
    value = int(value)
    if value < int(min_value):
        return int(min_value)
    if value > int(max_value):
        return int(max_value)
    return int(value)


def _coerce_float(value, label):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError("invalid {} value".format(label))


def _coerce_bool(value, label):
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    raise ValueError("invalid {} value".format(label))


def _normalize_temperature(value):
    celsius = _coerce_float(value, "temperature")
    if celsius < -50.0 or celsius > 150.0:
        raise ValueError("temperature out of range: {}".format(celsius))
    return celsius, int(round(celsius * 100.0))


def _normalize_humidity(value):
    humidity = _coerce_float(value, "humidity")
    if humidity < 0.0 or humidity > 100.0:
        raise ValueError("humidity out of range: {}".format(humidity))
    return humidity, int(round(humidity * 100.0))


def _normalize_pressure(value):
    pressure_hpa = _coerce_float(value, "pressure")
    if pressure_hpa < 300.0 or pressure_hpa > 1300.0:
        raise ValueError("pressure out of range: {}".format(pressure_hpa))
    return pressure_hpa, int(round(pressure_hpa))


def _normalize_binary(value, label):
    binary = _coerce_bool(value, label)
    return binary, int(binary)


def _normalize_ias_zone(value):
    if isinstance(value, bool):
        raw = int(value)
        return bool(raw), raw
    if isinstance(value, int) and value >= 0:
        return bool(int(value) & 0x0001), int(value)
    raise ValueError("invalid ias_zone value")


def _normalize_climate(value):
    if not isinstance(value, dict):
        raise ValueError("invalid climate payload")
    normalized = {}
    raw = {}
    if "temperature" in value:
        normalized["temperature"], raw["temperature"] = _normalize_temperature(value["temperature"])
    if "humidity" in value:
        normalized["humidity"], raw["humidity"] = _normalize_humidity(value["humidity"])
    if "pressure" in value:
        normalized["pressure"], raw["pressure"] = _normalize_pressure(value["pressure"])
    if not normalized:
        raise ValueError("climate payload must include at least one key")
    return normalized, raw


def _normalize_level(value):
    level = int(value)
    if level < 0 or level > 254:
        raise ValueError("level out of range: {}".format(level))
    return level, level


def _normalize_percent(value, label):
    percent = int(value)
    if percent < 0 or percent > 100:
        raise ValueError("{} out of range: {}".format(label, percent))
    return percent, percent


def _normalize_thermostat_mode(value):
    if isinstance(value, str):
        mode_key = _normalize_capability_name(value)
        if mode_key not in _THERMOSTAT_MODE_MAP:
            raise ValueError("invalid thermostat mode '{}'".format(value))
        mode = int(_THERMOSTAT_MODE_MAP[mode_key])
        return mode, mode
    mode = int(value)
    if mode < 0 or mode > 7:
        raise ValueError("invalid thermostat mode '{}'".format(value))
    return mode, mode


def _normalize_thermostat_setpoint(value):
    celsius = _coerce_float(value, "thermostat_heating_setpoint")
    if celsius < 5.0 or celsius > 35.0:
        raise ValueError("thermostat setpoint out of range: {}".format(celsius))
    return celsius, int(round(celsius * 100.0))


def _normalize_reporting_entry(entry):
    if isinstance(entry, dict):
        cluster_id = int(entry["cluster_id"])
        attr_id = int(entry["attr_id"])
        attr_type = int(entry["attr_type"])
        min_interval = int(entry.get("min_interval", 0))
        max_interval = int(entry.get("max_interval", 300))
        reportable_change = entry.get("reportable_change", None)
        if reportable_change is not None:
            reportable_change = int(reportable_change)
        return (
            cluster_id,
            attr_id,
            attr_type,
            min_interval,
            max_interval,
            reportable_change,
        )
    if not isinstance(entry, (tuple, list)) or len(entry) < 6:
        raise ValueError("reporting entry must have 6 fields")
    return (
        int(entry[0]),
        int(entry[1]),
        int(entry[2]),
        int(entry[3]),
        int(entry[4]),
        None if entry[5] is None else int(entry[5]),
    )


def _normalize_reporting_entries(entries):
    out = []
    for item in tuple(entries):
        out.append(_normalize_reporting_entry(item))
    return tuple(out)


def _merge_reporting_entries(base_entries, overrides):
    merged = {}
    order = []
    for entry in tuple(base_entries):
        key = (int(entry[0]), int(entry[1]))
        merged[key] = _normalize_reporting_entry(entry)
        order.append(key)
    for entry in _normalize_reporting_entries(overrides):
        key = (int(entry[0]), int(entry[1]))
        if key not in merged:
            order.append(key)
        merged[key] = entry
    out = []
    for key in tuple(order):
        out.append(merged[key])
    return tuple(out)


def _tune_low_power_reporting_entries(entries):
    tuned = []
    for entry in tuple(entries):
        cluster_id, attr_id, attr_type, min_interval, max_interval, reportable_change = _normalize_reporting_entry(entry)
        tuned_min = max(int(min_interval), 30)
        tuned_max = max(int(max_interval), 900)
        if tuned_max < tuned_min:
            tuned_max = tuned_min
        tuned.append((cluster_id, attr_id, attr_type, tuned_min, tuned_max, reportable_change))
    return tuple(tuned)


def _normalize_ieee_addr(value):
    if isinstance(value, str):
        parts = []
        for ch in value:
            if ch in ":-":
                continue
            parts.append(ch)
        hex_str = "".join(parts)
        if len(hex_str) != 16:
            raise ValueError("ieee address hex string must have 16 chars")
        try:
            return bytes.fromhex(hex_str)
        except Exception:
            raise ValueError("invalid ieee address hex string")
    ieee_addr = bytes(value)
    if len(ieee_addr) != 8:
        raise ValueError("ieee address must be 8 bytes")
    return ieee_addr


def _normalize_cluster_ids(clusters):
    out = []
    for cluster_id in tuple(clusters):
        out.append(int(cluster_id))
    return tuple(out)


def _ieee_to_hex(value):
    if value is None:
        return None
    return "".join("{:02x}".format(int(b)) for b in bytes(value))


class EndpointBuilder:
    """Declarative endpoint planner with capability templates."""

    __slots__ = ("node",)

    def __init__(self, node):
        self.node = node

    def _resolve_template(self, capability, options):
        options = dict(options or {})
        capability_key = _normalize_capability_name(capability)
        capability_key = self.node._custom_capability_aliases.get(capability_key, capability_key)
        capability_key = _CAPABILITY_ALIASES.get(capability_key, capability_key)

        custom_template = self.node._custom_capability_templates.get(capability_key, None)
        if custom_template is not None:
            return custom_template["kind"], custom_template["create_method"], dict(options)

        if capability_key == "light":
            color = bool(options.pop("color", False))
            dimmable = bool(options.pop("dimmable", False))
            if color:
                capability_key = "color_light"
            elif dimmable:
                capability_key = "dimmable_light"
        elif capability_key == "switch":
            if bool(options.pop("dimmable", False)):
                capability_key = "dimmable_switch"

        template = _CAPABILITY_TEMPLATES.get(capability_key)
        if template is None:
            raise ValueError(
                "unsupported capability '{}'; supported: {}".format(
                    capability, _supported_capabilities_str()
                )
            )

        create_options = {}
        if capability_key == "power_outlet":
            create_options["with_metering"] = bool(options.pop("with_metering", False))
        elif capability_key == "ias_zone":
            create_options["zone_type"] = int(options.pop("zone_type", IAS_ZONE_TYPE_CONTACT_SWITCH))

        if options:
            keys = ", ".join(sorted(options.keys()))
            raise ValueError(
                "unsupported options for capability '{}': {}".format(capability_key, keys)
            )

        return template["kind"], template["create_method"], create_options

    def add(self, capability, endpoint_id=None, name=None, **options):
        kind, create_method, create_options = self._resolve_template(capability, options)
        return self.node._add_component(
            kind,
            create_method,
            endpoint_id=endpoint_id,
            name=name,
            **create_options
        )

    def add_all(self, definitions):
        for item in tuple(definitions):
            if isinstance(item, str):
                self.add(item)
                continue
            if not isinstance(item, dict):
                raise TypeError("endpoint definition must be str or dict")
            capability = item.get("capability", item.get("kind"))
            if capability is None:
                raise ValueError("endpoint definition missing 'capability'")
            endpoint_id = item.get("endpoint_id", None)
            name = item.get("name", None)
            options = item.get("options", None)
            if options is None:
                options = {}
            if not isinstance(options, dict):
                raise TypeError("endpoint definition 'options' must be dict")
            options = dict(options)
            for key, value in item.items():
                if key in ("capability", "kind", "endpoint_id", "name", "options"):
                    continue
                options[key] = value
            self.add(capability, endpoint_id=endpoint_id, name=name, **options)
        return self.node

    def capabilities(self):
        out = []
        for name in _CANONICAL_CAPABILITIES:
            out.append(name)
        for name in self.node._custom_capability_templates.keys():
            if name not in out:
                out.append(name)
        return tuple(out)


class ActuatorProxy:
    """Per-component actuator control facade with local idempotent mirror."""

    __slots__ = ("_node", "_component")

    def __init__(self, node, component):
        self._node = node
        self._component = dict(component)

    @property
    def name(self):
        return self._component["name"]

    @property
    def kind(self):
        return self._component["kind"]

    @property
    def endpoint_id(self):
        return int(self._component["endpoint_id"])

    def _assert_kind(self, allowed_kinds, action):
        if self.kind not in allowed_kinds:
            raise ValueError(
                "action '{}' not supported for actor '{}' ({})".format(
                    action, self.name, self.kind
                )
            )

    def _set(self, field, value, raw_value=None, timestamp_ms=None):
        return self._node._set_actuator_state(
            endpoint_id=self.endpoint_id,
            actor_name=self.name,
            capability=self.kind,
            field=field,
            value=value,
            raw_value=raw_value,
            timestamp_ms=timestamp_ms,
        )

    def state(self, field=None, default=None):
        return self._node.actuator_state(self.name, field=field, default=default)

    def on(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_ON_OFF_KINDS, "on")
        value, raw = _normalize_binary(True, "on")
        return self._set("on_off", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def off(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_ON_OFF_KINDS, "off")
        value, raw = _normalize_binary(False, "off")
        return self._set("on_off", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def toggle(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_ON_OFF_KINDS, "toggle")
        current = self.state(field="on_off", default=None)
        current_value = False
        if current is not None:
            current_value = bool(current["value"])
        value, raw = _normalize_binary(not current_value, "toggle")
        return self._set("on_off", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def level(self, level, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_LEVEL_KINDS, "level")
        value, raw = _normalize_level(level)
        return self._set("level", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def lock(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_LOCK_KINDS, "lock")
        value, raw = _normalize_binary(True, "lock")
        return self._set("locked", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def unlock(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_LOCK_KINDS, "unlock")
        value, raw = _normalize_binary(False, "unlock")
        return self._set("locked", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def cover(self, percent, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_COVER_KINDS, "cover")
        value, raw = _normalize_percent(percent, "cover")
        return self._set("cover_lift_percent", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def cover_lift(self, percent, timestamp_ms=None):
        return self.cover(percent, timestamp_ms=timestamp_ms)

    def cover_tilt(self, percent, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_COVER_KINDS, "cover_tilt")
        value, raw = _normalize_percent(percent, "cover_tilt")
        return self._set("cover_tilt_percent", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def open(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_COVER_KINDS, "open")
        return self._set("cover_command", "open", raw_value=0, timestamp_ms=timestamp_ms)

    def close(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_COVER_KINDS, "close")
        return self._set("cover_command", "close", raw_value=1, timestamp_ms=timestamp_ms)

    def stop(self, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_COVER_KINDS, "stop")
        return self._set("cover_command", "stop", raw_value=2, timestamp_ms=timestamp_ms)

    def thermostat_mode(self, mode, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_THERMOSTAT_KINDS, "thermostat_mode")
        value, raw = _normalize_thermostat_mode(mode)
        return self._set("thermostat_mode", value, raw_value=raw, timestamp_ms=timestamp_ms)

    def thermostat_heating_setpoint(self, celsius, timestamp_ms=None):
        self._assert_kind(_ACTUATOR_THERMOSTAT_KINDS, "thermostat_heating_setpoint")
        value, raw = _normalize_thermostat_setpoint(celsius)
        return self._set("thermostat_heating_setpoint", value, raw_value=raw, timestamp_ms=timestamp_ms)


class _NodeBase:
    __slots__ = (
        "stack",
        "role",
        "auto_register",
        "_endpoint_plan",
        "_used_endpoints",
        "_registered",
        "_started",
        "_on_signal_cb",
        "_on_attribute_cb",
        "_last_signal",
        "_last_status",
        "_endpoint_builder",
        "_sensor_state",
        "_actuator_state",
        "_onoff_outputs",
        "_reporting_policies",
        "_binding_policies",
        "_persistence_min_interval_ms",
        "_persistence_last_save_ms",
        "_channel_mask",
        "_pan_id",
        "_extended_pan_id",
        "_auto_join_channel_mask",
        "commissioning_mode",
        "_join_retry_max",
        "_join_retry_base_ms",
        "_join_retry_max_backoff_ms",
        "_join_trigger_count",
        "_join_last_attempt_ms",
        "_join_last_backoff_ms",
        "_join_last_trigger_ok",
        "_self_heal_enabled",
        "_self_heal_retry_max",
        "_self_heal_retry_base_ms",
        "_self_heal_retry_max_backoff_ms",
        "_commissioning_event_cb",
        "_commissioning_stats",
        "_self_heal_stats",
        "_self_heal_inflight",
        "_network_profile",
        "_form_network",
        "_custom_capability_templates",
        "_custom_capability_aliases",
        "_policy_hooks",
    )

    def __init__(
        self,
        role,
        stack=None,
        auto_register=True,
        channel=None,
        channel_mask=None,
        auto_join_channel_mask=_DEFAULT_AUTO_JOIN_CHANNEL_MASK,
        pan_id=None,
        extended_pan_id=None,
        commissioning_mode="auto",
        join_retry_max=_JOIN_RETRY_MAX_DEFAULT,
        join_retry_base_ms=_JOIN_RETRY_BASE_MS_DEFAULT,
        join_retry_max_backoff_ms=_JOIN_RETRY_MAX_BACKOFF_MS_DEFAULT,
        self_heal_enabled=True,
        self_heal_retry_max=_SELF_HEAL_RETRY_MAX_DEFAULT,
        self_heal_retry_base_ms=_SELF_HEAL_RETRY_BASE_MS_DEFAULT,
        self_heal_retry_max_backoff_ms=_SELF_HEAL_RETRY_MAX_BACKOFF_MS_DEFAULT,
    ):
        self.stack = stack if stack is not None else ZigbeeStack()
        self.role = int(role)
        self.auto_register = bool(auto_register)
        self._endpoint_plan = []
        self._used_endpoints = set()
        self._registered = False
        self._started = False
        self._on_signal_cb = None
        self._on_attribute_cb = None
        self._last_signal = None
        self._last_status = None
        self._endpoint_builder = EndpointBuilder(self)
        self._sensor_state = {}
        self._actuator_state = {}
        self._onoff_outputs = {}
        self._reporting_policies = {}
        self._binding_policies = {}
        self._persistence_min_interval_ms = 30000
        self._persistence_last_save_ms = 0
        channel_mask_value = _normalize_channel_mask(channel=channel, channel_mask=channel_mask)
        auto_join_channel_mask_value = _normalize_channel_mask(channel_mask=auto_join_channel_mask)
        pan_id_value = _normalize_pan_id(pan_id)
        extended_pan_id_value = None if extended_pan_id is None else _normalize_ieee_addr(extended_pan_id)
        self.commissioning_mode = _infer_commissioning_mode(
            commissioning_mode,
            channel_mask=channel_mask_value,
            pan_id=pan_id_value,
            extended_pan_id=extended_pan_id_value,
            label="commissioning_mode",
        )
        self._channel_mask = channel_mask_value
        self._pan_id = pan_id_value
        self._extended_pan_id = extended_pan_id_value
        self._auto_join_channel_mask = auto_join_channel_mask_value
        self._join_retry_max = _clamp_int(join_retry_max, 0, 10)
        self._join_retry_base_ms = _clamp_int(join_retry_base_ms, 0, 60000)
        self._join_retry_max_backoff_ms = _clamp_int(
            join_retry_max_backoff_ms,
            self._join_retry_base_ms,
            300000,
        )
        self._join_trigger_count = 0
        self._join_last_attempt_ms = 0
        self._join_last_backoff_ms = 0
        self._join_last_trigger_ok = None
        self._self_heal_enabled = bool(self_heal_enabled)
        self._self_heal_retry_max = _clamp_int(self_heal_retry_max, 0, 10)
        self._self_heal_retry_base_ms = _clamp_int(self_heal_retry_base_ms, 0, 60000)
        self._self_heal_retry_max_backoff_ms = _clamp_int(
            self_heal_retry_max_backoff_ms,
            self._self_heal_retry_base_ms,
            300000,
        )
        self._commissioning_event_cb = None
        self._commissioning_stats = _new_commissioning_stats()
        self._self_heal_stats = {
            "panid_conflicts": 0,
            "steering_failures": 0,
            "attempts": 0,
            "success": 0,
            "failed": 0,
            "guided_fallback_count": 0,
            "last_reason": None,
            "last_signal": None,
            "last_status": None,
            "last_attempt_ms": 0,
            "last_backoff_ms": 0,
            "last_result": None,
        }
        self._self_heal_inflight = False
        self._network_profile = NetworkProfile(
            channel_mask=self._channel_mask,
            pan_id=self._pan_id,
            extended_pan_id=self._extended_pan_id,
            source=_mode_profile_source(self.commissioning_mode),
            formed_at_ms=None,
        )
        self._form_network = False
        self._custom_capability_templates = {}
        self._custom_capability_aliases = {}
        self._policy_hooks = {}

    def _next_endpoint(self):
        for endpoint_id in range(_ENDPOINT_MIN, _ENDPOINT_MAX + 1):
            if endpoint_id not in self._used_endpoints:
                return endpoint_id
        raise ZigbeeError("no free endpoints left")

    def _reserve_endpoint(self, endpoint_id=None):
        if endpoint_id is None:
            endpoint_id = self._next_endpoint()
        endpoint_id = _normalize_endpoint(endpoint_id)
        if endpoint_id in self._used_endpoints:
            raise ValueError("endpoint {} already in use".format(endpoint_id))
        self._used_endpoints.add(endpoint_id)
        return endpoint_id

    def _add_component(self, kind, create_method, endpoint_id=None, name=None, **options):
        endpoint_id = self._reserve_endpoint(endpoint_id)
        if not name:
            name = "{}_{}".format(str(kind), endpoint_id)
        self._endpoint_plan.append(
            {
                "kind": str(kind),
                "name": str(name),
                "endpoint_id": int(endpoint_id),
                "create_method": str(create_method),
                "options": dict(options),
                "provisioned": False,
            }
        )
        return self

    def builder(self):
        return self._endpoint_builder

    def add(self, capability, endpoint_id=None, name=None, **options):
        return self._endpoint_builder.add(
            capability, endpoint_id=endpoint_id, name=name, **options
        )

    def add_all(self, definitions):
        return self._endpoint_builder.add_all(definitions)

    def capabilities(self):
        return self._endpoint_builder.capabilities()

    def register_capability(self, name, create_method, kind=None, aliases=()):
        capability_name = _normalize_capability_name(name)
        capability_kind = capability_name if kind is None else _normalize_capability_name(kind)
        self._custom_capability_templates[capability_name] = {
            "kind": str(capability_kind),
            "create_method": str(create_method),
        }
        alias_map = {}
        for alias in tuple(aliases):
            alias_key = _normalize_capability_name(alias)
            self._custom_capability_aliases[alias_key] = capability_name
            alias_map[alias_key] = capability_name
        return {
            "name": capability_name,
            "kind": capability_kind,
            "create_method": str(create_method),
            "aliases": tuple(alias_map.keys()),
        }

    def unregister_capability(self, name):
        capability_name = _normalize_capability_name(name)
        removed = 0
        if capability_name in self._custom_capability_templates:
            del self._custom_capability_templates[capability_name]
            removed += 1
        aliases_to_remove = []
        for alias_key, mapped in self._custom_capability_aliases.items():
            if mapped == capability_name:
                aliases_to_remove.append(alias_key)
        for alias_key in tuple(aliases_to_remove):
            del self._custom_capability_aliases[alias_key]
        return int(removed)

    def custom_capabilities(self):
        out = []
        for name, template in self._custom_capability_templates.items():
            aliases = []
            for alias_key, mapped in self._custom_capability_aliases.items():
                if mapped == name:
                    aliases.append(alias_key)
            out.append(
                {
                    "name": name,
                    "kind": template["kind"],
                    "create_method": template["create_method"],
                    "aliases": tuple(sorted(aliases)),
                }
            )
        out.sort(key=lambda row: row["name"])
        return tuple(out)

    def register_policy_hook(self, name, callback):
        if callback is None or not callable(callback):
            raise ValueError("policy hook callback must be callable")
        self._policy_hooks[str(name)] = callback
        return int(len(self._policy_hooks))

    def remove_policy_hook(self, name):
        name = str(name)
        if name in self._policy_hooks:
            del self._policy_hooks[name]
            return 1
        return 0

    def policy_hooks(self):
        out = []
        for name in self._policy_hooks.keys():
            out.append(str(name))
        out.sort()
        return tuple(out)

    def _invoke_policy_hooks(self, event, payload):
        event = str(event)
        payload = dict(payload)
        for callback in tuple(self._policy_hooks.values()):
            try:
                callback(event, payload)
            except TypeError:
                try:
                    callback(payload)
                except Exception:
                    pass
            except Exception:
                pass

    def _actuator_components(self):
        out = []
        for item in self._endpoint_plan:
            if item["kind"] not in _ACTUATOR_KINDS:
                continue
            out.append(item)
        out.sort(key=lambda row: int(row["endpoint_id"]))
        return tuple(out)

    def _resolve_actor_component(self, name=None):
        actors = self._actuator_components()
        if not actors:
            raise ValueError("no actuator components registered")

        if name is None:
            if len(actors) != 1:
                raise ValueError("actor is ambiguous; pass actor name or endpoint_id")
            return actors[0]

        endpoint_id = None
        if isinstance(name, int):
            endpoint_id = _normalize_endpoint(name)
        elif isinstance(name, str) and name.strip().isdigit():
            endpoint_id = _normalize_endpoint(int(name.strip()))

        matches = []
        for item in actors:
            if endpoint_id is not None:
                if int(item["endpoint_id"]) == int(endpoint_id):
                    matches.append(item)
                continue
            if item["name"] == str(name):
                matches.append(item)
                continue
            if item["kind"] == str(name):
                matches.append(item)
                continue

        if not matches:
            raise ValueError("actor '{}' not found".format(name))
        if len(matches) > 1:
            raise ValueError("actor '{}' is ambiguous".format(name))
        return matches[0]

    def actor(self, name=None):
        component = self._resolve_actor_component(name=name)
        return ActuatorProxy(self, component)

    def _component_by_endpoint(self, endpoint_id):
        endpoint_id = int(endpoint_id)
        for item in self._endpoint_plan:
            if int(item["endpoint_id"]) == endpoint_id:
                return item
        return None

    def bind_onoff_output(
        self,
        actor=None,
        endpoint_id=None,
        pin=None,
        active_high=True,
        initial=False,
        writer=None,
    ):
        if endpoint_id is None:
            component = self._resolve_actor_component(name=actor)
            endpoint_id = int(component["endpoint_id"])
        endpoint_id = _normalize_endpoint(endpoint_id)

        if writer is None:
            if pin is None:
                raise ValueError("pin is required when writer is not provided")
            try:
                import machine
            except Exception as exc:
                raise ZigbeeError("machine module unavailable: {}".format(exc))
            pin_obj = machine.Pin(int(pin), machine.Pin.OUT)
            active_high = bool(active_high)

            def _writer(value):
                value = bool(value)
                pin_obj.value(1 if (value if active_high else (not value)) else 0)

            writer = _writer
        else:
            if not callable(writer):
                raise ValueError("writer must be callable")

        self._onoff_outputs[int(endpoint_id)] = writer
        writer(bool(initial))
        return {
            "endpoint_id": int(endpoint_id),
            "pin": None if pin is None else int(pin),
            "active_high": bool(active_high),
            "initial": bool(initial),
        }

    def unbind_onoff_output(self, endpoint_id):
        endpoint_id = _normalize_endpoint(endpoint_id)
        if int(endpoint_id) in self._onoff_outputs:
            del self._onoff_outputs[int(endpoint_id)]
            return 1
        return 0

    def onoff_outputs(self):
        out = []
        for endpoint_id in self._onoff_outputs.keys():
            out.append(int(endpoint_id))
        out.sort()
        return tuple(out)

    def _set_actuator_state(
        self,
        endpoint_id,
        actor_name,
        capability,
        field,
        value,
        raw_value=None,
        timestamp_ms=None,
    ):
        endpoint_id = _normalize_endpoint(endpoint_id)
        state_key = (int(endpoint_id), str(field))
        prev = self._actuator_state.get(state_key, None)
        changed = True
        if prev is not None and prev.get("value", None) == value:
            changed = False
        if timestamp_ms is None:
            timestamp_ms = _ticks_ms()
        row = {
            "endpoint_id": int(endpoint_id),
            "name": str(actor_name),
            "capability": str(capability),
            "field": str(field),
            "value": value,
            "raw_value": raw_value,
            "updated_ms": int(timestamp_ms),
            "changed": bool(changed),
            "sent": False,
        }
        self._actuator_state[state_key] = row
        if str(field) == "on_off":
            writer = self._onoff_outputs.get(int(endpoint_id), None)
            if writer is not None:
                try:
                    writer(bool(value))
                except Exception:
                    pass
        self._invoke_policy_hooks("actuator_update", row)
        return dict(row)

    def actuator_state(self, actor, field=None, default=None):
        component = self._resolve_actor_component(name=actor)
        endpoint_id = int(component["endpoint_id"])
        if field is not None:
            row = self._actuator_state.get((endpoint_id, str(field)), None)
            return dict(row) if row is not None else default
        out = {}
        for (state_endpoint_id, state_field), row in self._actuator_state.items():
            if int(state_endpoint_id) != endpoint_id:
                continue
            out[str(state_field)] = dict(row)
        if not out:
            return default
        return out

    def actuator_states(self):
        out = []
        for item in self._actuator_state.values():
            out.append(dict(item))
        out.sort(key=lambda row: (int(row["endpoint_id"]), str(row["field"])))
        return tuple(out)

    def _reporting_targets(self, capability=None, endpoint_id=None):
        if endpoint_id is not None:
            endpoint_id = _normalize_endpoint(endpoint_id)
            for item in self._endpoint_plan:
                if int(item["endpoint_id"]) == endpoint_id:
                    return (item,)
            raise ValueError("endpoint {} not found".format(endpoint_id))

        if capability is None:
            out = []
            for item in self._endpoint_plan:
                if item["kind"] in _REPORTING_PRESET_BY_KIND:
                    out.append(item)
            return tuple(out)

        capability_key = _normalize_capability_name(capability)
        capability_key = _CAPABILITY_ALIASES.get(capability_key, capability_key)
        allowed_kinds = _REPORTING_CAPABILITY_KIND_MAP.get(capability_key, None)
        if allowed_kinds is None:
            raise ValueError("unsupported reporting capability '{}'".format(capability))

        out = []
        for item in self._endpoint_plan:
            if item["kind"] in allowed_kinds:
                out.append(item)
        if not out:
            raise ValueError("no endpoint for reporting capability '{}'".format(capability))
        return tuple(out)

    def _resolve_reporting_preset(self, component_kind, preset):
        if preset is None:
            return tuple(_REPORTING_PRESET_BY_KIND.get(component_kind, ()))
        if isinstance(preset, str):
            preset_key = _normalize_capability_name(preset)
            preset_key = _CAPABILITY_ALIASES.get(preset_key, preset_key)
            preset_value = _REPORTING_PRESET_BY_NAME.get(preset_key, None)
            if preset_value is None:
                raise ValueError("unknown reporting preset '{}'".format(preset))
            return tuple(preset_value)
        return _normalize_reporting_entries(preset)

    def configure_reporting_policy(
        self,
        capability=None,
        endpoint_id=None,
        preset=None,
        overrides=None,
        dst_short_addr=0x0000,
        dst_endpoint=1,
        src_endpoint=None,
        auto_apply=False,
    ):
        targets = self._reporting_targets(capability=capability, endpoint_id=endpoint_id)
        configured = []
        for item in targets:
            item_endpoint = int(item["endpoint_id"])
            item_kind = item["kind"]
            base_entries = self._resolve_reporting_preset(item_kind, preset)
            if not base_entries and not overrides:
                raise ValueError("no reporting preset for endpoint {}".format(item_endpoint))
            entries = tuple(base_entries)
            if overrides:
                entries = _merge_reporting_entries(entries, overrides)
            if not entries:
                raise ValueError("empty reporting policy for endpoint {}".format(item_endpoint))
            policy_src_endpoint = int(item_endpoint if src_endpoint is None else src_endpoint)
            policy = {
                "name": item["name"],
                "kind": item_kind,
                "endpoint_id": item_endpoint,
                "src_endpoint": policy_src_endpoint,
                "dst_short_addr": int(dst_short_addr),
                "dst_endpoint": int(dst_endpoint),
                "entries": tuple(entries),
            }
            self._reporting_policies[item_endpoint] = policy
            self._invoke_policy_hooks("reporting_configured", policy)
            configured.append(dict(policy))

        if auto_apply:
            for item in configured:
                self.apply_reporting_policy(endpoint_id=item["endpoint_id"])
        return tuple(configured)

    def reporting_policies(self):
        out = []
        for policy in self._reporting_policies.values():
            row = dict(policy)
            row["entries"] = tuple(policy["entries"])
            out.append(row)
        out.sort(key=lambda row: int(row["endpoint_id"]))
        return tuple(out)

    def clear_reporting_policy(self, endpoint_id=None):
        if endpoint_id is None:
            count = len(self._reporting_policies)
            self._reporting_policies.clear()
            return count
        endpoint_id = _normalize_endpoint(endpoint_id)
        if endpoint_id in self._reporting_policies:
            del self._reporting_policies[endpoint_id]
            return 1
        return 0

    def apply_reporting_policy(self, capability=None, endpoint_id=None):
        targets = self._reporting_targets(capability=capability, endpoint_id=endpoint_id)
        applied = []
        for item in targets:
            item_endpoint = int(item["endpoint_id"])
            policy = self._reporting_policies.get(item_endpoint, None)
            if policy is None:
                continue
            for entry in policy["entries"]:
                self.stack.configure_reporting(
                    dst_short_addr=int(policy["dst_short_addr"]),
                    cluster_id=int(entry[0]),
                    attr_id=int(entry[1]),
                    attr_type=int(entry[2]),
                    src_endpoint=int(policy["src_endpoint"]),
                    dst_endpoint=int(policy["dst_endpoint"]),
                    min_interval=int(entry[3]),
                    max_interval=int(entry[4]),
                    reportable_change=entry[5],
                )
                applied.append(
                    {
                        "endpoint_id": item_endpoint,
                        "cluster_id": int(entry[0]),
                        "attr_id": int(entry[1]),
                        "attr_type": int(entry[2]),
                        "min_interval": int(entry[3]),
                        "max_interval": int(entry[4]),
                        "reportable_change": entry[5],
                    }
                )
                self._invoke_policy_hooks("reporting_applied", applied[-1])
        return tuple(applied)

    def _binding_targets(self, capability=None, endpoint_id=None):
        if endpoint_id is not None:
            endpoint_id = _normalize_endpoint(endpoint_id)
            for item in self._endpoint_plan:
                if int(item["endpoint_id"]) == endpoint_id:
                    return (item,)
            raise ValueError("endpoint {} not found".format(endpoint_id))

        if capability is None:
            out = []
            for item in self._endpoint_plan:
                if item["kind"] in _BIND_DEFAULT_CLUSTERS_BY_KIND:
                    out.append(item)
            return tuple(out)

        capability_key = _normalize_capability_name(capability)
        capability_key = _CAPABILITY_ALIASES.get(capability_key, capability_key)
        allowed_kinds = _BIND_CAPABILITY_KIND_MAP.get(capability_key, None)
        if allowed_kinds is None:
            raise ValueError("unsupported binding capability '{}'".format(capability))
        out = []
        for item in self._endpoint_plan:
            if item["kind"] in allowed_kinds:
                out.append(item)
        if not out:
            raise ValueError("no endpoint for binding capability '{}'".format(capability))
        return tuple(out)

    def _resolve_binding_clusters(self, component_kind, clusters):
        if clusters is None:
            return tuple(_BIND_DEFAULT_CLUSTERS_BY_KIND.get(component_kind, ()))
        return _normalize_cluster_ids(clusters)

    def configure_binding_policy(
        self,
        capability=None,
        endpoint_id=None,
        clusters=None,
        dst_ieee_addr=None,
        dst_endpoint=1,
        req_dst_short_addr=0x0000,
        src_ieee_addr=None,
        src_endpoint=None,
        ias_enroll=True,
        auto_apply=False,
    ):
        targets = self._binding_targets(capability=capability, endpoint_id=endpoint_id)
        configured = []
        for item in targets:
            item_endpoint = int(item["endpoint_id"])
            cluster_ids = self._resolve_binding_clusters(item["kind"], clusters)
            if not cluster_ids:
                raise ValueError("no bind clusters for endpoint {}".format(item_endpoint))
            policy = {
                "name": item["name"],
                "kind": item["kind"],
                "endpoint_id": item_endpoint,
                "src_endpoint": int(item_endpoint if src_endpoint is None else src_endpoint),
                "clusters": tuple(cluster_ids),
                "dst_ieee_addr": None if dst_ieee_addr is None else _normalize_ieee_addr(dst_ieee_addr),
                "dst_endpoint": int(dst_endpoint),
                "req_dst_short_addr": int(req_dst_short_addr),
                "src_ieee_addr": None if src_ieee_addr is None else _normalize_ieee_addr(src_ieee_addr),
                "ias_enroll": bool(ias_enroll),
            }
            self._binding_policies[item_endpoint] = policy
            self._invoke_policy_hooks("binding_configured", policy)
            configured.append(dict(policy))
        if auto_apply:
            for item in configured:
                self.apply_binding_policy(endpoint_id=item["endpoint_id"])
        return tuple(configured)

    def binding_policies(self):
        out = []
        for policy in self._binding_policies.values():
            row = dict(policy)
            row["clusters"] = tuple(policy["clusters"])
            out.append(row)
        out.sort(key=lambda row: int(row["endpoint_id"]))
        return tuple(out)

    def clear_binding_policy(self, endpoint_id=None):
        if endpoint_id is None:
            count = len(self._binding_policies)
            self._binding_policies.clear()
            return count
        endpoint_id = _normalize_endpoint(endpoint_id)
        if endpoint_id in self._binding_policies:
            del self._binding_policies[endpoint_id]
            return 1
        return 0

    def apply_binding_policy(
        self,
        capability=None,
        endpoint_id=None,
        dst_ieee_addr=None,
        dst_endpoint=None,
        req_dst_short_addr=None,
        src_ieee_addr=None,
        ias_enroll=None,
    ):
        targets = self._binding_targets(capability=capability, endpoint_id=endpoint_id)
        applied = []
        for item in targets:
            item_endpoint = int(item["endpoint_id"])
            policy = self._binding_policies.get(item_endpoint, None)
            if policy is None:
                continue
            effective_dst_ieee = (
                policy["dst_ieee_addr"]
                if dst_ieee_addr is None
                else _normalize_ieee_addr(dst_ieee_addr)
            )
            if effective_dst_ieee is None:
                applied.append(
                    {
                        "endpoint_id": item_endpoint,
                        "status": "skipped",
                        "reason": "missing_dst_ieee",
                        "bound": 0,
                        "failed": tuple(),
                    }
                )
                continue

            effective_src_ieee = policy["src_ieee_addr"]
            if src_ieee_addr is not None:
                effective_src_ieee = _normalize_ieee_addr(src_ieee_addr)
            if effective_src_ieee is None:
                effective_src_ieee = _normalize_ieee_addr(self.stack.get_ieee_addr())

            effective_dst_endpoint = int(policy["dst_endpoint"] if dst_endpoint is None else dst_endpoint)
            effective_req_short = int(
                policy["req_dst_short_addr"] if req_dst_short_addr is None else req_dst_short_addr
            )
            effective_ias_enroll = bool(policy["ias_enroll"] if ias_enroll is None else ias_enroll)

            bound = 0
            failures = []
            for cluster_id in policy["clusters"]:
                try:
                    self.stack.send_bind_cmd(
                        src_ieee_addr=effective_src_ieee,
                        src_endpoint=int(policy["src_endpoint"]),
                        cluster_id=int(cluster_id),
                        dst_ieee_addr=effective_dst_ieee,
                        dst_endpoint=effective_dst_endpoint,
                        req_dst_short_addr=effective_req_short,
                    )
                    bound += 1
                except Exception as exc:
                    failures.append(
                        {
                            "cluster_id": int(cluster_id),
                            "error": str(exc),
                        }
                    )

            enroll = None
            if effective_ias_enroll and item["kind"] == "ias_zone":
                try:
                    self.stack.set_attribute(
                        int(item_endpoint),
                        int(CLUSTER_ID_IAS_ZONE),
                        int(ATTR_IAS_ZONE_IAS_CIE_ADDRESS),
                        bytes(effective_dst_ieee),
                    )
                    enroll = {"status": "ok"}
                except Exception as exc:
                    enroll = {"status": "error", "error": str(exc)}

            applied.append(
                {
                    "endpoint_id": item_endpoint,
                    "status": "ok" if not failures else "partial",
                    "bound": int(bound),
                    "failed": tuple(failures),
                    "enroll": enroll,
                }
            )
            self._invoke_policy_hooks("binding_applied", applied[-1])
        return tuple(applied)

    def _resolve_update_key(self, capability):
        key = _normalize_capability_name(capability)
        key = _UPDATE_CAPABILITY_ALIASES.get(key, key)
        if key not in _UPDATE_ALLOWED_KINDS:
            raise ValueError("unsupported update capability '{}'".format(capability))
        return key

    def _match_update_component(self, capability_key, endpoint_id=None):
        allowed_kinds = _UPDATE_ALLOWED_KINDS[capability_key]
        if endpoint_id is not None:
            endpoint_id = _normalize_endpoint(endpoint_id)
        matches = []
        for item in self._endpoint_plan:
            if item["kind"] not in allowed_kinds:
                continue
            item_endpoint_id = int(item["endpoint_id"])
            if endpoint_id is not None and item_endpoint_id != endpoint_id:
                continue
            matches.append(item_endpoint_id)
        if not matches:
            raise ValueError("no endpoint for capability '{}'".format(capability_key))
        if endpoint_id is None and len(matches) > 1:
            raise ValueError(
                "capability '{}' is ambiguous; pass endpoint_id".format(capability_key)
            )
        return int(matches[0])

    def _normalize_update_value(self, capability_key, value):
        if capability_key == "temperature":
            return _normalize_temperature(value)
        if capability_key == "humidity":
            return _normalize_humidity(value)
        if capability_key == "pressure":
            return _normalize_pressure(value)
        if capability_key == "occupancy":
            return _normalize_binary(value, "occupancy")
        if capability_key == "contact":
            return _normalize_binary(value, "contact")
        if capability_key == "motion":
            return _normalize_binary(value, "motion")
        if capability_key == "ias_zone":
            return _normalize_ias_zone(value)
        if capability_key == "climate":
            return _normalize_climate(value)
        raise ValueError("unsupported update capability '{}'".format(capability_key))

    def _store_sensor_state(self, endpoint_id, capability_key, value, raw_value, updated_ms):
        state_key = (int(endpoint_id), str(capability_key))
        row = {
            "endpoint_id": int(endpoint_id),
            "capability": str(capability_key),
            "value": value,
            "raw_value": raw_value,
            "updated_ms": int(updated_ms),
        }
        self._sensor_state[state_key] = row
        return dict(row)

    def update(self, capability, value, endpoint_id=None, timestamp_ms=None):
        capability_key = self._resolve_update_key(capability)
        endpoint_id = self._match_update_component(capability_key, endpoint_id=endpoint_id)
        normalized_value, raw_value = self._normalize_update_value(capability_key, value)
        if timestamp_ms is None:
            timestamp_ms = _ticks_ms()
        row = self._store_sensor_state(
            endpoint_id,
            capability_key,
            normalized_value,
            raw_value,
            timestamp_ms,
        )
        self._invoke_policy_hooks("sensor_update", row)
        if capability_key == "climate":
            for sub_key in ("temperature", "humidity", "pressure"):
                if sub_key not in normalized_value:
                    continue
                self._store_sensor_state(
                    endpoint_id,
                    sub_key,
                    normalized_value[sub_key],
                    raw_value[sub_key],
                    timestamp_ms,
                )
        return row

    def sensor_state(self, capability, endpoint_id=None, default=None):
        capability_key = self._resolve_update_key(capability)
        if endpoint_id is not None:
            endpoint_id = _normalize_endpoint(endpoint_id)
            row = self._sensor_state.get((int(endpoint_id), capability_key), None)
            return dict(row) if row is not None else default
        rows = []
        for (state_endpoint_id, state_capability), row in self._sensor_state.items():
            if state_capability != capability_key:
                continue
            rows.append((int(state_endpoint_id), row))
        if not rows:
            return default
        if len(rows) > 1:
            raise ValueError(
                "sensor state '{}' is ambiguous; pass endpoint_id".format(capability_key)
            )
        return dict(rows[0][1])

    def sensor_states(self):
        out = []
        for item in self._sensor_state.values():
            out.append(dict(item))
        out.sort(key=lambda row: (int(row["endpoint_id"]), str(row["capability"])))
        return tuple(out)

    def _provision_endpoints(self, force_register=False):
        for item in self._endpoint_plan:
            if item["provisioned"]:
                continue
            method_name = item["create_method"]
            if not hasattr(self.stack, method_name):
                raise ZigbeeError("stack method not available: {}".format(method_name))
            method = getattr(self.stack, method_name)
            endpoint_id = int(item["endpoint_id"])
            options = dict(item.get("options") or {})
            method(endpoint_id, **options)
            item["provisioned"] = True
            # Register each endpoint right after creation. Current C bridge keeps
            # one pending endpoint descriptor at a time.
            if hasattr(self.stack, "register_device") and (self.auto_register or force_register):
                self.stack.register_device()
                self._registered = True

    def register(self):
        # The C bridge keeps one pending endpoint descriptor at a time, so
        # registration must happen right after each endpoint creation.
        self._provision_endpoints(force_register=True)
        if not self._registered and self.auto_register:
            self.stack.register_device()
            self._registered = True
        return self

    def on_signal(self, callback=None):
        self._on_signal_cb = callback
        return self

    def on_attribute(self, callback=None):
        self._on_attribute_cb = callback
        return self

    def on_commissioning_event(self, callback=None):
        self._commissioning_event_cb = callback if callable(callback) else None
        return self

    def configure_auto_join(
        self,
        auto_join_channel_mask=None,
        join_retry_max=None,
        join_retry_base_ms=None,
        join_retry_max_backoff_ms=None,
    ):
        if auto_join_channel_mask is not None:
            self._auto_join_channel_mask = _normalize_channel_mask(channel_mask=auto_join_channel_mask)
        if join_retry_max is not None:
            self._join_retry_max = _clamp_int(join_retry_max, 0, 10)
        if join_retry_base_ms is not None:
            self._join_retry_base_ms = _clamp_int(join_retry_base_ms, 0, 60000)
        if join_retry_max_backoff_ms is not None:
            self._join_retry_max_backoff_ms = _clamp_int(
                join_retry_max_backoff_ms,
                self._join_retry_base_ms,
                300000,
            )
        return {
            "auto_join_channel_mask": int(self._auto_join_channel_mask),
            "join_retry_max": int(self._join_retry_max),
            "join_retry_base_ms": int(self._join_retry_base_ms),
            "join_retry_max_backoff_ms": int(self._join_retry_max_backoff_ms),
        }

    def configure_self_heal(
        self,
        enabled=None,
        retry_max=None,
        retry_base_ms=None,
        retry_max_backoff_ms=None,
    ):
        if enabled is not None:
            self._self_heal_enabled = bool(enabled)
        if retry_max is not None:
            self._self_heal_retry_max = _clamp_int(retry_max, 0, 10)
        if retry_base_ms is not None:
            self._self_heal_retry_base_ms = _clamp_int(retry_base_ms, 0, 60000)
        if retry_max_backoff_ms is not None:
            self._self_heal_retry_max_backoff_ms = _clamp_int(
                retry_max_backoff_ms,
                self._self_heal_retry_base_ms,
                300000,
            )
        return {
            "enabled": bool(self._self_heal_enabled),
            "retry_max": int(self._self_heal_retry_max),
            "retry_base_ms": int(self._self_heal_retry_base_ms),
            "retry_max_backoff_ms": int(self._self_heal_retry_max_backoff_ms),
        }

    def commissioning_stats(self, reset=False):
        stats = dict(self._commissioning_stats)
        if reset:
            self._commissioning_stats = _new_commissioning_stats()
        return stats

    def self_heal_stats(self):
        return dict(self._self_heal_stats)

    def _mark_commissioning_attempt(self, kind):
        now_ms = int(_ticks_ms())
        stats = self._commissioning_stats
        if str(kind) == "form":
            stats["form_attempts"] += 1
            if stats.get("form_started_ms", None) is None:
                stats["form_started_ms"] = int(now_ms)
        else:
            stats["join_attempts"] += 1
            if stats.get("join_started_ms", None) is None:
                stats["join_started_ms"] = int(now_ms)
        stats["last_event_ms"] = int(now_ms)
        return int(now_ms)

    def _mark_commissioning_success(self, kind, now_ms=None):
        now_ms = int(_ticks_ms()) if now_ms is None else int(now_ms)
        stats = self._commissioning_stats
        if str(kind) == "form":
            stats["form_success"] += 1
            stats["last_form_success_ms"] = int(now_ms)
            started_ms = stats.get("form_started_ms", None)
            if started_ms is not None:
                stats["time_to_form_ms"] = int(now_ms) - int(started_ms)
                stats["form_started_ms"] = None
        else:
            stats["join_success"] += 1
            stats["last_join_success_ms"] = int(now_ms)
            started_ms = stats.get("join_started_ms", None)
            if started_ms is not None:
                stats["time_to_join_ms"] = int(now_ms) - int(started_ms)
                stats["join_started_ms"] = None
        stats["last_event_ms"] = int(now_ms)

    def _mark_commissioning_failure(self, kind, status=None, now_ms=None):
        now_ms = int(_ticks_ms()) if now_ms is None else int(now_ms)
        stats = self._commissioning_stats
        if str(kind) == "form":
            stats["form_failures"] += 1
        else:
            stats["join_failures"] += 1
        if _is_timeout_status(status):
            stats["timeout_events"] += 1
        stats["last_event_ms"] = int(now_ms)

    def _update_commissioning_stats_on_signal(self, signal_id, status):
        signal_id = int(signal_id)
        status = int(status)
        now_ms = int(_ticks_ms())
        stats = self._commissioning_stats
        stats["last_signal"] = int(signal_id)
        stats["last_status"] = int(status)
        stats["last_event_ms"] = int(now_ms)
        if signal_id == int(SIGNAL_PANID_CONFLICT_DETECTED):
            stats["conflict_events"] += 1
        if signal_id == int(SIGNAL_FORMATION):
            if status == 0:
                self._mark_commissioning_success("form", now_ms=now_ms)
            else:
                self._mark_commissioning_failure("form", status=status, now_ms=now_ms)
            return
        if signal_id == int(SIGNAL_STEERING):
            if status == 0:
                self._mark_commissioning_success("join", now_ms=now_ms)
            else:
                self._mark_commissioning_failure("join", status=status, now_ms=now_ms)
            return
        if signal_id == int(SIGNAL_STEERING_CANCELLED):
            self._mark_commissioning_failure("join", status=status, now_ms=now_ms)
            return
        if signal_id in (int(SIGNAL_DEVICE_FIRST_START), int(SIGNAL_DEVICE_REBOOT)) and status == 0:
            if stats.get("join_started_ms", None) is not None:
                self._mark_commissioning_success("join", now_ms=now_ms)

    def _sync_network_profile_from_runtime(self):
        if not hasattr(self.stack, "get_network_runtime"):
            return False
        try:
            runtime = self.stack.get_network_runtime() or {}
        except Exception:
            return False
        if not isinstance(runtime, dict):
            return False

        channel_mask = None
        pan_id = None
        ext_pan = None
        formed = bool(runtime.get("formed", False))

        try:
            channel = int(runtime.get("channel"))
            if 11 <= channel <= 26:
                channel_mask = int(1 << channel)
        except Exception:
            channel_mask = None

        try:
            pan_candidate = int(runtime.get("pan_id"))
            if 0x0001 <= pan_candidate <= 0xFFFE:
                pan_id = int(pan_candidate)
        except Exception:
            pan_id = None

        try:
            ext_candidate = runtime.get("extended_pan_id", None)
            if ext_candidate is not None:
                ext_candidate = bytes(ext_candidate)
                if len(ext_candidate) == 8:
                    ext_pan = bytes(ext_candidate)
        except Exception:
            ext_pan = None

        changed = False
        if channel_mask is not None and self._network_profile.channel_mask != int(channel_mask):
            self._channel_mask = int(channel_mask)
            changed = True
        if pan_id is not None and self._network_profile.pan_id != int(pan_id):
            self._pan_id = int(pan_id)
            changed = True
        if ext_pan is not None and self._network_profile.extended_pan_id != bytes(ext_pan):
            self._extended_pan_id = bytes(ext_pan)
            changed = True

        formed_at_ms = self._network_profile.formed_at_ms
        if formed and formed_at_ms is None:
            formed_at_ms = int(_ticks_ms())
            changed = True

        if changed:
            self._network_profile.update(
                channel_mask=channel_mask,
                pan_id=pan_id,
                extended_pan_id=ext_pan,
                source=_mode_profile_source(self.commissioning_mode),
                formed_at_ms=formed_at_ms,
            )
        return bool(changed)

    def _emit_commissioning_event(self, event, reason=None, signal_id=None, status=None, attempt=None, ok=None, backoff_ms=None):
        payload = {
            "event": str(event),
            "reason": None if reason is None else str(reason),
            "signal_id": None if signal_id is None else int(signal_id),
            "status": None if status is None else int(status),
            "attempt": None if attempt is None else int(attempt),
            "ok": None if ok is None else bool(ok),
            "backoff_ms": None if backoff_ms is None else int(backoff_ms),
            "timestamp_ms": int(_ticks_ms()),
        }
        if callable(self._commissioning_event_cb):
            try:
                self._commissioning_event_cb(dict(payload))
            except Exception:
                pass
        return payload

    def _self_heal_retrigger_steering(self, reason, signal_id=None, status=None):
        if not bool(self._self_heal_enabled):
            return False
        if int(self.role) not in (ROLE_ROUTER, ROLE_END_DEVICE):
            return False
        if not bool(self._started):
            return False
        if bool(self._self_heal_inflight):
            return False

        self._self_heal_inflight = True
        try:
            attempt = 0
            guided_fallback_applied = False
            while True:
                self._mark_commissioning_attempt("join")
                ok = bool(self._trigger_network_steering_once())
                self._self_heal_stats["attempts"] += 1
                self._self_heal_stats["last_reason"] = None if reason is None else str(reason)
                self._self_heal_stats["last_signal"] = None if signal_id is None else int(signal_id)
                self._self_heal_stats["last_status"] = None if status is None else int(status)
                self._self_heal_stats["last_attempt_ms"] = int(_ticks_ms())
                self._self_heal_stats["last_result"] = "success" if ok else "retrying"
                self._emit_commissioning_event(
                    "self_heal_retry",
                    reason=reason,
                    signal_id=signal_id,
                    status=status,
                    attempt=attempt,
                    ok=ok,
                    backoff_ms=0,
                )
                if ok:
                    self._self_heal_stats["success"] += 1
                    self._self_heal_stats["last_backoff_ms"] = 0
                    return True

                if (
                    self.commissioning_mode == NETWORK_MODE_GUIDED
                    and not guided_fallback_applied
                ):
                    fallback_mask = int(self._auto_join_channel_mask)
                    current_mask = None if self._channel_mask is None else int(self._channel_mask)
                    if current_mask != fallback_mask:
                        if hasattr(self.stack, "set_primary_channel_mask"):
                            _ignore_invalid_state(self.stack.set_primary_channel_mask, int(fallback_mask))
                        self._channel_mask = int(fallback_mask)
                    guided_fallback_applied = True
                    self._self_heal_stats["guided_fallback_count"] += 1

                if attempt >= int(self._self_heal_retry_max):
                    self._self_heal_stats["failed"] += 1
                    self._self_heal_stats["last_result"] = "failed"
                    return False

                backoff_ms = int(self._self_heal_retry_base_ms) * (1 << int(attempt))
                if backoff_ms > int(self._self_heal_retry_max_backoff_ms):
                    backoff_ms = int(self._self_heal_retry_max_backoff_ms)
                self._self_heal_stats["last_backoff_ms"] = int(backoff_ms)
                _sleep_ms(backoff_ms)
                attempt += 1
        finally:
            self._self_heal_inflight = False

    def _hydrate_guided_identity_from_profile(self):
        if self.commissioning_mode != NETWORK_MODE_GUIDED:
            return False
        changed = False
        if self._pan_id is None and self._network_profile.pan_id is not None:
            self._pan_id = int(self._network_profile.pan_id)
            changed = True
        if self._extended_pan_id is None and self._network_profile.extended_pan_id is not None:
            self._extended_pan_id = bytes(self._network_profile.extended_pan_id)
            changed = True
        return bool(changed)

    def _prepare_guided_join_channel_mask(self):
        if self.commissioning_mode != NETWORK_MODE_GUIDED:
            return None
        if int(self.role) not in (ROLE_ROUTER, ROLE_END_DEVICE):
            return None
        if self._channel_mask is not None:
            selected_channels = _channels_from_mask(int(self._channel_mask))
            return {
                "strategy": "guided_explicit",
                "channel_mask": int(self._channel_mask),
                "channel": int(selected_channels[0]) if len(selected_channels) == 1 else None,
            }
        if self._network_profile.channel_mask is not None:
            restored_mask = int(self._network_profile.channel_mask)
            self._channel_mask = int(restored_mask)
            selected_channels = _channels_from_mask(restored_mask)
            return {
                "strategy": "guided_restored_profile",
                "channel_mask": int(restored_mask),
                "channel": int(selected_channels[0]) if len(selected_channels) == 1 else None,
            }
        self._channel_mask = int(self._auto_join_channel_mask)
        selected_channels = _channels_from_mask(self._channel_mask)
        return {
            "strategy": "guided_auto_fallback",
            "channel_mask": int(self._channel_mask),
            "channel": int(selected_channels[0]) if len(selected_channels) == 1 else None,
        }

    def _trigger_network_steering_once(self):
        if hasattr(self.stack, "start_network_steering"):
            return bool(_ignore_invalid_state_or_steering_busy(self.stack.start_network_steering))
        if self._started:
            _ignore_invalid_state(self.stack.start, False)
            return True
        return False

    def _start_network_steering_with_backoff(self):
        attempt = 0
        while True:
            self._mark_commissioning_attempt("join")
            ok = bool(self._trigger_network_steering_once())
            self._join_trigger_count += 1
            self._join_last_attempt_ms = int(_ticks_ms())
            self._join_last_trigger_ok = bool(ok)
            if ok:
                self._join_last_backoff_ms = 0
                return True
            if attempt >= int(self._join_retry_max):
                return False
            delay_ms = int(self._join_retry_base_ms) * (1 << int(attempt))
            if delay_ms > int(self._join_retry_max_backoff_ms):
                delay_ms = int(self._join_retry_max_backoff_ms)
            self._join_last_backoff_ms = int(delay_ms)
            _sleep_ms(delay_ms)
            attempt += 1

    def _handle_signal(self, signal_id, status):
        self._last_signal = int(signal_id)
        self._last_status = int(status)
        signal_id = int(signal_id)
        status = int(status)
        self._update_commissioning_stats_on_signal(signal_id, status)
        if status == 0 and signal_id in _JOIN_PROFILE_SYNC_SIGNALS:
            self._sync_network_profile_from_runtime()
        if signal_id == int(SIGNAL_PANID_CONFLICT_DETECTED):
            self._self_heal_stats["panid_conflicts"] += 1
            self._emit_commissioning_event(
                "panid_conflict_detected",
                reason="panid_conflict_detected",
                signal_id=signal_id,
                status=status,
            )
            self._self_heal_retrigger_steering(
                reason="panid_conflict_detected",
                signal_id=signal_id,
                status=status,
            )
        elif signal_id in _SELF_HEAL_STEERING_SIGNALS and status != 0:
            self._self_heal_stats["steering_failures"] += 1
            self._self_heal_retrigger_steering(
                reason="steering_failure",
                signal_id=signal_id,
                status=status,
            )
        if self._on_signal_cb is not None:
            self._on_signal_cb(int(signal_id), int(status))

    def _handle_attribute(self, *event):
        source_short_addr = None
        attr_type = None

        if len(event) == 5:
            endpoint, cluster_id, attr_id, value, status = event
        elif len(event) == 6:
            endpoint, cluster_id, attr_id, value, attr_type, status = event
        elif len(event) >= 7:
            source_short_addr, endpoint, cluster_id, attr_id, value, attr_type, status = event[:7]
        else:
            return

        endpoint = int(endpoint)
        cluster_id = int(cluster_id)
        attr_id = int(attr_id)
        status = int(status)
        if source_short_addr is not None:
            source_short_addr = int(source_short_addr) & 0xFFFF
        if attr_type is not None:
            attr_type = int(attr_type)

        if self._on_attribute_cb is not None:
            try:
                if source_short_addr is not None:
                    self._on_attribute_cb(
                        source_short_addr,
                        endpoint,
                        cluster_id,
                        attr_id,
                        value,
                        attr_type,
                        status,
                    )
                else:
                    self._on_attribute_cb(endpoint, cluster_id, attr_id, value, status)
            except TypeError:
                self._on_attribute_cb(endpoint, cluster_id, attr_id, value, status)

        if status != 0:
            return

        component = self._component_by_endpoint(endpoint)
        if component is None:
            return
        kind = str(component["kind"])
        name = str(component["name"])
        now_ms = _ticks_ms()

        if (
            cluster_id == int(CLUSTER_ID_ON_OFF)
            and attr_id == int(ATTR_ON_OFF_ON_OFF)
            and kind in _ACTUATOR_ON_OFF_KINDS
        ):
            value_bool = bool(int(value))
            self._set_actuator_state(
                endpoint_id=endpoint,
                actor_name=name,
                capability=kind,
                field="on_off",
                value=value_bool,
                raw_value=int(value_bool),
                timestamp_ms=now_ms,
            )
            return

        if (
            cluster_id == int(CLUSTER_ID_LEVEL_CONTROL)
            and attr_id == int(ATTR_LEVEL_CONTROL_CURRENT_LEVEL)
            and kind in _ACTUATOR_LEVEL_KINDS
        ):
            level = int(value)
            if level < 0:
                level = 0
            if level > 254:
                level = 254
            self._set_actuator_state(
                endpoint_id=endpoint,
                actor_name=name,
                capability=kind,
                field="level",
                value=int(level),
                raw_value=int(level),
                timestamp_ms=now_ms,
            )
            return

        if (
            cluster_id == int(CLUSTER_ID_DOOR_LOCK)
            and attr_id == int(ATTR_DOOR_LOCK_LOCK_STATE)
            and kind in _ACTUATOR_LOCK_KINDS
        ):
            locked = int(value) == 1
            self._set_actuator_state(
                endpoint_id=endpoint,
                actor_name=name,
                capability=kind,
                field="locked",
                value=bool(locked),
                raw_value=int(value),
                timestamp_ms=now_ms,
            )
            return

        if cluster_id == int(CLUSTER_ID_WINDOW_COVERING) and kind in _ACTUATOR_COVER_KINDS:
            if attr_id == int(ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE):
                self._set_actuator_state(
                    endpoint_id=endpoint,
                    actor_name=name,
                    capability=kind,
                    field="cover_lift_percent",
                    value=int(value),
                    raw_value=int(value),
                    timestamp_ms=now_ms,
                )
            elif attr_id == int(ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE):
                self._set_actuator_state(
                    endpoint_id=endpoint,
                    actor_name=name,
                    capability=kind,
                    field="cover_tilt_percent",
                    value=int(value),
                    raw_value=int(value),
                    timestamp_ms=now_ms,
                )
            return

        if cluster_id == int(CLUSTER_ID_THERMOSTAT) and kind in _ACTUATOR_THERMOSTAT_KINDS:
            if attr_id == int(ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT):
                celsius = float(int(value)) / 100.0
                self._set_actuator_state(
                    endpoint_id=endpoint,
                    actor_name=name,
                    capability=kind,
                    field="thermostat_heating_setpoint",
                    value=celsius,
                    raw_value=int(value),
                    timestamp_ms=now_ms,
                )
            elif attr_id == int(ATTR_THERMOSTAT_SYSTEM_MODE):
                self._set_actuator_state(
                    endpoint_id=endpoint,
                    actor_name=name,
                    capability=kind,
                    field="thermostat_mode",
                    value=int(value),
                    raw_value=int(value),
                    timestamp_ms=now_ms,
                )

    def start(self, join_parent=True, form_network=None):
        now_ms = int(_ticks_ms())
        self._commissioning_stats["start_count"] += 1
        self._commissioning_stats["last_start_ms"] = int(now_ms)
        if bool(form_network):
            self._mark_commissioning_attempt("form")
        self._hydrate_guided_identity_from_profile()
        self._prepare_guided_join_channel_mask()
        apply_network_identity = self.commissioning_mode in (NETWORK_MODE_FIXED, NETWORK_MODE_GUIDED)
        if apply_network_identity and self._extended_pan_id is not None and hasattr(self.stack, "set_extended_pan_id"):
            _ignore_invalid_state(self.stack.set_extended_pan_id, bytes(self._extended_pan_id))
        if apply_network_identity and self._pan_id is not None and hasattr(self.stack, "set_pan_id"):
            _ignore_invalid_state(self.stack.set_pan_id, int(self._pan_id))
        if apply_network_identity and self._channel_mask is not None and hasattr(self.stack, "set_primary_channel_mask"):
            _ignore_invalid_state(self.stack.set_primary_channel_mask, int(self._channel_mask))
        if (
            self.commissioning_mode == NETWORK_MODE_AUTO
            and int(self.role) in (ROLE_ROUTER, ROLE_END_DEVICE)
            and self._auto_join_channel_mask is not None
            and hasattr(self.stack, "set_primary_channel_mask")
        ):
            _ignore_invalid_state(self.stack.set_primary_channel_mask, int(self._auto_join_channel_mask))
        _ignore_invalid_state(self.stack.init, self.role)
        self.stack.on_signal(self._handle_signal)
        if hasattr(self.stack, "on_attribute"):
            self.stack.on_attribute(self._handle_attribute)
        self.register()
        if form_network is None:
            form_network = False if bool(join_parent) else False
        _ignore_invalid_state(self.stack.start, bool(form_network))
        self._form_network = bool(form_network)
        if bool(join_parent) and int(self.role) in (ROLE_ROUTER, ROLE_END_DEVICE):
            self.join_parent()
        self._started = True
        formed_at_ms = int(_ticks_ms()) if bool(form_network) else self._network_profile.formed_at_ms
        self._network_profile.update(
            channel_mask=self._channel_mask,
            pan_id=self._pan_id,
            extended_pan_id=self._extended_pan_id,
            source=_mode_profile_source(self.commissioning_mode),
            formed_at_ms=formed_at_ms,
        )
        if self.commissioning_mode in (NETWORK_MODE_AUTO, NETWORK_MODE_GUIDED):
            self._sync_network_profile_from_runtime()
        return self

    def join_parent(self):
        if int(self.role) not in (ROLE_ROUTER, ROLE_END_DEVICE):
            raise ValueError("join_parent is supported only for Router/EndDevice")
        if self.commissioning_mode == NETWORK_MODE_GUIDED:
            preferred_mask = self._channel_mask
            if self._start_network_steering_with_backoff():
                return self
            fallback_mask = int(self._auto_join_channel_mask)
            if preferred_mask is None or int(preferred_mask) != fallback_mask:
                if hasattr(self.stack, "set_primary_channel_mask"):
                    _ignore_invalid_state(self.stack.set_primary_channel_mask, int(fallback_mask))
                self._channel_mask = int(fallback_mask)
            if not self._start_network_steering_with_backoff():
                self._mark_commissioning_failure("join", status=116)
            return self
        if not self._start_network_steering_with_backoff():
            self._mark_commissioning_failure("join", status=116)
        return self

    def status(self):
        runtime = {}
        if hasattr(self.stack, "get_network_runtime"):
            try:
                raw_runtime = self.stack.get_network_runtime() or {}
                if isinstance(raw_runtime, dict):
                    runtime = raw_runtime
            except Exception:
                runtime = {}

        try:
            if "short_addr" in runtime:
                short_addr = int(runtime.get("short_addr")) & 0xFFFF
            else:
                short_addr = int(self.stack.get_short_addr()) & 0xFFFF
        except Exception:
            short_addr = None
        try:
            ieee_addr = bytes(self.stack.get_ieee_addr())
        except Exception:
            ieee_addr = None

        runtime_channel = runtime.get("channel", None)
        runtime_pan_id = runtime.get("pan_id", None)
        runtime_ext_pan = runtime.get("extended_pan_id", None)
        if runtime_ext_pan is not None:
            try:
                runtime_ext_pan = bytes(runtime_ext_pan)
            except Exception:
                runtime_ext_pan = None

        return {
            "role": int(self.role),
            "commissioning_mode": str(self.commissioning_mode),
            "registered": bool(self._registered),
            "started": bool(self._started),
            "form_network": bool(self._form_network),
            "short_addr": short_addr,
            "ieee_addr": ieee_addr,
            "ieee_hex": _ieee_to_hex(ieee_addr),
            "channel": None if runtime_channel is None else int(runtime_channel),
            "pan_id": None if runtime_pan_id is None else int(runtime_pan_id) & 0xFFFF,
            "extended_pan_id": runtime_ext_pan,
            "extended_pan_id_hex": _ieee_to_hex(runtime_ext_pan),
            "formed": None if runtime.get("formed", None) is None else bool(runtime.get("formed")),
            "joined": None if runtime.get("joined", None) is None else bool(runtime.get("joined")),
            "auto_join": {
                "channel_mask": int(self._auto_join_channel_mask),
                "join_retry_max": int(self._join_retry_max),
                "join_retry_base_ms": int(self._join_retry_base_ms),
                "join_retry_max_backoff_ms": int(self._join_retry_max_backoff_ms),
                "trigger_count": int(self._join_trigger_count),
                "last_attempt_ms": int(self._join_last_attempt_ms),
                "last_backoff_ms": int(self._join_last_backoff_ms),
                "last_trigger_ok": self._join_last_trigger_ok,
            },
            "self_heal": {
                "policy": self.configure_self_heal(),
                "stats": self.self_heal_stats(),
            },
            "commissioning": self.commissioning_stats(),
            "network_profile": self._network_profile.to_dict(),
            "last_signal": self._last_signal,
            "last_status": self._last_status,
            "components": self.components(),
            "endpoint_ids": self.endpoints(),
            "sensor_state_count": len(self._sensor_state),
            "actuator_state_count": len(self._actuator_state),
            "reporting_policy_count": len(self._reporting_policies),
            "binding_policy_count": len(self._binding_policies),
            "custom_capability_count": len(self._custom_capability_templates),
            "policy_hook_count": len(self._policy_hooks),
        }

    def network_info(self):
        status = self.status()
        return {
            "role": int(status["role"]),
            "commissioning_mode": str(status["commissioning_mode"]),
            "started": bool(status["started"]),
            "form_network": bool(status["form_network"]),
            "short_addr": status["short_addr"],
            "ieee_addr": status["ieee_addr"],
            "ieee_hex": status["ieee_hex"],
            "channel": status.get("channel"),
            "pan_id": status.get("pan_id"),
            "extended_pan_id": status.get("extended_pan_id"),
            "extended_pan_id_hex": status.get("extended_pan_id_hex"),
            "formed": status.get("formed"),
            "joined": status.get("joined"),
            "auto_join": dict(status.get("auto_join") or {}),
            "self_heal": dict(status.get("self_heal") or {}),
            "commissioning": dict(status.get("commissioning") or {}),
            "profile": dict(status["network_profile"]),
        }

    def configure_persistence(self, min_interval_ms=None):
        if min_interval_ms is not None:
            self._persistence_min_interval_ms = int(min_interval_ms)
        return {
            "min_interval_ms": int(self._persistence_min_interval_ms),
            "last_save_ms": int(self._persistence_last_save_ms),
        }

    def dump_node_state(self):
        components = []
        for item in self.components():
            create_method = None
            for planned in self._endpoint_plan:
                if int(planned["endpoint_id"]) == int(item["endpoint_id"]):
                    create_method = planned["create_method"]
                    break
            components.append(
                {
                    "name": item["name"],
                    "kind": item["kind"],
                    "endpoint_id": int(item["endpoint_id"]),
                    "create_method": create_method,
                    "options": dict(item.get("options") or {}),
                }
            )

        reporting_policies = []
        for policy in self.reporting_policies():
            reporting_policies.append(
                {
                    "name": policy["name"],
                    "kind": policy["kind"],
                    "endpoint_id": int(policy["endpoint_id"]),
                    "src_endpoint": int(policy["src_endpoint"]),
                    "dst_short_addr": int(policy["dst_short_addr"]),
                    "dst_endpoint": int(policy["dst_endpoint"]),
                    "entries": [list(entry) for entry in tuple(policy["entries"])],
                }
            )

        binding_policies = []
        for policy in self.binding_policies():
            binding_policies.append(
                {
                    "name": policy["name"],
                    "kind": policy["kind"],
                    "endpoint_id": int(policy["endpoint_id"]),
                    "src_endpoint": int(policy["src_endpoint"]),
                    "clusters": [int(cluster_id) for cluster_id in tuple(policy["clusters"])],
                    "dst_ieee_addr": _ieee_to_hex(policy.get("dst_ieee_addr")),
                    "dst_endpoint": int(policy["dst_endpoint"]),
                    "req_dst_short_addr": int(policy["req_dst_short_addr"]),
                    "src_ieee_addr": _ieee_to_hex(policy.get("src_ieee_addr")),
                    "ias_enroll": bool(policy["ias_enroll"]),
                }
            )

        out = {
            "version": 1,
            "role": int(self.role),
            "commissioning_mode": str(self.commissioning_mode),
            "network_profile": self._network_profile.to_dict(),
            "auto_join_policy": self.configure_auto_join(),
            "self_heal_policy": self.configure_self_heal(),
            "components": components,
            "custom_capabilities": [dict(item) for item in self.custom_capabilities()],
            "sensor_states": [dict(item) for item in self.sensor_states()],
            "actuator_states": [dict(item) for item in self.actuator_states()],
            "reporting_policies": reporting_policies,
            "binding_policies": binding_policies,
            "persistence": self.configure_persistence(),
        }
        if hasattr(self, "sleepy_profile"):
            out["sleepy_profile"] = self.sleepy_profile()
        return out

    def restore_node_state(self, snapshot, merge=False):
        if not isinstance(snapshot, dict):
            raise ValueError("snapshot must be dict")

        if not merge:
            self._endpoint_plan = []
            self._used_endpoints = set()
            self._sensor_state = {}
            self._actuator_state = {}
            self._reporting_policies = {}
            self._binding_policies = {}
            self._custom_capability_templates = {}
            self._custom_capability_aliases = {}

        saved_mode = snapshot.get("commissioning_mode", None)
        if saved_mode is not None:
            try:
                self.commissioning_mode = _infer_commissioning_mode(saved_mode, label="commissioning_mode")
            except Exception:
                pass
        saved_profile = snapshot.get("network_profile", None)
        if isinstance(saved_profile, dict):
            try:
                self._network_profile = NetworkProfile.from_dict(saved_profile)
            except Exception:
                pass
        auto_join_policy = snapshot.get("auto_join_policy", None)
        if isinstance(auto_join_policy, dict):
            self.configure_auto_join(
                auto_join_channel_mask=auto_join_policy.get("auto_join_channel_mask", None),
                join_retry_max=auto_join_policy.get("join_retry_max", None),
                join_retry_base_ms=auto_join_policy.get("join_retry_base_ms", None),
                join_retry_max_backoff_ms=auto_join_policy.get("join_retry_max_backoff_ms", None),
            )
        self_heal_policy = snapshot.get("self_heal_policy", None)
        if isinstance(self_heal_policy, dict):
            self.configure_self_heal(
                enabled=self_heal_policy.get("enabled", None),
                retry_max=self_heal_policy.get("retry_max", None),
                retry_base_ms=self_heal_policy.get("retry_base_ms", None),
                retry_max_backoff_ms=self_heal_policy.get("retry_max_backoff_ms", None),
            )

        for item in tuple(snapshot.get("custom_capabilities", ())):
            self.register_capability(
                name=item.get("name"),
                create_method=item.get("create_method"),
                kind=item.get("kind", None),
                aliases=item.get("aliases", ()),
            )

        for item in tuple(snapshot.get("components", ())):
            endpoint_id = _normalize_endpoint(item.get("endpoint_id"))
            if endpoint_id in self._used_endpoints:
                if merge:
                    continue
                raise ValueError("duplicate endpoint in snapshot: {}".format(endpoint_id))
            kind = str(item.get("kind"))
            create_method = item.get("create_method")
            if not create_method:
                template = _CAPABILITY_TEMPLATES.get(kind, None)
                if template is None:
                    raise ValueError("unknown component kind '{}'".format(kind))
                create_method = template["create_method"]
            self._used_endpoints.add(endpoint_id)
            self._endpoint_plan.append(
                {
                    "kind": kind,
                    "name": str(item.get("name", "{}_{}".format(kind, endpoint_id))),
                    "endpoint_id": int(endpoint_id),
                    "create_method": str(create_method),
                    "options": dict(item.get("options") or {}),
                    "provisioned": False,
                }
            )

        for item in tuple(snapshot.get("sensor_states", ())):
            endpoint_id = _normalize_endpoint(item.get("endpoint_id"))
            capability = str(item.get("capability"))
            self._sensor_state[(int(endpoint_id), capability)] = {
                "endpoint_id": int(endpoint_id),
                "capability": capability,
                "value": item.get("value"),
                "raw_value": item.get("raw_value"),
                "updated_ms": int(item.get("updated_ms", 0)),
            }

        for item in tuple(snapshot.get("actuator_states", ())):
            endpoint_id = _normalize_endpoint(item.get("endpoint_id"))
            field = str(item.get("field"))
            self._actuator_state[(int(endpoint_id), field)] = {
                "endpoint_id": int(endpoint_id),
                "name": str(item.get("name", "")),
                "capability": str(item.get("capability", "")),
                "field": field,
                "value": item.get("value"),
                "raw_value": item.get("raw_value"),
                "updated_ms": int(item.get("updated_ms", 0)),
                "changed": bool(item.get("changed", False)),
                "sent": bool(item.get("sent", False)),
            }

        for item in tuple(snapshot.get("reporting_policies", ())):
            endpoint_id = _normalize_endpoint(item.get("endpoint_id"))
            self._reporting_policies[int(endpoint_id)] = {
                "name": str(item.get("name", "")),
                "kind": str(item.get("kind", "")),
                "endpoint_id": int(endpoint_id),
                "src_endpoint": int(item.get("src_endpoint", endpoint_id)),
                "dst_short_addr": int(item.get("dst_short_addr", 0x0000)),
                "dst_endpoint": int(item.get("dst_endpoint", 1)),
                "entries": _normalize_reporting_entries(item.get("entries", ())),
            }

        for item in tuple(snapshot.get("binding_policies", ())):
            endpoint_id = _normalize_endpoint(item.get("endpoint_id"))
            dst_ieee_addr = item.get("dst_ieee_addr", None)
            src_ieee_addr = item.get("src_ieee_addr", None)
            self._binding_policies[int(endpoint_id)] = {
                "name": str(item.get("name", "")),
                "kind": str(item.get("kind", "")),
                "endpoint_id": int(endpoint_id),
                "src_endpoint": int(item.get("src_endpoint", endpoint_id)),
                "clusters": _normalize_cluster_ids(item.get("clusters", ())),
                "dst_ieee_addr": None if dst_ieee_addr is None else _normalize_ieee_addr(dst_ieee_addr),
                "dst_endpoint": int(item.get("dst_endpoint", 1)),
                "req_dst_short_addr": int(item.get("req_dst_short_addr", 0x0000)),
                "src_ieee_addr": None if src_ieee_addr is None else _normalize_ieee_addr(src_ieee_addr),
                "ias_enroll": bool(item.get("ias_enroll", True)),
            }

        persistence = snapshot.get("persistence", None)
        if isinstance(persistence, dict):
            self.configure_persistence(min_interval_ms=persistence.get("min_interval_ms", None))

        sleepy_profile = snapshot.get("sleepy_profile", None)
        if isinstance(sleepy_profile, dict) and hasattr(self, "configure_sleepy_profile"):
            self.configure_sleepy_profile(
                sleepy=sleepy_profile.get("sleepy", None),
                keep_alive_ms=sleepy_profile.get("keep_alive_ms", None),
                poll_interval_ms=sleepy_profile.get("poll_interval_ms", None),
                wake_window_ms=sleepy_profile.get("wake_window_ms", None),
                checkin_interval_ms=sleepy_profile.get("checkin_interval_ms", None),
                low_power_reporting=sleepy_profile.get("low_power_reporting", None),
            )
            if "last_wake_ms" in sleepy_profile:
                self._last_wake_ms = int(sleepy_profile["last_wake_ms"])
            if "last_poll_ms" in sleepy_profile:
                self._last_poll_ms = int(sleepy_profile["last_poll_ms"])
            if "last_keepalive_ms" in sleepy_profile:
                self._last_keepalive_ms = int(sleepy_profile["last_keepalive_ms"])

        return {
            "components": len(self._endpoint_plan),
            "sensor_states": len(self._sensor_state),
            "actuator_states": len(self._actuator_state),
            "reporting_policies": len(self._reporting_policies),
            "binding_policies": len(self._binding_policies),
        }

    def save_node_state(self, path="uzigbee_node_state.json", force=False):
        now_ms = _ticks_ms()
        elapsed = int(now_ms) - int(self._persistence_last_save_ms)
        if not force and elapsed < int(self._persistence_min_interval_ms):
            return {
                "saved": False,
                "path": str(path),
                "reason": "throttled",
                "elapsed_ms": int(elapsed),
                "min_interval_ms": int(self._persistence_min_interval_ms),
            }

        snapshot = self.dump_node_state()
        payload = json.dumps(snapshot)
        with open(path, "w") as handle:
            handle.write(payload)
        self._persistence_last_save_ms = int(now_ms)
        return {
            "saved": True,
            "path": str(path),
            "bytes": int(len(payload)),
            "saved_ms": int(self._persistence_last_save_ms),
        }

    def load_node_state(self, path="uzigbee_node_state.json", merge=False):
        with open(path, "r") as handle:
            payload = handle.read()
        snapshot = json.loads(payload)
        restored = self.restore_node_state(snapshot, merge=merge)
        restored["loaded"] = True
        restored["path"] = str(path)
        return restored

    def components(self):
        out = []
        for item in self._endpoint_plan:
            out.append(
                {
                    "name": item["name"],
                    "kind": item["kind"],
                    "endpoint_id": int(item["endpoint_id"]),
                    "options": dict(item.get("options") or {}),
                    "provisioned": bool(item.get("provisioned", False)),
                }
            )
        out.sort(key=lambda row: int(row["endpoint_id"]))
        return tuple(out)

    def endpoints(self):
        return tuple(int(item["endpoint_id"]) for item in self.components())

    def describe(self):
        info = self.status()
        info["endpoint_ids"] = self.endpoints()
        return info


class Router(_NodeBase):
    """High-level Router node with chainable `add_*` endpoint helpers."""

    __slots__ = ()

    def __init__(
        self,
        stack=None,
        auto_register=True,
        channel=None,
        channel_mask=None,
        auto_join_channel_mask=_DEFAULT_AUTO_JOIN_CHANNEL_MASK,
        pan_id=None,
        extended_pan_id=None,
        commissioning_mode="auto",
        join_retry_max=_JOIN_RETRY_MAX_DEFAULT,
        join_retry_base_ms=_JOIN_RETRY_BASE_MS_DEFAULT,
        join_retry_max_backoff_ms=_JOIN_RETRY_MAX_BACKOFF_MS_DEFAULT,
        self_heal_enabled=True,
        self_heal_retry_max=_SELF_HEAL_RETRY_MAX_DEFAULT,
        self_heal_retry_base_ms=_SELF_HEAL_RETRY_BASE_MS_DEFAULT,
        self_heal_retry_max_backoff_ms=_SELF_HEAL_RETRY_MAX_BACKOFF_MS_DEFAULT,
    ):
        super().__init__(
            role=ROLE_ROUTER,
            stack=stack,
            auto_register=auto_register,
            channel=channel,
            channel_mask=channel_mask,
            auto_join_channel_mask=auto_join_channel_mask,
            pan_id=pan_id,
            extended_pan_id=extended_pan_id,
            commissioning_mode=commissioning_mode,
            join_retry_max=join_retry_max,
            join_retry_base_ms=join_retry_base_ms,
            join_retry_max_backoff_ms=join_retry_max_backoff_ms,
            self_heal_enabled=self_heal_enabled,
            self_heal_retry_max=self_heal_retry_max,
            self_heal_retry_base_ms=self_heal_retry_base_ms,
            self_heal_retry_max_backoff_ms=self_heal_retry_max_backoff_ms,
        )

    def add_light(self, endpoint_id=None, name=None, dimmable=False, color=False):
        return self.add(
            "light",
            endpoint_id=endpoint_id,
            name=name,
            dimmable=bool(dimmable),
            color=bool(color),
        )

    def add_switch(self, endpoint_id=None, name=None, dimmable=False):
        return self.add("switch", endpoint_id=endpoint_id, name=name, dimmable=bool(dimmable))

    def add_temperature_sensor(self, endpoint_id=None, name=None):
        return self.add("temperature_sensor", endpoint_id=endpoint_id, name=name)

    def add_humidity_sensor(self, endpoint_id=None, name=None):
        return self.add("humidity_sensor", endpoint_id=endpoint_id, name=name)

    def add_pressure_sensor(self, endpoint_id=None, name=None):
        return self.add("pressure_sensor", endpoint_id=endpoint_id, name=name)

    def add_climate_sensor(self, endpoint_id=None, name=None):
        return self.add("climate_sensor", endpoint_id=endpoint_id, name=name)

    def add_occupancy_sensor(self, endpoint_id=None, name=None):
        return self.add("occupancy_sensor", endpoint_id=endpoint_id, name=name)

    def add_contact_sensor(self, endpoint_id=None, name=None):
        return self.add("contact_sensor", endpoint_id=endpoint_id, name=name)

    def add_motion_sensor(self, endpoint_id=None, name=None):
        return self.add("motion_sensor", endpoint_id=endpoint_id, name=name)

    def add_power_outlet(self, endpoint_id=None, name=None, with_metering=False):
        return self.add(
            "power_outlet",
            endpoint_id=endpoint_id,
            name=name,
            with_metering=bool(with_metering),
        )

    def add_door_lock(self, endpoint_id=None, name=None):
        return self.add("door_lock", endpoint_id=endpoint_id, name=name)

    def add_thermostat(self, endpoint_id=None, name=None):
        return self.add("thermostat", endpoint_id=endpoint_id, name=name)

    def add_window_covering(self, endpoint_id=None, name=None):
        return self.add("window_covering", endpoint_id=endpoint_id, name=name)

    def add_ias_zone(self, endpoint_id=None, name=None, zone_type=IAS_ZONE_TYPE_CONTACT_SWITCH):
        return self.add("ias_zone", endpoint_id=endpoint_id, name=name, zone_type=int(zone_type))


class EndDevice(Router):
    """High-level EndDevice node with optional sleepy profile metadata."""

    __slots__ = (
        "sleepy",
        "keep_alive_ms",
        "poll_interval_ms",
        "wake_window_ms",
        "checkin_interval_ms",
        "low_power_reporting",
        "_last_wake_ms",
        "_last_poll_ms",
        "_last_keepalive_ms",
    )

    def __init__(
        self,
        stack=None,
        auto_register=True,
        channel=None,
        channel_mask=None,
        auto_join_channel_mask=_DEFAULT_AUTO_JOIN_CHANNEL_MASK,
        pan_id=None,
        extended_pan_id=None,
        commissioning_mode="auto",
        join_retry_max=_JOIN_RETRY_MAX_DEFAULT,
        join_retry_base_ms=_JOIN_RETRY_BASE_MS_DEFAULT,
        join_retry_max_backoff_ms=_JOIN_RETRY_MAX_BACKOFF_MS_DEFAULT,
        self_heal_enabled=True,
        self_heal_retry_max=_SELF_HEAL_RETRY_MAX_DEFAULT,
        self_heal_retry_base_ms=_SELF_HEAL_RETRY_BASE_MS_DEFAULT,
        self_heal_retry_max_backoff_ms=_SELF_HEAL_RETRY_MAX_BACKOFF_MS_DEFAULT,
        sleepy=False,
        keep_alive_ms=3000,
        poll_interval_ms=1000,
        wake_window_ms=5000,
        checkin_interval_ms=60000,
        low_power_reporting=True,
    ):
        super().__init__(
            stack=stack,
            auto_register=auto_register,
            channel=channel,
            channel_mask=channel_mask,
            auto_join_channel_mask=auto_join_channel_mask,
            pan_id=pan_id,
            extended_pan_id=extended_pan_id,
            commissioning_mode=commissioning_mode,
            join_retry_max=join_retry_max,
            join_retry_base_ms=join_retry_base_ms,
            join_retry_max_backoff_ms=join_retry_max_backoff_ms,
            self_heal_enabled=self_heal_enabled,
            self_heal_retry_max=self_heal_retry_max,
            self_heal_retry_base_ms=self_heal_retry_base_ms,
            self_heal_retry_max_backoff_ms=self_heal_retry_max_backoff_ms,
        )
        self.role = ROLE_END_DEVICE
        self.sleepy = bool(sleepy)
        self.keep_alive_ms = int(keep_alive_ms)
        self.poll_interval_ms = int(poll_interval_ms)
        self.wake_window_ms = int(wake_window_ms)
        self.checkin_interval_ms = int(checkin_interval_ms)
        self.low_power_reporting = bool(low_power_reporting)
        now_ms = _ticks_ms()
        self._last_wake_ms = int(now_ms)
        self._last_poll_ms = int(now_ms)
        self._last_keepalive_ms = int(now_ms)

    def configure_sleepy(
        self,
        sleepy=None,
        keep_alive_ms=None,
        poll_interval_ms=None,
        wake_window_ms=None,
        checkin_interval_ms=None,
        low_power_reporting=None,
    ):
        if sleepy is not None:
            self.sleepy = bool(sleepy)
        if keep_alive_ms is not None:
            self.keep_alive_ms = int(keep_alive_ms)
        if poll_interval_ms is not None:
            self.poll_interval_ms = int(poll_interval_ms)
        if wake_window_ms is not None:
            self.wake_window_ms = int(wake_window_ms)
        if checkin_interval_ms is not None:
            self.checkin_interval_ms = int(checkin_interval_ms)
        if low_power_reporting is not None:
            self.low_power_reporting = bool(low_power_reporting)
        return self.sleepy_profile()

    def configure_sleepy_profile(
        self,
        sleepy=None,
        keep_alive_ms=None,
        poll_interval_ms=None,
        wake_window_ms=None,
        checkin_interval_ms=None,
        low_power_reporting=None,
    ):
        return self.configure_sleepy(
            sleepy=sleepy,
            keep_alive_ms=keep_alive_ms,
            poll_interval_ms=poll_interval_ms,
            wake_window_ms=wake_window_ms,
            checkin_interval_ms=checkin_interval_ms,
            low_power_reporting=low_power_reporting,
        )

    def sleepy_profile(self):
        return {
            "sleepy": bool(self.sleepy),
            "keep_alive_ms": int(self.keep_alive_ms),
            "poll_interval_ms": int(self.poll_interval_ms),
            "wake_window_ms": int(self.wake_window_ms),
            "checkin_interval_ms": int(self.checkin_interval_ms),
            "low_power_reporting": bool(self.low_power_reporting),
            "last_wake_ms": int(self._last_wake_ms),
            "last_poll_ms": int(self._last_poll_ms),
            "last_keepalive_ms": int(self._last_keepalive_ms),
        }

    def mark_wake(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        self._last_wake_ms = int(now_ms)
        return int(self._last_wake_ms)

    def mark_poll(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        self._last_poll_ms = int(now_ms)
        return int(self._last_poll_ms)

    def mark_keepalive(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        self._last_keepalive_ms = int(now_ms)
        return int(self._last_keepalive_ms)

    def wake_window_active(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        if not self.sleepy:
            return True
        return int(now_ms) - int(self._last_wake_ms) <= int(self.wake_window_ms)

    def should_poll(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        if not self.sleepy:
            return False
        elapsed = int(now_ms) - int(self._last_poll_ms)
        return elapsed >= int(self.poll_interval_ms)

    def should_keepalive(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        if not self.sleepy:
            return False
        elapsed = int(now_ms) - int(self._last_keepalive_ms)
        return elapsed >= int(self.keep_alive_ms)

    def next_poll_due_ms(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        due = int(self._last_poll_ms) + int(self.poll_interval_ms)
        remaining = int(due) - int(now_ms)
        return 0 if remaining < 0 else int(remaining)

    def next_keepalive_due_ms(self, now_ms=None):
        if now_ms is None:
            now_ms = _ticks_ms()
        due = int(self._last_keepalive_ms) + int(self.keep_alive_ms)
        remaining = int(due) - int(now_ms)
        return 0 if remaining < 0 else int(remaining)

    def configure_reporting_policy(
        self,
        capability=None,
        endpoint_id=None,
        preset=None,
        overrides=None,
        dst_short_addr=0x0000,
        dst_endpoint=1,
        src_endpoint=None,
        auto_apply=False,
        low_power=None,
    ):
        configured = super().configure_reporting_policy(
            capability=capability,
            endpoint_id=endpoint_id,
            preset=preset,
            overrides=overrides,
            dst_short_addr=dst_short_addr,
            dst_endpoint=dst_endpoint,
            src_endpoint=src_endpoint,
            auto_apply=False,
        )
        enable_low_power = bool(self.sleepy and self.low_power_reporting)
        if low_power is not None:
            enable_low_power = bool(low_power)
        if enable_low_power:
            for item in configured:
                item_endpoint = int(item["endpoint_id"])
                policy = self._reporting_policies.get(item_endpoint, None)
                if policy is None:
                    continue
                tuned_entries = _tune_low_power_reporting_entries(policy["entries"])
                policy = dict(policy)
                policy["entries"] = tuple(tuned_entries)
                self._reporting_policies[item_endpoint] = policy
        out = []
        for item in configured:
            out.append(dict(self._reporting_policies[int(item["endpoint_id"])]))
        if auto_apply:
            for item in tuple(out):
                self.apply_reporting_policy(endpoint_id=int(item["endpoint_id"]))
        return tuple(out)

    def status(self):
        out = super().status()
        out.update(self.sleepy_profile())
        out["wake_window_active"] = bool(self.wake_window_active())
        out["next_poll_due_ms"] = int(self.next_poll_due_ms())
        out["next_keepalive_due_ms"] = int(self.next_keepalive_due_ms())
        return out
