"""High-level coordinator/network API with auto-discovery and device registry."""

from .core import (
    ATTR_COLOR_CONTROL_COLOR_TEMPERATURE,
    ATTR_COLOR_CONTROL_CURRENT_X,
    ATTR_COLOR_CONTROL_CURRENT_Y,
    ATTR_DOOR_LOCK_LOCK_STATE,
    ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER,
    ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT,
    ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE,
    ATTR_IAS_ZONE_STATUS,
    ATTR_LEVEL_CONTROL_CURRENT_LEVEL,
    ATTR_OCCUPANCY_SENSING_OCCUPANCY,
    ATTR_ON_OFF_ON_OFF,
    ATTR_PRESSURE_MEASUREMENT_VALUE,
    ATTR_REL_HUMIDITY_MEASUREMENT_VALUE,
    ATTR_TEMP_MEASUREMENT_VALUE,
    ATTR_THERMOSTAT_LOCAL_TEMPERATURE,
    ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
    ATTR_THERMOSTAT_SYSTEM_MODE,
    ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE,
    ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE,
    CLUSTER_ID_COLOR_CONTROL,
    CLUSTER_ID_DOOR_LOCK,
    CLUSTER_ID_ELECTRICAL_MEASUREMENT,
    CLUSTER_ID_IAS_ZONE,
    CLUSTER_ID_LEVEL_CONTROL,
    CLUSTER_ID_OCCUPANCY_SENSING,
    CLUSTER_ID_ON_OFF,
    CLUSTER_ID_PRESSURE_MEASUREMENT,
    CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
    CLUSTER_ID_TEMP_MEASUREMENT,
    CLUSTER_ID_THERMOSTAT,
    CLUSTER_ID_WINDOW_COVERING,
    CLUSTER_ROLE_SERVER,
    CMD_DOOR_LOCK_LOCK_DOOR,
    CMD_DOOR_LOCK_UNLOCK_DOOR,
    CMD_ON_OFF_OFF,
    CMD_ON_OFF_ON,
    CMD_ON_OFF_TOGGLE,
    IAS_ZONE_STATUS_ALARM1,
    SIGNAL_DEVICE_ASSOCIATED,
    SIGNAL_DEVICE_ANNCE,
    SIGNAL_DEVICE_AUTHORIZED,
    SIGNAL_DEVICE_FIRST_START,
    SIGNAL_DEVICE_REBOOT,
    SIGNAL_DEVICE_UPDATE,
    SIGNAL_FORMATION,
    SIGNAL_FORMATION_CANCELLED,
    SIGNAL_PANID_CONFLICT_DETECTED,
    SIGNAL_STEERING,
    SIGNAL_STEERING_CANCELLED,
    ZigbeeError,
    ZigbeeStack,
)
from . import reporting as _reporting
from .commissioning import (
    NETWORK_MODE_AUTO,
    NETWORK_MODE_FIXED,
    NETWORK_MODE_GUIDED,
    NetworkProfile,
    infer_mode as _infer_network_mode,
    mode_profile_source as _mode_profile_source,
)
from .zcl import DATA_TYPE_S16, DATA_TYPE_U8, DATA_TYPE_U16

try:
    import time as _time
except ImportError:
    _time = None

try:
    import math as _math
except ImportError:
    _math = None

try:
    import network as _mp_network
except ImportError:
    _mp_network = None

try:
    import json as _json
except ImportError:
    _json = None


ROLE_COORDINATOR = 0
ESP_ERR_INVALID_STATE = 259

_JOIN_SIGNALS = {
    int(SIGNAL_DEVICE_ASSOCIATED),
    int(SIGNAL_DEVICE_ANNCE),
    int(SIGNAL_DEVICE_UPDATE),
    int(SIGNAL_DEVICE_AUTHORIZED),
}

_NETWORK_PROFILE_SYNC_SIGNALS = {
    int(SIGNAL_FORMATION),
    int(SIGNAL_STEERING),
    int(SIGNAL_DEVICE_FIRST_START),
    int(SIGNAL_DEVICE_REBOOT),
}

_STEERING_FAILURE_SIGNALS = {
    int(SIGNAL_STEERING),
    int(SIGNAL_STEERING_CANCELLED),
    int(SIGNAL_FORMATION_CANCELLED),
}

_DISCOVERY_TIMEOUT_MS_MIN = 500
_DISCOVERY_TIMEOUT_MS_MAX = 120000
_DISCOVERY_POLL_MS_MIN = 50
_DISCOVERY_POLL_MS_MAX = 10000
_STATE_TTL_MS_MIN = 0
_STATE_TTL_MS_MAX = 86400000
_STATE_CACHE_MAX_MIN = 8
_STATE_CACHE_MAX_MAX = 512
_STATE_CACHE_MAX_DEFAULT = 64
_OFFLINE_AFTER_MS_MIN = 0
_OFFLINE_AFTER_MS_MAX = 86400000
_CHANNEL_MASK_ALLOWED = 0
for _ch in range(11, 27):
    _CHANNEL_MASK_ALLOWED |= 1 << _ch
_DEFAULT_AUTO_CHANNEL_PREFERRED = (15, 20, 25, 11, 14, 19, 24, 12, 13, 16, 17, 18, 21, 22, 23, 26)
_SELF_HEAL_RETRY_MAX_DEFAULT = 2
_SELF_HEAL_RETRY_BASE_MS_DEFAULT = 100
_SELF_HEAL_RETRY_MAX_BACKOFF_MS_DEFAULT = 2000
_COMMISSIONING_TIMEOUT_STATUSES = (110, 116, -110, -116)

_FEATURE_BY_CLUSTER = {
    int(CLUSTER_ID_ON_OFF): "on_off",
    int(CLUSTER_ID_LEVEL_CONTROL): "level",
    int(CLUSTER_ID_COLOR_CONTROL): "color",
    int(CLUSTER_ID_TEMP_MEASUREMENT): "temperature",
    int(CLUSTER_ID_REL_HUMIDITY_MEASUREMENT): "humidity",
    int(CLUSTER_ID_PRESSURE_MEASUREMENT): "pressure",
    int(CLUSTER_ID_OCCUPANCY_SENSING): "occupancy",
    int(CLUSTER_ID_DOOR_LOCK): "lock",
    int(CLUSTER_ID_WINDOW_COVERING): "cover",
    int(CLUSTER_ID_IAS_ZONE): "ias_zone",
    int(CLUSTER_ID_THERMOSTAT): "thermostat",
    int(CLUSTER_ID_ELECTRICAL_MEASUREMENT): "energy",
}

_AUTO_REPORTING_PRESET_COVER = (
    (
        int(CLUSTER_ID_WINDOW_COVERING),
        int(ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE),
        int(DATA_TYPE_U8),
        1,
        300,
        1,
    ),
    (
        int(CLUSTER_ID_WINDOW_COVERING),
        int(ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE),
        int(DATA_TYPE_U8),
        1,
        300,
        1,
    ),
)

_AUTO_REPORTING_PRESET_ENERGY = (
    (
        int(CLUSTER_ID_ELECTRICAL_MEASUREMENT),
        int(ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER),
        int(DATA_TYPE_S16),
        5,
        300,
        1,
    ),
    (
        int(CLUSTER_ID_ELECTRICAL_MEASUREMENT),
        int(ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE),
        int(DATA_TYPE_U16),
        5,
        300,
        1,
    ),
    (
        int(CLUSTER_ID_ELECTRICAL_MEASUREMENT),
        int(ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT),
        int(DATA_TYPE_U16),
        5,
        300,
        1,
    ),
)


def _ticks_ms():
    if _time is None:
        return 0
    if hasattr(_time, "ticks_ms"):
        return int(_time.ticks_ms())
    return int(_time.time() * 1000)


def _ticks_add(base, delta):
    if _time is not None and hasattr(_time, "ticks_add"):
        return int(_time.ticks_add(int(base), int(delta)))
    return int(base) + int(delta)


def _ticks_diff(a, b):
    if _time is not None and hasattr(_time, "ticks_diff"):
        return int(_time.ticks_diff(int(a), int(b)))
    return int(a) - int(b)


def _sleep_ms(ms):
    ms = int(ms)
    if ms <= 0 or _time is None:
        return
    if hasattr(_time, "sleep_ms"):
        _time.sleep_ms(ms)
        return
    _time.sleep(ms / 1000.0)


def _safe_bool(value):
    return bool(value)


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


def _ignore_invalid_state(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except OSError as exc:
        if exc.args and int(exc.args[0]) == ESP_ERR_INVALID_STATE:
            return None
        raise


def _error_repr(exc):
    if exc is None:
        return None
    try:
        return "{}:{}".format(type(exc).__name__, str(exc))
    except Exception:
        return "error"


def _clamp_int(value, min_value, max_value):
    value = int(value)
    if value < int(min_value):
        return int(min_value)
    if value > int(max_value):
        return int(max_value)
    return value


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
    mask = int(channel_mask or 0)
    out = []
    for channel in range(11, 27):
        if (mask & (1 << channel)) != 0:
            out.append(int(channel))
    return tuple(out)


def _channel_mask_from_channels(channels):
    mask = 0
    for channel in tuple(channels or ()):
        channel = int(channel)
        if channel < 11 or channel > 26:
            raise ValueError("channel must be in range 11..26")
        mask |= int(1 << channel)
    if mask <= 0:
        raise ValueError("channel set must not be empty")
    return int(mask)


def _normalize_channel_list(name, channels, default=()):
    if channels is None:
        channels = default
    out = []
    seen = set()
    for raw in tuple(channels or ()):
        channel = int(raw)
        if channel < 11 or channel > 26:
            raise ValueError("{} contains invalid channel {}".format(name, channel))
        if channel in seen:
            continue
        seen.add(channel)
        out.append(channel)
    return tuple(out)


def _zigbee_channel_to_mhz(channel):
    return float(2405 + (int(channel) - 11) * 5)


def _wifi_channel_to_mhz(channel):
    return float(2412 + (int(channel) - 1) * 5)


def _wifi_overlap_factor(zigbee_channel, wifi_channel):
    delta = abs(_zigbee_channel_to_mhz(zigbee_channel) - _wifi_channel_to_mhz(wifi_channel))
    if delta >= 20.0:
        return 0.0
    if delta <= 2.0:
        return 1.0
    # Triangular attenuation between 2 and 20 MHz.
    return float((20.0 - delta) / 18.0)


def _rssi_weight_dbm(rssi_dbm):
    rssi = int(rssi_dbm)
    if _math is not None and hasattr(_math, "pow"):
        return float(_math.pow(10.0, rssi / 10.0))
    # Fallback approximation for environments without floating math.
    clamped = _clamp_int(rssi, -100, -20)
    return float(101 + clamped)


def _channel_compat_penalty(channel):
    channel = int(channel)
    # Favor interoperability channels common in professional coordinator defaults.
    if channel in (11, 15, 20, 25):
        return 0.0
    if channel == 26:
        return 0.0005
    return 0.0001


def _scan_wifi_channels(scan_fn=None):
    if callable(scan_fn):
        raw_rows = scan_fn() or ()
    else:
        if _mp_network is None:
            return ()
        try:
            sta = _mp_network.WLAN(_mp_network.STA_IF)
        except Exception:
            return ()
        was_active = False
        try:
            was_active = bool(sta.active())
        except Exception:
            was_active = False
        if not was_active:
            try:
                sta.active(True)
            except Exception:
                return ()
        try:
            raw_rows = sta.scan() or ()
        except Exception:
            raw_rows = ()
        finally:
            if not was_active:
                try:
                    sta.active(False)
                except Exception:
                    pass

    out = []
    for row in tuple(raw_rows):
        try:
            wifi_channel = int(row[2])
            rssi = int(row[3])
        except Exception:
            continue
        if wifi_channel < 1 or wifi_channel > 14:
            continue
        out.append((wifi_channel, rssi))
    return tuple(out)


def _score_channels_with_wifi(candidates, wifi_rows):
    scores = {}
    for channel in tuple(candidates or ()):
        score = _channel_compat_penalty(int(channel))
        for wifi_channel, rssi in tuple(wifi_rows or ()):
            overlap = _wifi_overlap_factor(int(channel), int(wifi_channel))
            if overlap <= 0.0:
                continue
            score += _rssi_weight_dbm(int(rssi)) * overlap
        scores[int(channel)] = float(score)
    return scores


def _select_best_channel(candidates, preferred, wifi_rows):
    channels = tuple(candidates or ())
    if not channels:
        raise ZigbeeError("auto channel candidates are empty")
    scores = _score_channels_with_wifi(channels, wifi_rows)
    preferred_order = {int(channel): idx for idx, channel in enumerate(tuple(preferred or ()))}
    default_rank = int(len(preferred_order) + 100)
    ranked = sorted(
        channels,
        key=lambda channel: (
            float(scores.get(int(channel), 0.0)),
            int(preferred_order.get(int(channel), default_rank)),
            int(channel),
        ),
    )
    selected = int(ranked[0])
    return {
        "selected_channel": selected,
        "selected_channel_mask": int(1 << selected),
        "scores": {int(channel): float(scores.get(int(channel), 0.0)) for channel in channels},
        "wifi_scan_count": int(len(tuple(wifi_rows or ()))),
    }


def _normalize_pan_id(pan_id):
    if pan_id is None:
        return None
    pan_id = int(pan_id)
    if pan_id <= 0 or pan_id >= 0xFFFF:
        raise ValueError("pan_id must be in range 0x0001..0xFFFE")
    return int(pan_id)


def _normalize_extended_pan_id(extended_pan_id):
    if extended_pan_id is None:
        return None
    return _normalize_ieee_addr(extended_pan_id)


def _normalize_stale_policy(value):
    policy = str(value or "allow").strip().lower()
    if policy not in ("allow", "refresh", "raise"):
        raise ValueError("invalid stale_read_policy: {}".format(value))
    return policy


def _prune_cache_map(cache, meta, max_items):
    max_items = _clamp_int(max_items, _STATE_CACHE_MAX_MIN, _STATE_CACHE_MAX_MAX)
    while len(cache) > int(max_items):
        oldest_key = None
        oldest_ms = None
        for key in cache.keys():
            row = meta.get(key)
            updated_ms = 0
            if isinstance(row, dict):
                updated_ms = int(row.get("updated_ms", 0))
            if oldest_ms is None or updated_ms < oldest_ms:
                oldest_ms = updated_ms
                oldest_key = key
        if oldest_key is None:
            try:
                oldest_key = next(iter(cache))
            except Exception:
                break
        cache.pop(oldest_key, None)
        meta.pop(oldest_key, None)


def _state_key_to_text(key):
    if len(key) == 2:
        return "{}:{}".format(int(key[0]), int(key[1]))
    if len(key) == 3:
        return "{}:{}:{}".format(int(key[0]), int(key[1]), int(key[2]))
    raise ValueError("unsupported state key format")


def _state_key_from_text(key_text):
    try:
        parts = str(key_text).split(":")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
        if len(parts) == 3:
            return int(parts[0]), int(parts[1]), int(parts[2])
        return None
    except Exception:
        return None


def _ieee_to_hex(ieee_addr):
    if ieee_addr is None:
        return None
    return "".join("{:02x}".format(int(b)) for b in bytes(ieee_addr))


def _normalize_ieee_addr(value):
    if value is None:
        return None
    if isinstance(value, str):
        compact = value.strip().lower().replace(":", "").replace("-", "").replace(" ", "")
        if len(compact) != 16:
            raise ValueError("ieee address hex string must have 16 hex chars")
        try:
            return bytes.fromhex(compact)
        except Exception:
            raise ValueError("invalid ieee address hex string")
    try:
        out = bytes(value)
    except Exception:
        raise ValueError("ieee address must be bytes-like or hex string")
    if len(out) != 8:
        raise ValueError("ieee address must be 8 bytes")
    return out


def _extract_simple_descriptor(row):
    row = row or {}
    endpoint = int(row.get("endpoint", 0))
    snapshot = row.get("snapshot") or {}
    simple_desc = snapshot.get("simple_desc") or {}
    if int(simple_desc.get("endpoint", endpoint)) > 0:
        endpoint = int(simple_desc.get("endpoint", endpoint))
    return endpoint, simple_desc


class DeviceIdentity:
    """User-facing immutable identity snapshot of discovered remote device."""

    __slots__ = (
        "short_addr",
        "ieee_addr",
        "manufacturer_code",
        "endpoints",
        "primary_endpoint",
        "profile_id",
        "device_id",
        "device_version",
        "power_source",
        "power_source_level",
        "_by_endpoint",
    )

    def __init__(
        self,
        short_addr,
        ieee_addr=None,
        manufacturer_code=None,
        by_endpoint=None,
        power_source=None,
        power_source_level=None,
    ):
        self.short_addr = int(short_addr) & 0xFFFF
        self.ieee_addr = _normalize_ieee_addr(ieee_addr) if ieee_addr is not None else None
        self.manufacturer_code = None if manufacturer_code is None else int(manufacturer_code)
        by_endpoint = dict(by_endpoint or {})
        endpoint_ids = sorted(int(endpoint) for endpoint in by_endpoint.keys())
        self.endpoints = tuple(endpoint_ids)
        self.primary_endpoint = int(endpoint_ids[0]) if endpoint_ids else None
        self.profile_id = None
        self.device_id = None
        self.device_version = None
        if self.primary_endpoint is not None:
            primary = by_endpoint.get(int(self.primary_endpoint), {})
            self.profile_id = None if primary.get("profile_id") is None else int(primary.get("profile_id"))
            self.device_id = None if primary.get("device_id") is None else int(primary.get("device_id"))
            self.device_version = None if primary.get("device_version") is None else int(primary.get("device_version"))
        self.power_source = None if power_source is None else int(power_source)
        self.power_source_level = None if power_source_level is None else int(power_source_level)
        self._by_endpoint = by_endpoint

    def endpoint(self, endpoint_id=None):
        endpoint_id = self.primary_endpoint if endpoint_id is None else int(endpoint_id)
        if endpoint_id is None:
            return None
        data = self._by_endpoint.get(int(endpoint_id))
        if data is None:
            return None
        return dict(data)

    def to_dict(self):
        endpoints = {}
        for endpoint_id, data in self._by_endpoint.items():
            endpoints[int(endpoint_id)] = dict(data)
        return {
            "short_addr": int(self.short_addr),
            "ieee_addr": _ieee_to_hex(self.ieee_addr),
            "manufacturer_code": self.manufacturer_code,
            "endpoints": tuple(self.endpoints),
            "primary_endpoint": self.primary_endpoint,
            "profile_id": self.profile_id,
            "device_id": self.device_id,
            "device_version": self.device_version,
            "power_source": self.power_source,
            "power_source_level": self.power_source_level,
            "by_endpoint": endpoints,
        }

    @classmethod
    def from_discovery(cls, discovered):
        discovered = discovered or {}
        short_addr = int(discovered.get("short_addr", 0)) & 0xFFFF
        ieee_addr = discovered.get("ieee_addr")
        node_desc = ((discovered.get("node_descriptor") or {}).get("node_desc") or {})
        manufacturer_code = node_desc.get("manufacturer_code")

        by_endpoint = {}
        for row in discovered.get("simple_descriptors", ()):
            endpoint, simple_desc = _extract_simple_descriptor(row)
            if endpoint <= 0:
                continue
            by_endpoint[int(endpoint)] = {
                "endpoint": int(endpoint),
                "profile_id": None if simple_desc.get("profile_id") is None else int(simple_desc.get("profile_id")),
                "device_id": None if simple_desc.get("device_id") is None else int(simple_desc.get("device_id")),
                "device_version": None if simple_desc.get("device_version") is None else int(simple_desc.get("device_version")),
                "input_clusters": tuple(int(cluster_id) for cluster_id in (simple_desc.get("input_clusters") or ())),
                "output_clusters": tuple(int(cluster_id) for cluster_id in (simple_desc.get("output_clusters") or ())),
            }

        power_desc = ((discovered.get("power_descriptor") or {}).get("power_desc") or {})
        return cls(
            short_addr=short_addr,
            ieee_addr=ieee_addr,
            manufacturer_code=manufacturer_code,
            by_endpoint=by_endpoint,
            power_source=power_desc.get("current_power_source"),
            power_source_level=power_desc.get("current_power_source_level"),
        )

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        by_endpoint = {}
        for endpoint_key, endpoint_data in (data.get("by_endpoint") or {}).items():
            try:
                endpoint_id = int(endpoint_key)
            except Exception:
                continue
            endpoint_data = endpoint_data or {}
            by_endpoint[endpoint_id] = {
                "endpoint": int(endpoint_data.get("endpoint", endpoint_id)),
                "profile_id": endpoint_data.get("profile_id"),
                "device_id": endpoint_data.get("device_id"),
                "device_version": endpoint_data.get("device_version"),
                "input_clusters": tuple(int(cluster_id) for cluster_id in (endpoint_data.get("input_clusters") or ())),
                "output_clusters": tuple(int(cluster_id) for cluster_id in (endpoint_data.get("output_clusters") or ())),
            }
        return cls(
            short_addr=int(data.get("short_addr", 0)),
            ieee_addr=data.get("ieee_addr"),
            manufacturer_code=data.get("manufacturer_code"),
            by_endpoint=by_endpoint,
            power_source=data.get("power_source"),
            power_source_level=data.get("power_source_level"),
        )


class DeviceReadProxy:
    __slots__ = ("_device", "_endpoint_id")

    def __init__(self, device, endpoint_id=None):
        self._device = device
        self._endpoint_id = None if endpoint_id is None else int(endpoint_id)

    def _resolve_endpoint(self, cluster_id):
        cluster_id = int(cluster_id)
        if self._endpoint_id is None:
            endpoint = self._device.endpoint_for(cluster_id)
            if endpoint is None:
                raise ZigbeeError(
                    "cluster 0x{:04x} not mapped on device".format(cluster_id)
                )
            return int(endpoint)

        endpoint = int(self._endpoint_id)
        endpoint_clusters = self._device.endpoint_clusters.get(endpoint, {})
        input_clusters = tuple(endpoint_clusters.get("input") or ())
        if cluster_id not in input_clusters:
            raise ZigbeeError(
                "cluster 0x{:04x} not mapped on endpoint {}".format(
                    cluster_id, endpoint
                )
            )
        return endpoint

    def _read_raw(self, cluster_id, attr_id, use_cache=True):
        cluster_id = int(cluster_id)
        attr_id = int(attr_id)
        endpoint = self._resolve_endpoint(cluster_id)
        key = (cluster_id, attr_id)

        if use_cache:
            value = self._device.get_state(
                cluster_id,
                attr_id,
                default=None,
                allow_stale=True,
                endpoint_id=endpoint,
            )
            if value is not None:
                is_stale = self._device._is_state_stale_key(key, endpoint_id=endpoint)
                if is_stale:
                    if self._device.stale_read_policy == "raise":
                        raise ZigbeeError(
                            "stale cached value for endpoint {} cluster 0x{:04x} attr 0x{:04x}".format(
                                endpoint, cluster_id, attr_id
                            )
                        )
                    if self._device.stale_read_policy == "refresh":
                        value = None
                if value is not None:
                    return value

        is_local_device = True
        if hasattr(self._device.stack, "get_short_addr"):
            try:
                local_short = int(self._device.stack.get_short_addr()) & 0xFFFF
                is_local_device = int(self._device.short_addr) == int(local_short)
            except Exception:
                is_local_device = True
        if not is_local_device:
            value = self._device.get_state(
                cluster_id,
                attr_id,
                default=None,
                allow_stale=True,
                endpoint_id=endpoint,
            )
            if value is not None:
                return value
            raise ZigbeeError(
                "remote direct read unsupported without cached value on endpoint {} cluster 0x{:04x} attr 0x{:04x}".format(
                    endpoint, cluster_id, attr_id
                )
            )

        value = self._device.stack.get_attribute(
            endpoint,
            cluster_id,
            attr_id,
            CLUSTER_ROLE_SERVER,
        )
        self._device._write_state(
            key,
            value,
            source="read",
            authoritative=True,
            endpoint_id=endpoint,
        )
        return value

    def on_off(self, use_cache=True):
        return _safe_bool(self._read_raw(CLUSTER_ID_ON_OFF, ATTR_ON_OFF_ON_OFF, use_cache=use_cache))

    def level(self, use_cache=True):
        return int(self._read_raw(CLUSTER_ID_LEVEL_CONTROL, ATTR_LEVEL_CONTROL_CURRENT_LEVEL, use_cache=use_cache))

    def lock_state(self, use_cache=True):
        return int(self._read_raw(CLUSTER_ID_DOOR_LOCK, ATTR_DOOR_LOCK_LOCK_STATE, use_cache=use_cache))

    def temperature_raw(self, use_cache=True):
        return int(self._read_raw(CLUSTER_ID_TEMP_MEASUREMENT, ATTR_TEMP_MEASUREMENT_VALUE, use_cache=use_cache))

    def temperature(self, use_cache=True):
        return float(self.temperature_raw(use_cache=use_cache)) / 100.0

    def humidity_raw(self, use_cache=True):
        return int(self._read_raw(CLUSTER_ID_REL_HUMIDITY_MEASUREMENT, ATTR_REL_HUMIDITY_MEASUREMENT_VALUE, use_cache=use_cache))

    def humidity(self, use_cache=True):
        return float(self.humidity_raw(use_cache=use_cache)) / 100.0

    def pressure(self, use_cache=True):
        return int(self._read_raw(CLUSTER_ID_PRESSURE_MEASUREMENT, ATTR_PRESSURE_MEASUREMENT_VALUE, use_cache=use_cache))

    def occupancy(self, use_cache=True):
        return int(self._read_raw(CLUSTER_ID_OCCUPANCY_SENSING, ATTR_OCCUPANCY_SENSING_OCCUPANCY, use_cache=use_cache))

    def thermostat_temperature_raw(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_THERMOSTAT,
                ATTR_THERMOSTAT_LOCAL_TEMPERATURE,
                use_cache=use_cache,
            )
        )

    def thermostat_temperature(self, use_cache=True):
        raw = self.thermostat_temperature_raw(use_cache=use_cache)
        if raw == -32768:
            return None
        return float(raw) / 100.0

    def thermostat_heating_setpoint_raw(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_THERMOSTAT,
                ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
                use_cache=use_cache,
            )
        )

    def thermostat_heating_setpoint(self, use_cache=True):
        return float(self.thermostat_heating_setpoint_raw(use_cache=use_cache)) / 100.0

    def thermostat_system_mode(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_THERMOSTAT,
                ATTR_THERMOSTAT_SYSTEM_MODE,
                use_cache=use_cache,
            )
        )

    def cover_lift(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_WINDOW_COVERING,
                ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE,
                use_cache=use_cache,
            )
        ) & 0xFF

    def cover_tilt(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_WINDOW_COVERING,
                ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE,
                use_cache=use_cache,
            )
        ) & 0xFF

    def ias_zone_status(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_IAS_ZONE,
                ATTR_IAS_ZONE_STATUS,
                use_cache=use_cache,
            )
        ) & 0xFFFF

    def ias_alarm(self, use_cache=True):
        return bool(self.ias_zone_status(use_cache=use_cache) & int(IAS_ZONE_STATUS_ALARM1))

    def power_w(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_ELECTRICAL_MEASUREMENT,
                ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER,
                use_cache=use_cache,
            )
        )

    def voltage_v(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_ELECTRICAL_MEASUREMENT,
                ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE,
                use_cache=use_cache,
            )
        )

    def current_a(self, use_cache=True):
        raw = int(
            self._read_raw(
                CLUSTER_ID_ELECTRICAL_MEASUREMENT,
                ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT,
                use_cache=use_cache,
            )
        )
        return float(raw) / 1000.0

    def color_x(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_COLOR_CONTROL,
                ATTR_COLOR_CONTROL_CURRENT_X,
                use_cache=use_cache,
            )
        ) & 0xFFFF

    def color_y(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_COLOR_CONTROL,
                ATTR_COLOR_CONTROL_CURRENT_Y,
                use_cache=use_cache,
            )
        ) & 0xFFFF

    def color_xy(self, use_cache=True):
        return (
            int(self.color_x(use_cache=use_cache)),
            int(self.color_y(use_cache=use_cache)),
        )

    def color_temperature(self, use_cache=True):
        return int(
            self._read_raw(
                CLUSTER_ID_COLOR_CONTROL,
                ATTR_COLOR_CONTROL_COLOR_TEMPERATURE,
                use_cache=use_cache,
            )
        ) & 0xFFFF


class DeviceControlProxy:
    __slots__ = ("_device", "_endpoint_id")

    def __init__(self, device, endpoint_id=None):
        self._device = device
        self._endpoint_id = None if endpoint_id is None else int(endpoint_id)

    def _endpoint(self, cluster_id):
        cluster_id = int(cluster_id)
        if self._endpoint_id is None:
            endpoint = self._device.endpoint_for(cluster_id)
            if endpoint is None:
                raise ZigbeeError(
                    "cluster 0x{:04x} not mapped on device".format(cluster_id)
                )
            return int(endpoint)

        endpoint = int(self._endpoint_id)
        endpoint_clusters = self._device.endpoint_clusters.get(endpoint, {})
        input_clusters = tuple(endpoint_clusters.get("input") or ())
        if cluster_id not in input_clusters:
            raise ZigbeeError(
                "cluster 0x{:04x} not mapped on endpoint {}".format(
                    cluster_id, endpoint
                )
            )
        return endpoint

    def _set_attr(self, cluster_id, attr_id, value, check=False):
        endpoint = self._endpoint(cluster_id)
        self._device.stack.set_attribute(
            endpoint,
            int(cluster_id),
            int(attr_id),
            value,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        return endpoint

    def on(self):
        endpoint = self._endpoint(CLUSTER_ID_ON_OFF)
        self._device.stack.send_on_off_cmd(
            self._device.short_addr,
            dst_endpoint=endpoint,
            cmd_id=CMD_ON_OFF_ON,
        )
        self._device._write_state(
            (int(CLUSTER_ID_ON_OFF), int(ATTR_ON_OFF_ON_OFF)),
            True,
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return True

    def off(self):
        endpoint = self._endpoint(CLUSTER_ID_ON_OFF)
        self._device.stack.send_on_off_cmd(
            self._device.short_addr,
            dst_endpoint=endpoint,
            cmd_id=CMD_ON_OFF_OFF,
        )
        self._device._write_state(
            (int(CLUSTER_ID_ON_OFF), int(ATTR_ON_OFF_ON_OFF)),
            False,
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return False

    def toggle(self):
        endpoint = self._endpoint(CLUSTER_ID_ON_OFF)
        self._device.stack.send_on_off_cmd(
            self._device.short_addr,
            dst_endpoint=endpoint,
            cmd_id=CMD_ON_OFF_TOGGLE,
        )
        key = (int(CLUSTER_ID_ON_OFF), int(ATTR_ON_OFF_ON_OFF))
        if key in self._device.state:
            self._device._write_state(
                key,
                not _safe_bool(self._device.state[key]),
                source="control",
                authoritative=False,
                endpoint_id=endpoint,
            )
        return self._device.state.get(key, None)

    def level(self, level, transition_ds=0, with_onoff=True):
        endpoint = self._endpoint(CLUSTER_ID_LEVEL_CONTROL)
        value = int(level)
        if value < 0:
            value = 0
        if value > 254:
            value = 254
        self._device.stack.send_level_cmd(
            self._device.short_addr,
            value,
            dst_endpoint=endpoint,
            transition_ds=int(transition_ds),
            with_onoff=bool(with_onoff),
        )
        self._device._write_state(
            (int(CLUSTER_ID_LEVEL_CONTROL), int(ATTR_LEVEL_CONTROL_CURRENT_LEVEL)),
            value,
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return value

    def lock(self):
        endpoint = self._endpoint(CLUSTER_ID_DOOR_LOCK)
        self._device.stack.send_lock_cmd(
            self._device.short_addr,
            lock=True,
            dst_endpoint=endpoint,
        )
        self._device._write_state(
            (int(CLUSTER_ID_DOOR_LOCK), int(ATTR_DOOR_LOCK_LOCK_STATE)),
            int(CMD_DOOR_LOCK_LOCK_DOOR),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return True

    def unlock(self):
        endpoint = self._endpoint(CLUSTER_ID_DOOR_LOCK)
        self._device.stack.send_lock_cmd(
            self._device.short_addr,
            lock=False,
            dst_endpoint=endpoint,
        )
        self._device._write_state(
            (int(CLUSTER_ID_DOOR_LOCK), int(ATTR_DOOR_LOCK_LOCK_STATE)),
            int(CMD_DOOR_LOCK_UNLOCK_DOOR),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return False

    def thermostat_heating_setpoint(self, celsius, check=False):
        raw = int(round(float(celsius) * 100.0))
        if raw < -27315:
            raw = -27315
        if raw > 32767:
            raw = 32767
        endpoint = self._set_attr(
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
            raw,
            check=check,
        )
        self._device._write_state(
            (int(CLUSTER_ID_THERMOSTAT), int(ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT)),
            int(raw),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return float(raw) / 100.0

    def thermostat_system_mode(self, mode, check=False):
        mode = _clamp_int(mode, 0, 9)
        endpoint = self._set_attr(
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_SYSTEM_MODE,
            mode,
            check=check,
        )
        self._device._write_state(
            (int(CLUSTER_ID_THERMOSTAT), int(ATTR_THERMOSTAT_SYSTEM_MODE)),
            int(mode),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return int(mode)

    def cover_lift(self, percent, check=False):
        percent = _clamp_int(percent, 0, 100)
        endpoint = self._set_attr(
            CLUSTER_ID_WINDOW_COVERING,
            ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE,
            percent,
            check=check,
        )
        self._device._write_state(
            (int(CLUSTER_ID_WINDOW_COVERING), int(ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE)),
            int(percent),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return int(percent)

    def cover_tilt(self, percent, check=False):
        percent = _clamp_int(percent, 0, 100)
        endpoint = self._set_attr(
            CLUSTER_ID_WINDOW_COVERING,
            ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE,
            percent,
            check=check,
        )
        self._device._write_state(
            (int(CLUSTER_ID_WINDOW_COVERING), int(ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE)),
            int(percent),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return int(percent)

    def ias_alarm(self, active, check=False):
        endpoint = self._endpoint(CLUSTER_ID_IAS_ZONE)
        key = (int(CLUSTER_ID_IAS_ZONE), int(ATTR_IAS_ZONE_STATUS))
        current = int(self._device.state.get(key, 0)) & 0xFFFF
        mask = int(IAS_ZONE_STATUS_ALARM1)
        if bool(active):
            status = current | mask
        else:
            status = current & (~mask)
        status &= 0xFFFF
        self._set_attr(
            CLUSTER_ID_IAS_ZONE,
            ATTR_IAS_ZONE_STATUS,
            status,
            check=check,
        )
        self._device._write_state(
            key,
            int(status),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return bool(status & mask)

    def power_w(self, watts, check=False):
        watts = _clamp_int(watts, 0, 0xFFFF)
        endpoint = self._set_attr(
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER,
            watts,
            check=check,
        )
        self._device._write_state(
            (int(CLUSTER_ID_ELECTRICAL_MEASUREMENT), int(ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER)),
            int(watts),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return int(watts)

    def voltage_v(self, volts, check=False):
        volts = _clamp_int(volts, 0, 0xFFFF)
        endpoint = self._set_attr(
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE,
            volts,
            check=check,
        )
        self._device._write_state(
            (int(CLUSTER_ID_ELECTRICAL_MEASUREMENT), int(ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE)),
            int(volts),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return int(volts)

    def current_a(self, amps, check=False):
        raw = _clamp_int(round(float(amps) * 1000.0), 0, 0xFFFF)
        endpoint = self._set_attr(
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT,
            raw,
            check=check,
        )
        self._device._write_state(
            (int(CLUSTER_ID_ELECTRICAL_MEASUREMENT), int(ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT)),
            int(raw),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return float(raw) / 1000.0

    def color_xy(self, color_x, color_y, transition_ds=0):
        endpoint = self._endpoint(CLUSTER_ID_COLOR_CONTROL)
        color_x = _clamp_int(color_x, 0, 0xFFFF)
        color_y = _clamp_int(color_y, 0, 0xFFFF)
        transition_ds = _clamp_int(transition_ds, 0, 0xFFFF)
        self._device.stack.send_color_move_to_color_cmd(
            self._device.short_addr,
            color_x,
            color_y,
            dst_endpoint=endpoint,
            transition_ds=transition_ds,
        )
        self._device._write_state(
            (int(CLUSTER_ID_COLOR_CONTROL), int(ATTR_COLOR_CONTROL_CURRENT_X)),
            int(color_x),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        self._device._write_state(
            (int(CLUSTER_ID_COLOR_CONTROL), int(ATTR_COLOR_CONTROL_CURRENT_Y)),
            int(color_y),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return int(color_x), int(color_y)

    def color_temperature(self, mireds, transition_ds=0):
        endpoint = self._endpoint(CLUSTER_ID_COLOR_CONTROL)
        mireds = _clamp_int(mireds, 0, 0xFFFF)
        transition_ds = _clamp_int(transition_ds, 0, 0xFFFF)
        self._device.stack.send_color_move_to_color_temperature_cmd(
            self._device.short_addr,
            mireds,
            dst_endpoint=endpoint,
            transition_ds=transition_ds,
        )
        self._device._write_state(
            (int(CLUSTER_ID_COLOR_CONTROL), int(ATTR_COLOR_CONTROL_COLOR_TEMPERATURE)),
            int(mireds),
            source="control",
            authoritative=False,
            endpoint_id=endpoint,
        )
        return int(mireds)


class DeviceEndpointProxy:
    """Endpoint-scoped facade for read/control on a discovered remote device."""

    __slots__ = ("_device", "endpoint_id", "read", "control")

    def __init__(self, device, endpoint_id):
        endpoint_id = int(endpoint_id)
        if endpoint_id not in device.endpoint_clusters:
            raise ZigbeeError("endpoint {} not mapped on device".format(endpoint_id))
        self._device = device
        self.endpoint_id = int(endpoint_id)
        self.read = DeviceReadProxy(device, endpoint_id=self.endpoint_id)
        self.control = DeviceControlProxy(device, endpoint_id=self.endpoint_id)

    def on(self):
        return self.control.on()

    def off(self):
        return self.control.off()

    def toggle(self):
        return self.control.toggle()

    def level(self, level, transition_ds=0, with_onoff=True):
        return self.control.level(level, transition_ds=transition_ds, with_onoff=with_onoff)

    def lock(self):
        return self.control.lock()

    def unlock(self):
        return self.control.unlock()

    def color_xy(self, color_x, color_y, transition_ds=0):
        return self.control.color_xy(color_x, color_y, transition_ds=transition_ds)

    def color_temperature(self, mireds, transition_ds=0):
        return self.control.color_temperature(mireds, transition_ds=transition_ds)


class DiscoveredDevice:
    """Discovered remote Zigbee device with inferred capabilities and cache."""

    __slots__ = (
        "stack",
        "short_addr",
        "endpoint_clusters",
        "cluster_to_endpoint",
        "cluster_to_endpoints",
        "feature_to_endpoints",
        "features",
        "state",
        "state_meta",
        "state_by_endpoint",
        "state_meta_by_endpoint",
        "state_ttl_ms",
        "stale_read_policy",
        "state_cache_max",
        "meta",
        "identity",
        "last_seen_ms",
        "_last_seen_source",
        "_forced_offline",
        "_offline_reason",
        "_offline_set_ms",
        "read",
        "control",
    )

    def __init__(
        self,
        stack,
        short_addr,
        endpoint_clusters,
        cluster_to_endpoint,
        features,
        cluster_to_endpoints=None,
        feature_to_endpoints=None,
        meta=None,
        identity=None,
        state_ttl_ms=120000,
        stale_read_policy="allow",
        state_cache_max=_STATE_CACHE_MAX_DEFAULT,
    ):
        self.stack = stack
        self.short_addr = int(short_addr) & 0xFFFF
        self.endpoint_clusters = endpoint_clusters
        self.cluster_to_endpoint = cluster_to_endpoint
        if cluster_to_endpoints is None:
            cluster_to_endpoints = {}
            for cluster_id, endpoint_id in cluster_to_endpoint.items():
                cluster_to_endpoints[int(cluster_id)] = (int(endpoint_id),)
        self.cluster_to_endpoints = {}
        for cluster_id, endpoint_ids in (cluster_to_endpoints or {}).items():
            cleaned = []
            for endpoint_id in tuple(endpoint_ids or ()):
                endpoint_id = int(endpoint_id)
                if endpoint_id not in cleaned:
                    cleaned.append(endpoint_id)
            cleaned.sort()
            self.cluster_to_endpoints[int(cluster_id)] = tuple(cleaned)

        self.feature_to_endpoints = {}
        for feature_name, endpoint_ids in (feature_to_endpoints or {}).items():
            cleaned = []
            for endpoint_id in tuple(endpoint_ids or ()):
                endpoint_id = int(endpoint_id)
                if endpoint_id not in cleaned:
                    cleaned.append(endpoint_id)
            cleaned.sort()
            self.feature_to_endpoints[str(feature_name)] = tuple(cleaned)
        self.features = set(features)
        self.state = {}
        self.state_meta = {}
        self.state_by_endpoint = {}
        self.state_meta_by_endpoint = {}
        self.state_ttl_ms = _clamp_int(state_ttl_ms, _STATE_TTL_MS_MIN, _STATE_TTL_MS_MAX)
        self.stale_read_policy = _normalize_stale_policy(stale_read_policy)
        self.state_cache_max = _clamp_int(state_cache_max, _STATE_CACHE_MAX_MIN, _STATE_CACHE_MAX_MAX)
        self.meta = meta if meta is not None else {}
        self.identity = identity if identity is not None else DeviceIdentity(short_addr=self.short_addr)
        self.last_seen_ms = _ticks_ms()
        self._last_seen_source = "discovery"
        self._forced_offline = False
        self._offline_reason = None
        self._offline_set_ms = None
        self.read = DeviceReadProxy(self)
        self.control = DeviceControlProxy(self)

    def has_feature(self, name):
        return str(name) in self.features

    @property
    def ieee_addr(self):
        return self.identity.ieee_addr

    @property
    def ieee_hex(self):
        return _ieee_to_hex(self.identity.ieee_addr)

    def endpoint_for(self, cluster_id):
        return self.cluster_to_endpoint.get(int(cluster_id))

    def endpoints_for(self, cluster_id):
        return tuple(self.cluster_to_endpoints.get(int(cluster_id), ()))

    def endpoints(self):
        out = []
        for endpoint_id in self.endpoint_clusters.keys():
            out.append(int(endpoint_id))
        out.sort()
        return tuple(out)

    def endpoint(self, endpoint_id):
        return DeviceEndpointProxy(self, endpoint_id)

    def feature_endpoints(self, feature):
        return tuple(self.feature_to_endpoints.get(str(feature), ()))

    def _select_feature_endpoint(self, feature, selector=1):
        feature = str(feature)
        endpoints = self.feature_endpoints(feature)
        if not endpoints:
            raise ZigbeeError("feature '{}' not mapped on device".format(feature))

        if selector is None:
            if len(endpoints) != 1:
                raise ZigbeeError(
                    "feature '{}' is ambiguous; pass endpoint selector".format(
                        feature
                    )
                )
            return int(endpoints[0])

        selector_int = int(selector)
        if selector_int in endpoints:
            return int(selector_int)

        if selector_int < 1 or selector_int > len(endpoints):
            raise ZigbeeError(
                "feature '{}' selector {} out of range (1..{})".format(
                    feature, selector_int, len(endpoints)
                )
            )
        return int(endpoints[selector_int - 1])

    def feature(self, name, selector=1):
        return self.endpoint(self._select_feature_endpoint(name, selector=selector))

    def switch(self, selector=1):
        return self.feature("on_off", selector=selector)

    def thermostat(self, selector=1):
        return self.feature("thermostat", selector=selector)

    def cover(self, selector=1):
        return self.feature("cover", selector=selector)

    def lock_endpoint(self, selector=1):
        return self.feature("lock", selector=selector)

    def temperature_sensor(self, selector=1):
        return self.feature("temperature", selector=selector)

    def humidity_sensor(self, selector=1):
        return self.feature("humidity", selector=selector)

    def pressure_sensor(self, selector=1):
        return self.feature("pressure", selector=selector)

    def occupancy_sensor(self, selector=1):
        return self.feature("occupancy", selector=selector)

    def ias_zone(self, selector=1):
        return self.feature("ias_zone", selector=selector)

    def energy_meter(self, selector=1):
        return self.feature("energy", selector=selector)

    def color_light(self, selector=1):
        return self.feature("color", selector=selector)

    def on(self):
        return self.control.on()

    def off(self):
        return self.control.off()

    def toggle(self):
        return self.control.toggle()

    def set_level(self, level, transition_ds=0, with_onoff=True):
        return self.control.level(level, transition_ds=transition_ds, with_onoff=with_onoff)

    def lock(self):
        return self.control.lock()

    def unlock(self):
        return self.control.unlock()

    def set_thermostat_heating_setpoint(self, celsius, check=False):
        return self.control.thermostat_heating_setpoint(celsius, check=check)

    def set_thermostat_mode(self, mode, check=False):
        return self.control.thermostat_system_mode(mode, check=check)

    def set_cover_position(self, percent, check=False):
        return self.control.cover_lift(percent, check=check)

    def set_cover_tilt(self, percent, check=False):
        return self.control.cover_tilt(percent, check=check)

    def set_ias_alarm(self, active, check=False):
        return self.control.ias_alarm(active, check=check)

    def set_power_w(self, watts, check=False):
        return self.control.power_w(watts, check=check)

    def set_voltage_v(self, volts, check=False):
        return self.control.voltage_v(volts, check=check)

    def set_current_a(self, amps, check=False):
        return self.control.current_a(amps, check=check)

    def set_color_xy(self, color_x, color_y, transition_ds=0):
        return self.control.color_xy(color_x, color_y, transition_ds=transition_ds)

    def set_color_temperature(self, mireds, transition_ds=0):
        return self.control.color_temperature(mireds, transition_ds=transition_ds)

    def touch_seen(self, now_ms=None, source="activity"):
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)
        self.last_seen_ms = int(now_ms)
        self._last_seen_source = None if source is None else str(source)
        self._forced_offline = False
        self._offline_reason = None
        self._offline_set_ms = None
        return int(self.last_seen_ms)

    def mark_offline(self, reason="manual", now_ms=None):
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)
        self._forced_offline = True
        self._offline_reason = None if reason is None else str(reason)
        self._offline_set_ms = int(now_ms)
        return self.lifecycle()

    def last_seen_age_ms(self, now_ms=None):
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)
        age_ms = _ticks_diff(now_ms, int(self.last_seen_ms))
        if age_ms < 0:
            return 0
        return int(age_ms)

    def is_online(self, offline_after_ms=300000, now_ms=None):
        if self._forced_offline:
            return False
        offline_after_ms = _clamp_int(offline_after_ms, _OFFLINE_AFTER_MS_MIN, _OFFLINE_AFTER_MS_MAX)
        if int(offline_after_ms) <= 0:
            return True
        return self.last_seen_age_ms(now_ms=now_ms) <= int(offline_after_ms)

    def lifecycle(self, offline_after_ms=300000, now_ms=None):
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)
        return {
            "online": bool(self.is_online(offline_after_ms=offline_after_ms, now_ms=now_ms)),
            "last_seen_ms": int(self.last_seen_ms),
            "last_seen_age_ms": int(self.last_seen_age_ms(now_ms=now_ms)),
            "last_seen_source": self._last_seen_source,
            "forced_offline": bool(self._forced_offline),
            "offline_reason": self._offline_reason,
            "offline_set_ms": self._offline_set_ms,
        }

    def _is_state_stale_key(self, key, now_ms=None, endpoint_id=None):
        if endpoint_id is None:
            meta = self.state_meta.get(key)
        else:
            meta = self.state_meta_by_endpoint.get(
                (int(endpoint_id), int(key[0]), int(key[1]))
            )
        if meta is None:
            return True
        ttl_ms = int(self.state_ttl_ms)
        if ttl_ms <= 0:
            return False
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)
        updated_ms = int(meta.get("updated_ms", 0))
        age_ms = _ticks_diff(now_ms, updated_ms)
        if age_ms < 0:
            return False
        return age_ms > ttl_ms

    def _write_state(
        self,
        key,
        value,
        source="unknown",
        authoritative=True,
        now_ms=None,
        endpoint_id=None,
        source_short_addr=None,
        source_endpoint=None,
        attr_type=None,
    ):
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)
        key = (int(key[0]), int(key[1]))
        endpoint_id = (
            self.endpoint_for(key[0])
            if endpoint_id is None
            else int(endpoint_id)
        )
        meta = {
            "updated_ms": now_ms,
            "source": str(source),
            "authoritative": bool(authoritative),
        }
        if source_short_addr is not None:
            meta["source_short_addr"] = int(source_short_addr) & 0xFFFF
        if source_endpoint is not None:
            meta["source_endpoint"] = int(source_endpoint)
        if attr_type is not None:
            meta["attr_type"] = int(attr_type)

        if endpoint_id is not None:
            endpoint_key = (int(endpoint_id), int(key[0]), int(key[1]))
            endpoint_meta = dict(meta)
            endpoint_meta["endpoint_id"] = int(endpoint_id)
            self.state_by_endpoint[endpoint_key] = value
            self.state_meta_by_endpoint[endpoint_key] = endpoint_meta

        default_endpoint = self.endpoint_for(key[0])
        if endpoint_id is None or default_endpoint is None or int(default_endpoint) == int(endpoint_id):
            self.state[key] = value
            self.state_meta[key] = dict(meta)
        self._prune_state_caches()
        self.touch_seen(now_ms=now_ms, source=source)

    def _prune_state_caches(self):
        _prune_cache_map(self.state_by_endpoint, self.state_meta_by_endpoint, self.state_cache_max)
        _prune_cache_map(self.state, self.state_meta, self.state_cache_max)

    def state_info(self, cluster_id, attr_id, endpoint_id=None):
        key = (int(cluster_id), int(attr_id))
        if endpoint_id is None:
            meta = self.state_meta.get(key)
        else:
            endpoint_id = int(endpoint_id)
            meta = self.state_meta_by_endpoint.get((endpoint_id, key[0], key[1]))
        if meta is None:
            return None
        out = dict(meta)
        out["stale"] = self._is_state_stale_key(key, endpoint_id=endpoint_id)
        return out

    def get_state(self, cluster_id, attr_id, default=None, allow_stale=True, endpoint_id=None):
        key = (int(cluster_id), int(attr_id))
        if endpoint_id is None:
            if key not in self.state:
                return default
            value = self.state[key]
        else:
            endpoint_key = (int(endpoint_id), int(key[0]), int(key[1]))
            if endpoint_key not in self.state_by_endpoint:
                return default
            value = self.state_by_endpoint[endpoint_key]
        if allow_stale:
            return value
        if self._is_state_stale_key(key, endpoint_id=endpoint_id):
            return default
        return value

    def to_dict(self):
        endpoint_clusters = {}
        for endpoint_id, clusters in self.endpoint_clusters.items():
            clusters = clusters or {}
            endpoint_clusters[int(endpoint_id)] = {
                "input": tuple(int(cluster_id) for cluster_id in (clusters.get("input") or ())),
                "output": tuple(int(cluster_id) for cluster_id in (clusters.get("output") or ())),
            }
        state = {}
        for key, value in self.state.items():
            state[_state_key_to_text(key)] = value
        state_meta = {}
        for key, meta in self.state_meta.items():
            state_meta[_state_key_to_text(key)] = {
                "updated_ms": int(meta.get("updated_ms", 0)),
                "source": str(meta.get("source", "unknown")),
                "authoritative": bool(meta.get("authoritative", False)),
                "stale": self._is_state_stale_key(key),
                "source_short_addr": meta.get("source_short_addr"),
                "source_endpoint": meta.get("source_endpoint"),
                "attr_type": meta.get("attr_type"),
            }
        return {
            "short_addr": int(self.short_addr),
            "features": sorted(self.features),
            "cluster_to_endpoint": dict(self.cluster_to_endpoint),
            "cluster_to_endpoints": {
                int(cluster_id): tuple(int(endpoint_id) for endpoint_id in tuple(endpoint_ids))
                for cluster_id, endpoint_ids in self.cluster_to_endpoints.items()
            },
            "feature_to_endpoints": {
                str(feature): tuple(int(endpoint_id) for endpoint_id in tuple(endpoint_ids))
                for feature, endpoint_ids in self.feature_to_endpoints.items()
            },
            "endpoint_clusters": endpoint_clusters,
            "state": state,
            "state_by_endpoint": {
                _state_key_to_text(key): value
                for key, value in self.state_by_endpoint.items()
            },
            "last_seen_ms": int(self.last_seen_ms),
            "last_seen_source": self._last_seen_source,
            "forced_offline": bool(self._forced_offline),
            "offline_reason": self._offline_reason,
            "offline_set_ms": self._offline_set_ms,
            "identity": self.identity.to_dict(),
            "state_meta": state_meta,
            "state_meta_by_endpoint": {
                _state_key_to_text(key): {
                    "updated_ms": int(meta.get("updated_ms", 0)),
                    "source": str(meta.get("source", "unknown")),
                    "authoritative": bool(meta.get("authoritative", False)),
                    "endpoint_id": int(meta.get("endpoint_id", key[0])),
                    "stale": self._is_state_stale_key(
                        (int(key[1]), int(key[2])),
                        endpoint_id=int(key[0]),
                    ),
                    "source_short_addr": meta.get("source_short_addr"),
                    "source_endpoint": meta.get("source_endpoint"),
                    "attr_type": meta.get("attr_type"),
                }
                for key, meta in self.state_meta_by_endpoint.items()
            },
            "state_ttl_ms": int(self.state_ttl_ms),
            "stale_read_policy": self.stale_read_policy,
            "state_cache_max": int(self.state_cache_max),
        }

    @classmethod
    def from_dict(cls, data, stack):
        data = data or {}
        short_addr = int(data.get("short_addr", 0)) & 0xFFFF
        endpoint_clusters = {}
        for endpoint_id, clusters in (data.get("endpoint_clusters") or {}).items():
            try:
                endpoint_int = int(endpoint_id)
            except Exception:
                continue
            clusters = clusters or {}
            endpoint_clusters[endpoint_int] = {
                "input": tuple(int(cluster_id) for cluster_id in (clusters.get("input") or ())),
                "output": tuple(int(cluster_id) for cluster_id in (clusters.get("output") or ())),
            }
        cluster_to_endpoint = {}
        for cluster_id, endpoint_id in (data.get("cluster_to_endpoint") or {}).items():
            try:
                cluster_to_endpoint[int(cluster_id)] = int(endpoint_id)
            except Exception:
                continue
        cluster_to_endpoints = {}
        for cluster_id, endpoint_ids in (data.get("cluster_to_endpoints") or {}).items():
            try:
                cluster_int = int(cluster_id)
            except Exception:
                continue
            cleaned = []
            for endpoint_id in tuple(endpoint_ids or ()):
                try:
                    endpoint_int = int(endpoint_id)
                except Exception:
                    continue
                if endpoint_int not in cleaned:
                    cleaned.append(endpoint_int)
            cleaned.sort()
            if cleaned:
                cluster_to_endpoints[cluster_int] = tuple(cleaned)
        if not cluster_to_endpoints:
            for cluster_id, endpoint_id in cluster_to_endpoint.items():
                cluster_to_endpoints[int(cluster_id)] = (int(endpoint_id),)

        feature_to_endpoints = {}
        for feature_name, endpoint_ids in (data.get("feature_to_endpoints") or {}).items():
            cleaned = []
            for endpoint_id in tuple(endpoint_ids or ()):
                try:
                    endpoint_int = int(endpoint_id)
                except Exception:
                    continue
                if endpoint_int not in cleaned:
                    cleaned.append(endpoint_int)
            cleaned.sort()
            if cleaned:
                feature_to_endpoints[str(feature_name)] = tuple(cleaned)
        if not feature_to_endpoints:
            for endpoint_id, clusters in endpoint_clusters.items():
                endpoint_features = set()
                for cluster_id in tuple(clusters.get("input") or ()):
                    feature_name = _FEATURE_BY_CLUSTER.get(int(cluster_id))
                    if feature_name is not None:
                        endpoint_features.add(str(feature_name))
                for feature_name in endpoint_features:
                    row = list(feature_to_endpoints.get(feature_name, ()))
                    if int(endpoint_id) not in row:
                        row.append(int(endpoint_id))
                    row.sort()
                    feature_to_endpoints[feature_name] = tuple(row)
        features = tuple(str(feature) for feature in (data.get("features") or ()))
        identity_raw = data.get("identity") or {"short_addr": short_addr}
        device = cls(
            stack=stack,
            short_addr=short_addr,
            endpoint_clusters=endpoint_clusters,
            cluster_to_endpoint=cluster_to_endpoint,
            cluster_to_endpoints=cluster_to_endpoints,
            feature_to_endpoints=feature_to_endpoints,
            features=features,
            meta={},
            identity=DeviceIdentity.from_dict(identity_raw),
            state_ttl_ms=int(data.get("state_ttl_ms", 120000)),
            stale_read_policy=str(data.get("stale_read_policy", "allow")),
            state_cache_max=int(data.get("state_cache_max", _STATE_CACHE_MAX_DEFAULT)),
        )
        for key_text, value in (data.get("state") or {}).items():
            key = _state_key_from_text(key_text)
            if key is None or len(key) != 2:
                continue
            device.state[key] = value
        for key_text, value in (data.get("state_by_endpoint") or {}).items():
            key = _state_key_from_text(key_text)
            if key is None or len(key) != 3:
                continue
            device.state_by_endpoint[(int(key[0]), int(key[1]), int(key[2]))] = value
        for key_text, meta in (data.get("state_meta") or {}).items():
            key = _state_key_from_text(key_text)
            if key is None or len(key) != 2:
                continue
            meta = meta or {}
            cleaned = {
                "updated_ms": int(meta.get("updated_ms", 0)),
                "source": str(meta.get("source", "unknown")),
                "authoritative": bool(meta.get("authoritative", False)),
            }
            if meta.get("source_short_addr") is not None:
                cleaned["source_short_addr"] = int(meta.get("source_short_addr")) & 0xFFFF
            if meta.get("source_endpoint") is not None:
                cleaned["source_endpoint"] = int(meta.get("source_endpoint"))
            if meta.get("attr_type") is not None:
                cleaned["attr_type"] = int(meta.get("attr_type"))
            device.state_meta[key] = cleaned
        for key_text, meta in (data.get("state_meta_by_endpoint") or {}).items():
            key = _state_key_from_text(key_text)
            if key is None or len(key) != 3:
                continue
            meta = meta or {}
            cleaned = {
                "updated_ms": int(meta.get("updated_ms", 0)),
                "source": str(meta.get("source", "unknown")),
                "authoritative": bool(meta.get("authoritative", False)),
                "endpoint_id": int(meta.get("endpoint_id", key[0])),
            }
            if meta.get("source_short_addr") is not None:
                cleaned["source_short_addr"] = int(meta.get("source_short_addr")) & 0xFFFF
            if meta.get("source_endpoint") is not None:
                cleaned["source_endpoint"] = int(meta.get("source_endpoint"))
            if meta.get("attr_type") is not None:
                cleaned["attr_type"] = int(meta.get("attr_type"))
            device.state_meta_by_endpoint[(int(key[0]), int(key[1]), int(key[2]))] = cleaned
        device.last_seen_ms = int(data.get("last_seen_ms", _ticks_ms()))
        device._last_seen_source = data.get("last_seen_source")
        device._forced_offline = bool(data.get("forced_offline", False))
        device._offline_reason = data.get("offline_reason")
        offline_set_ms = data.get("offline_set_ms")
        device._offline_set_ms = None if offline_set_ms is None else int(offline_set_ms)
        device._prune_state_caches()
        return device


class DeviceRegistry:
    """Bounded in-memory registry keyed by short address."""

    __slots__ = ("max_devices", "_by_short")

    def __init__(self, max_devices=32):
        self.max_devices = max(1, int(max_devices))
        self._by_short = {}

    def __len__(self):
        return len(self._by_short)

    def get(self, short_addr, default=None):
        return self._by_short.get(int(short_addr) & 0xFFFF, default)

    def values(self):
        return tuple(self._by_short.values())

    def by_short(self):
        return dict(self._by_short)

    def upsert(self, device):
        key = int(device.short_addr) & 0xFFFF
        self._by_short[key] = device
        self._prune()
        return device

    def _prune(self):
        while len(self._by_short) > self.max_devices:
            oldest_key = None
            oldest_ts = None
            for key, device in self._by_short.items():
                ts = int(device.last_seen_ms)
                if oldest_ts is None or ts < oldest_ts:
                    oldest_ts = ts
                    oldest_key = key
            if oldest_key is None:
                break
            self._by_short.pop(oldest_key, None)


class Coordinator:
    """Automation-first coordinator facade over ZigbeeStack."""

    __slots__ = (
        "stack",
        "registry",
        "auto_discovery",
        "strict_discovery",
        "discover_timeout_ms",
        "discover_poll_ms",
        "include_power_desc",
        "fallback_without_power_desc",
        "opportunistic_last_joined_scan",
        "state_ttl_ms",
        "stale_read_policy",
        "state_cache_max",
        "join_debounce_ms",
        "discovery_retry_max",
        "discovery_retry_base_ms",
        "discovery_retry_max_backoff_ms",
        "discovery_queue_max",
        "offline_after_ms",
        "auto_bind",
        "auto_configure_reporting",
        "local_endpoint",
        "persistence_path",
        "persistence_min_interval_ms",
        "network_mode",
        "pan_id",
        "extended_pan_id",
        "channel_mask",
        "auto_channel_mask",
        "auto_channel_preferred",
        "auto_channel_blacklist",
        "auto_channel_scan_wifi",
        "auto_channel_scan_fn",
        "_auto_channel_last_decision",
        "_network_profile",
        "_self_heal_enabled",
        "_self_heal_retry_max",
        "_self_heal_retry_base_ms",
        "_self_heal_retry_max_backoff_ms",
        "_commissioning_event_cb",
        "_commissioning_stats",
        "_self_heal_stats",
        "_self_heal_inflight",
        "_started",
        "_form_network",
        "_on_signal_cb",
        "_on_attribute_cb",
        "_on_device_added_cb",
        "_on_device_updated_cb",
        "_join_pending",
        "_join_order",
        "_join_last_seen_ms",
        "_discovery_stats",
        "_automation_stats",
        "_last_discovery_error",
        "_last_persist_ms",
    )

    def __init__(
        self,
        stack=None,
        max_devices=32,
        auto_discovery=True,
        strict_discovery=False,
        discover_timeout_ms=5000,
        discover_poll_ms=200,
        include_power_desc=True,
        fallback_without_power_desc=True,
        opportunistic_last_joined_scan=True,
        state_ttl_ms=120000,
        stale_read_policy="allow",
        state_cache_max=_STATE_CACHE_MAX_DEFAULT,
        join_debounce_ms=3000,
        discovery_retry_max=3,
        discovery_retry_base_ms=400,
        discovery_retry_max_backoff_ms=5000,
        discovery_queue_max=16,
        offline_after_ms=300000,
        auto_bind=False,
        auto_configure_reporting=False,
        local_endpoint=1,
        persistence_path=None,
        persistence_min_interval_ms=30000,
        network_mode="auto",
        pan_id=None,
        extended_pan_id=None,
        channel=None,
        channel_mask=None,
        auto_channel_mask=None,
        auto_channel_preferred=_DEFAULT_AUTO_CHANNEL_PREFERRED,
        auto_channel_blacklist=None,
        auto_channel_scan_wifi=True,
        auto_channel_scan_fn=None,
        self_heal_enabled=True,
        self_heal_retry_max=_SELF_HEAL_RETRY_MAX_DEFAULT,
        self_heal_retry_base_ms=_SELF_HEAL_RETRY_BASE_MS_DEFAULT,
        self_heal_retry_max_backoff_ms=_SELF_HEAL_RETRY_MAX_BACKOFF_MS_DEFAULT,
    ):
        self.stack = stack if stack is not None else ZigbeeStack()
        self.registry = DeviceRegistry(max_devices=max_devices)
        self.auto_discovery = bool(auto_discovery)
        self.strict_discovery = bool(strict_discovery)
        self.discover_timeout_ms = int(discover_timeout_ms)
        self.discover_poll_ms = int(discover_poll_ms)
        self.include_power_desc = bool(include_power_desc)
        self.fallback_without_power_desc = bool(fallback_without_power_desc)
        self.opportunistic_last_joined_scan = bool(opportunistic_last_joined_scan)
        self.state_ttl_ms = _clamp_int(state_ttl_ms, _STATE_TTL_MS_MIN, _STATE_TTL_MS_MAX)
        self.stale_read_policy = _normalize_stale_policy(stale_read_policy)
        self.state_cache_max = _clamp_int(state_cache_max, _STATE_CACHE_MAX_MIN, _STATE_CACHE_MAX_MAX)
        self.join_debounce_ms = _clamp_int(join_debounce_ms, 0, 60000)
        self.discovery_retry_max = _clamp_int(discovery_retry_max, 0, 10)
        self.discovery_retry_base_ms = _clamp_int(discovery_retry_base_ms, 50, 60000)
        self.discovery_retry_max_backoff_ms = _clamp_int(discovery_retry_max_backoff_ms, self.discovery_retry_base_ms, 300000)
        self.discovery_queue_max = _clamp_int(discovery_queue_max, 1, 128)
        self.offline_after_ms = _clamp_int(offline_after_ms, _OFFLINE_AFTER_MS_MIN, _OFFLINE_AFTER_MS_MAX)
        self.auto_bind = bool(auto_bind)
        self.auto_configure_reporting = bool(auto_configure_reporting)
        self.local_endpoint = _clamp_int(local_endpoint, 1, 240)
        self.persistence_path = persistence_path
        self.persistence_min_interval_ms = _clamp_int(persistence_min_interval_ms, 0, 86400000)
        pan_id_value = _normalize_pan_id(pan_id)
        extended_pan_id_value = _normalize_extended_pan_id(extended_pan_id)
        channel_mask_value = _normalize_channel_mask(channel=channel, channel_mask=channel_mask)
        self.network_mode = _infer_network_mode(
            network_mode,
            channel_mask=channel_mask_value,
            pan_id=pan_id_value,
            extended_pan_id=extended_pan_id_value,
            label="network_mode",
        )
        self.pan_id = pan_id_value
        self.extended_pan_id = extended_pan_id_value
        self.channel_mask = channel_mask_value
        self.auto_channel_mask = _normalize_channel_mask(channel_mask=auto_channel_mask)
        self.auto_channel_preferred = _normalize_channel_list(
            "auto_channel_preferred",
            auto_channel_preferred,
            default=_DEFAULT_AUTO_CHANNEL_PREFERRED,
        )
        self.auto_channel_blacklist = _normalize_channel_list("auto_channel_blacklist", auto_channel_blacklist)
        self.auto_channel_scan_wifi = bool(auto_channel_scan_wifi)
        self.auto_channel_scan_fn = auto_channel_scan_fn if callable(auto_channel_scan_fn) else None
        self._auto_channel_last_decision = None
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
            "last_reason": None,
            "last_signal": None,
            "last_status": None,
            "last_attempt_ms": 0,
            "last_backoff_ms": 0,
            "last_result": None,
        }
        self._self_heal_inflight = False
        self._network_profile = NetworkProfile(
            channel_mask=self.channel_mask,
            pan_id=self.pan_id,
            extended_pan_id=self.extended_pan_id,
            source=_mode_profile_source(self.network_mode),
            formed_at_ms=None,
        )
        self._started = False
        self._form_network = False
        self._on_signal_cb = None
        self._on_attribute_cb = None
        self._on_device_added_cb = None
        self._on_device_updated_cb = None
        self._join_pending = {}
        self._join_order = []
        self._join_last_seen_ms = {}
        self._discovery_stats = {
            "queue_enqueued": 0,
            "queue_refreshed": 0,
            "queue_overflow_drop": 0,
            "debounced": 0,
            "attempts": 0,
            "success": 0,
            "failures": 0,
            "requeued": 0,
            "gave_up": 0,
        }
        self._automation_stats = {
            "reporting_applied": 0,
            "reporting_failed": 0,
            "bind_attempted": 0,
            "bind_skipped": 0,
            "bind_failed": 0,
        }
        self._last_discovery_error = None
        self._last_persist_ms = 0
        self._normalize_discovery_timing()

    def configure_state_engine(self, state_ttl_ms=None, stale_read_policy=None, state_cache_max=None):
        if state_ttl_ms is not None:
            self.state_ttl_ms = _clamp_int(state_ttl_ms, _STATE_TTL_MS_MIN, _STATE_TTL_MS_MAX)
        if stale_read_policy is not None:
            self.stale_read_policy = _normalize_stale_policy(stale_read_policy)
        if state_cache_max is not None:
            self.state_cache_max = _clamp_int(state_cache_max, _STATE_CACHE_MAX_MIN, _STATE_CACHE_MAX_MAX)
        for device in self.registry.values():
            device.state_ttl_ms = int(self.state_ttl_ms)
            device.stale_read_policy = self.stale_read_policy
            device.state_cache_max = int(self.state_cache_max)
            device._prune_state_caches()
        return {
            "state_ttl_ms": int(self.state_ttl_ms),
            "stale_read_policy": self.stale_read_policy,
            "state_cache_max": int(self.state_cache_max),
        }

    def configure_automation(self, auto_bind=None, auto_configure_reporting=None, local_endpoint=None):
        if auto_bind is not None:
            self.auto_bind = bool(auto_bind)
        if auto_configure_reporting is not None:
            self.auto_configure_reporting = bool(auto_configure_reporting)
        if local_endpoint is not None:
            self.local_endpoint = _clamp_int(local_endpoint, 1, 240)
        return {
            "auto_bind": bool(self.auto_bind),
            "auto_configure_reporting": bool(self.auto_configure_reporting),
            "local_endpoint": int(self.local_endpoint),
        }

    def configure_auto_channel(
        self,
        auto_channel_mask=None,
        auto_channel_preferred=None,
        auto_channel_blacklist=None,
        auto_channel_scan_wifi=None,
        auto_channel_scan_fn=None,
    ):
        if auto_channel_mask is not None:
            self.auto_channel_mask = _normalize_channel_mask(channel_mask=auto_channel_mask)
        if auto_channel_preferred is not None:
            self.auto_channel_preferred = _normalize_channel_list("auto_channel_preferred", auto_channel_preferred)
        if auto_channel_blacklist is not None:
            self.auto_channel_blacklist = _normalize_channel_list("auto_channel_blacklist", auto_channel_blacklist)
        if auto_channel_scan_wifi is not None:
            self.auto_channel_scan_wifi = bool(auto_channel_scan_wifi)
        if auto_channel_scan_fn is not None:
            self.auto_channel_scan_fn = auto_channel_scan_fn if callable(auto_channel_scan_fn) else None
        return {
            "auto_channel_mask": self.auto_channel_mask,
            "auto_channel_preferred": tuple(self.auto_channel_preferred),
            "auto_channel_blacklist": tuple(self.auto_channel_blacklist),
            "auto_channel_scan_wifi": bool(self.auto_channel_scan_wifi),
            "scan_fn_configured": bool(callable(self.auto_channel_scan_fn)),
        }

    def on_commissioning_event(self, callback=None):
        self._commissioning_event_cb = callback if callable(callback) else None
        return self

    def commissioning_stats(self, reset=False):
        stats = dict(self._commissioning_stats)
        if reset:
            self._commissioning_stats = _new_commissioning_stats()
        return stats

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
                stats["time_to_form_ms"] = int(_ticks_diff(now_ms, int(started_ms)))
                stats["form_started_ms"] = None
        else:
            stats["join_success"] += 1
            stats["last_join_success_ms"] = int(now_ms)
            started_ms = stats.get("join_started_ms", None)
            if started_ms is not None:
                stats["time_to_join_ms"] = int(_ticks_diff(now_ms, int(started_ms)))
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
        if signal_id == int(SIGNAL_FORMATION_CANCELLED):
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

    def configure_lifecycle(self, offline_after_ms=None):
        if offline_after_ms is not None:
            self.offline_after_ms = _clamp_int(offline_after_ms, _OFFLINE_AFTER_MS_MIN, _OFFLINE_AFTER_MS_MAX)
        return {
            "offline_after_ms": int(self.offline_after_ms),
        }

    def automation_stats(self):
        return dict(self._automation_stats)

    def dump_registry(self):
        devices = [device.to_dict() for device in self.registry.values()]
        return {
            "schema": 1,
            "saved_ms": int(_ticks_ms()),
            "network_mode": self.network_mode,
            "network_profile": self._network_profile.to_dict(),
            "self_heal_policy": self.configure_self_heal(),
            "devices": devices,
        }

    def restore_registry(self, snapshot, merge=False):
        snapshot = snapshot or {}
        restored_mode = snapshot.get("network_mode", None)
        if restored_mode is not None:
            try:
                self.network_mode = _infer_network_mode(restored_mode, label="network_mode")
            except Exception:
                pass
        restored_profile = snapshot.get("network_profile", None)
        if isinstance(restored_profile, dict):
            try:
                self._network_profile = NetworkProfile.from_dict(restored_profile)
            except Exception:
                pass
        restored_self_heal_policy = snapshot.get("self_heal_policy", None)
        if isinstance(restored_self_heal_policy, dict):
            self.configure_self_heal(
                enabled=restored_self_heal_policy.get("enabled", None),
                retry_max=restored_self_heal_policy.get("retry_max", None),
                retry_base_ms=restored_self_heal_policy.get("retry_base_ms", None),
                retry_max_backoff_ms=restored_self_heal_policy.get("retry_max_backoff_ms", None),
            )
        rows = snapshot.get("devices") or ()
        if not merge:
            self.registry = DeviceRegistry(max_devices=self.registry.max_devices)
        restored = 0
        for row in rows:
            try:
                device = DiscoveredDevice.from_dict(row, stack=self.stack)
            except Exception:
                continue
            device.state_ttl_ms = int(self.state_ttl_ms)
            device.stale_read_policy = self.stale_read_policy
            device.state_cache_max = int(self.state_cache_max)
            device._prune_state_caches()
            self.registry.upsert(device)
            restored += 1
        return int(restored)

    def save_registry(self, path=None, force=False):
        if _json is None:
            raise ZigbeeError("json module unavailable")
        path = path or self.persistence_path
        if not path:
            raise ZigbeeError("persistence path not configured")
        now_ms = _ticks_ms()
        if not force and int(self.persistence_min_interval_ms) > 0:
            age_ms = _ticks_diff(now_ms, int(self._last_persist_ms))
            if age_ms >= 0 and age_ms < int(self.persistence_min_interval_ms):
                return {
                    "saved": False,
                    "reason": "throttled",
                    "age_ms": int(age_ms),
                    "min_interval_ms": int(self.persistence_min_interval_ms),
                    "path": str(path),
                }
        snapshot = self.dump_registry()
        with open(path, "w") as fp:
            _json.dump(snapshot, fp)
        self._last_persist_ms = int(now_ms)
        return {
            "saved": True,
            "path": str(path),
            "count": len(snapshot.get("devices") or ()),
        }

    def load_registry(self, path=None, merge=False):
        if _json is None:
            raise ZigbeeError("json module unavailable")
        path = path or self.persistence_path
        if not path:
            raise ZigbeeError("persistence path not configured")
        with open(path, "r") as fp:
            snapshot = _json.load(fp)
        restored = self.restore_registry(snapshot, merge=bool(merge))
        return {
            "loaded": True,
            "path": str(path),
            "restored": int(restored),
        }

    def _safe_apply_reporting_preset(self, device, feature_name, cluster_id, preset):
        if not device.has_feature(feature_name):
            return {"feature": feature_name, "status": "skipped", "reason": "feature_not_present"}
        dst_endpoints = device.endpoints_for(cluster_id)
        if not dst_endpoints:
            return {"feature": feature_name, "status": "skipped", "reason": "endpoint_not_mapped"}
        results = []
        applied_total = 0
        any_error = False
        for dst_endpoint in tuple(dst_endpoints):
            try:
                applied_entries = _reporting.apply_reporting_preset(
                    stack=self.stack,
                    dst_short_addr=device.short_addr,
                    preset=preset,
                    src_endpoint=self.local_endpoint,
                    dst_endpoint=int(dst_endpoint),
                )
                applied_count = int(len(applied_entries))
                applied_total += applied_count
                self._automation_stats["reporting_applied"] += applied_count
                results.append(
                    {
                        "dst_endpoint": int(dst_endpoint),
                        "status": "ok",
                        "entries": applied_count,
                    }
                )
            except Exception as exc:
                any_error = True
                self._automation_stats["reporting_failed"] += 1
                results.append(
                    {
                        "dst_endpoint": int(dst_endpoint),
                        "status": "error",
                        "error": _error_repr(exc),
                    }
                )
        return {
            "feature": feature_name,
            "status": "partial" if any_error else "ok",
            "src_endpoint": int(self.local_endpoint),
            "entries": int(applied_total),
            "endpoints": tuple(results),
        }

    def _auto_configure_reporting_for_device(self, device):
        return (
            self._safe_apply_reporting_preset(device, "lock", CLUSTER_ID_DOOR_LOCK, _reporting.PRESET_DOOR_LOCK),
            self._safe_apply_reporting_preset(device, "thermostat", CLUSTER_ID_THERMOSTAT, _reporting.PRESET_THERMOSTAT),
            self._safe_apply_reporting_preset(device, "occupancy", CLUSTER_ID_OCCUPANCY_SENSING, _reporting.PRESET_OCCUPANCY),
            self._safe_apply_reporting_preset(device, "ias_zone", CLUSTER_ID_IAS_ZONE, _reporting.PRESET_CONTACT_SENSOR),
            self._safe_apply_reporting_preset(device, "cover", CLUSTER_ID_WINDOW_COVERING, _AUTO_REPORTING_PRESET_COVER),
            self._safe_apply_reporting_preset(device, "energy", CLUSTER_ID_ELECTRICAL_MEASUREMENT, _AUTO_REPORTING_PRESET_ENERGY),
        )

    def _auto_bind_for_device(self, device):
        self._automation_stats["bind_attempted"] += 1
        discovered = device.meta.get("discovered") or {}
        remote_ieee = discovered.get("ieee_addr")
        if remote_ieee is None:
            self._automation_stats["bind_skipped"] += 1
            return {"status": "skipped", "reason": "missing_remote_ieee"}
        try:
            local_ieee = self.stack.get_ieee_addr()
        except Exception as exc:
            self._automation_stats["bind_failed"] += 1
            return {"status": "error", "reason": "local_ieee_unavailable", "error": _error_repr(exc)}

        clusters = []
        for cluster_id in (
            CLUSTER_ID_ON_OFF,
            CLUSTER_ID_LEVEL_CONTROL,
            CLUSTER_ID_THERMOSTAT,
            CLUSTER_ID_OCCUPANCY_SENSING,
            CLUSTER_ID_IAS_ZONE,
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            CLUSTER_ID_WINDOW_COVERING,
            CLUSTER_ID_DOOR_LOCK,
        ):
            endpoint_ids = device.endpoints_for(cluster_id)
            if not endpoint_ids:
                continue
            for endpoint_id in tuple(endpoint_ids):
                row = (int(endpoint_id), int(cluster_id))
                if row not in clusters:
                    clusters.append(row)

        if not clusters:
            self._automation_stats["bind_skipped"] += 1
            return {"status": "skipped", "reason": "no_bindable_clusters"}

        bound = 0
        failures = []
        for endpoint_id, cluster_id in clusters:
            try:
                self.stack.send_bind_cmd(
                    src_ieee_addr=remote_ieee,
                    src_endpoint=int(endpoint_id),
                    cluster_id=int(cluster_id),
                    dst_ieee_addr=local_ieee,
                    dst_endpoint=int(self.local_endpoint),
                    req_dst_short_addr=int(device.short_addr),
                )
                bound += 1
            except Exception as exc:
                self._automation_stats["bind_failed"] += 1
                failures.append(
                    {
                        "cluster_id": int(cluster_id),
                        "endpoint": int(endpoint_id),
                        "error": _error_repr(exc),
                    }
                )
        return {
            "status": "ok" if not failures else "partial",
            "bound": int(bound),
            "failed": tuple(failures),
        }

    def _post_discovery_automation(self, device):
        automation_meta = {
            "auto_configure_reporting": bool(self.auto_configure_reporting),
            "auto_bind": bool(self.auto_bind),
            "local_endpoint": int(self.local_endpoint),
        }
        if self.auto_configure_reporting:
            automation_meta["reporting"] = self._auto_configure_reporting_for_device(device)
        if self.auto_bind:
            automation_meta["bind"] = self._auto_bind_for_device(device)
        device.meta["automation"] = automation_meta

    def on_signal(self, callback=None):
        self._on_signal_cb = callback
        return self

    def on_attribute(self, callback=None):
        self._on_attribute_cb = callback
        return self

    def on_device_added(self, callback=None):
        self._on_device_added_cb = callback
        return self

    def on_device_updated(self, callback=None):
        self._on_device_updated_cb = callback
        return self

    def _resolve_auto_channel_candidates(self):
        if self.auto_channel_mask is not None:
            candidates = list(_channels_from_mask(self.auto_channel_mask))
        else:
            candidates = list(_channels_from_mask(_CHANNEL_MASK_ALLOWED))
        if self.auto_channel_blacklist:
            blocked = set(int(ch) for ch in tuple(self.auto_channel_blacklist))
            candidates = [int(ch) for ch in candidates if int(ch) not in blocked]
        if not candidates:
            candidates = list(_channels_from_mask(_CHANNEL_MASK_ALLOWED))
        return tuple(int(ch) for ch in candidates)

    def _select_auto_channel(self):
        candidates = self._resolve_auto_channel_candidates()
        wifi_rows = ()
        if bool(self.auto_channel_scan_wifi):
            wifi_rows = _scan_wifi_channels(scan_fn=self.auto_channel_scan_fn)
        selection = _select_best_channel(
            candidates=candidates,
            preferred=self.auto_channel_preferred,
            wifi_rows=wifi_rows,
        )
        selection["strategy"] = "wifi_aware" if wifi_rows else "preferred_fallback"
        selection["candidates"] = tuple(candidates)
        selection["blacklist"] = tuple(self.auto_channel_blacklist)
        selection["preferred"] = tuple(self.auto_channel_preferred)
        return selection

    def _prepare_auto_channel_if_needed(self, form_network):
        if not bool(form_network):
            return None
        if str(self.network_mode) != NETWORK_MODE_AUTO:
            return None
        if self.channel_mask is not None:
            selected_channels = _channels_from_mask(int(self.channel_mask))
            return {
                "strategy": "explicit_existing",
                "selected_channel_mask": int(self.channel_mask),
                "selected_channel": int(selected_channels[0]) if len(selected_channels) == 1 else None,
                "wifi_scan_count": 0,
            }
        if self._network_profile.channel_mask is not None:
            restored_mask = int(self._network_profile.channel_mask)
            selected = _channels_from_mask(restored_mask)
            return {
                "strategy": "restored_profile",
                "selected_channel_mask": restored_mask,
                "selected_channel": int(selected[0]) if len(selected) == 1 else None,
                "wifi_scan_count": 0,
            }
        selection = self._select_auto_channel()
        self.channel_mask = int(selection["selected_channel_mask"])
        return selection

    def _hydrate_guided_identity_from_profile(self):
        if str(self.network_mode) != NETWORK_MODE_GUIDED:
            return False
        changed = False
        if self.pan_id is None and self._network_profile.pan_id is not None:
            self.pan_id = int(self._network_profile.pan_id)
            changed = True
        if self.extended_pan_id is None and self._network_profile.extended_pan_id is not None:
            self.extended_pan_id = bytes(self._network_profile.extended_pan_id)
            changed = True
        return bool(changed)

    def _prepare_guided_channel_if_needed(self, form_network):
        if not bool(form_network):
            return None
        if str(self.network_mode) != NETWORK_MODE_GUIDED:
            return None
        if self.channel_mask is not None:
            selected_channels = _channels_from_mask(int(self.channel_mask))
            return {
                "strategy": "guided_explicit",
                "selected_channel_mask": int(self.channel_mask),
                "selected_channel": int(selected_channels[0]) if len(selected_channels) == 1 else None,
                "wifi_scan_count": 0,
            }
        if self._network_profile.channel_mask is not None:
            restored_mask = int(self._network_profile.channel_mask)
            self.channel_mask = int(restored_mask)
            selected = _channels_from_mask(restored_mask)
            return {
                "strategy": "guided_restored_profile",
                "selected_channel_mask": restored_mask,
                "selected_channel": int(selected[0]) if len(selected) == 1 else None,
                "wifi_scan_count": 0,
            }
        selection = self._select_auto_channel()
        strategy = str(selection.get("strategy") or "fallback")
        selection["strategy"] = "guided_{}".format(strategy)
        self.channel_mask = int(selection["selected_channel_mask"])
        return selection

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
            self.channel_mask = int(channel_mask)
            changed = True
        if pan_id is not None and self._network_profile.pan_id != int(pan_id):
            self.pan_id = int(pan_id)
            changed = True
        if ext_pan is not None and self._network_profile.extended_pan_id != bytes(ext_pan):
            self.extended_pan_id = bytes(ext_pan)
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
                source=_mode_profile_source(self.network_mode),
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

    def _self_heal_retrigger(self, reason, signal_id=None, status=None, action="rejoin"):
        if not bool(self._self_heal_enabled):
            return False
        if not bool(self._started):
            return False
        if bool(self._self_heal_inflight):
            return False
        self._self_heal_inflight = True
        try:
            attempt = 0
            while True:
                ok = True
                if str(action) == "reform":
                    self._mark_commissioning_attempt("form")
                else:
                    self._mark_commissioning_attempt("join")
                try:
                    if str(action) == "reform":
                        self.stack.start(True)
                    elif hasattr(self.stack, "start_network_steering"):
                        self.stack.start_network_steering()
                    else:
                        self.stack.start(False)
                except OSError as exc:
                    if exc.args and int(exc.args[0]) == ESP_ERR_INVALID_STATE:
                        ok = False
                    else:
                        ok = False
                except Exception:
                    ok = False

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

    def start(self, form_network=True):
        now_ms = int(_ticks_ms())
        self._commissioning_stats["start_count"] += 1
        self._commissioning_stats["last_start_ms"] = int(now_ms)
        if bool(form_network):
            self._mark_commissioning_attempt("form")
        else:
            self._mark_commissioning_attempt("join")
        auto_channel_decision = None
        if self.network_mode == NETWORK_MODE_AUTO:
            auto_channel_decision = self._prepare_auto_channel_if_needed(bool(form_network))
        elif self.network_mode == NETWORK_MODE_GUIDED:
            auto_channel_decision = self._prepare_guided_channel_if_needed(bool(form_network))
            self._hydrate_guided_identity_from_profile()
        self._auto_channel_last_decision = auto_channel_decision

        apply_network_identity = self.network_mode in (NETWORK_MODE_FIXED, NETWORK_MODE_GUIDED)
        if apply_network_identity and self.extended_pan_id is not None and hasattr(self.stack, "set_extended_pan_id"):
            _ignore_invalid_state(self.stack.set_extended_pan_id, bytes(self.extended_pan_id))
        if apply_network_identity and self.pan_id is not None and hasattr(self.stack, "set_pan_id"):
            _ignore_invalid_state(self.stack.set_pan_id, int(self.pan_id))
        if (apply_network_identity or (self.network_mode == "auto" and self.channel_mask is not None)) and hasattr(self.stack, "set_primary_channel_mask"):
            _ignore_invalid_state(self.stack.set_primary_channel_mask, int(self.channel_mask))
        if hasattr(self.stack, "enable_wifi_i154_coex"):
            _ignore_invalid_state(self.stack.enable_wifi_i154_coex)
        _ignore_invalid_state(self.stack.init, ROLE_COORDINATOR)
        if hasattr(self.stack, "create_on_off_switch"):
            # Ensure a local endpoint exists so register_device can succeed.
            _ignore_invalid_state(self.stack.create_on_off_switch, int(self.local_endpoint))
        if hasattr(self.stack, "register_device"):
            # Registering the local endpoint keeps high-level coordinator control
            # paths valid on firmware that gates ZCL requests behind registration.
            _ignore_invalid_state(self.stack.register_device)
        self.stack.on_signal(self._handle_signal)
        self.stack.on_attribute(self._handle_attribute)
        _ignore_invalid_state(self.stack.start, bool(form_network))
        if hasattr(self.stack, "enable_wifi_i154_coex"):
            # Coex needs both Wi-Fi and 802.15.4 stacks active on some firmwares.
            _ignore_invalid_state(self.stack.enable_wifi_i154_coex)
        self._started = True
        self._form_network = bool(form_network)
        profile_source = _mode_profile_source(self.network_mode)
        formed_at_ms = int(_ticks_ms()) if bool(form_network) else self._network_profile.formed_at_ms
        self._network_profile.update(
            channel_mask=self.channel_mask,
            pan_id=self.pan_id,
            extended_pan_id=self.extended_pan_id,
            source=profile_source,
            formed_at_ms=formed_at_ms,
        )
        if self.network_mode in (NETWORK_MODE_AUTO, NETWORK_MODE_GUIDED):
            self._sync_network_profile_from_runtime()
        return self

    def network_info(self):
        runtime = {}
        if hasattr(self.stack, "get_network_runtime"):
            try:
                raw_runtime = self.stack.get_network_runtime() or {}
                if isinstance(raw_runtime, dict):
                    runtime = raw_runtime
            except Exception:
                runtime = {}

        short_addr = None
        ieee_addr = None
        if "short_addr" in runtime:
            try:
                short_addr = int(runtime.get("short_addr")) & 0xFFFF
            except Exception:
                short_addr = None
        if short_addr is None:
            try:
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

        runtime_formed = runtime.get("formed", None)
        runtime_joined = runtime.get("joined", None)

        return {
            "network_mode": str(self.network_mode),
            "started": bool(self._started),
            "form_network": bool(self._form_network),
            "short_addr": short_addr,
            "ieee_addr": ieee_addr,
            "ieee_hex": _ieee_to_hex(ieee_addr),
            "channel": None if runtime_channel is None else int(runtime_channel),
            "pan_id": None if runtime_pan_id is None else int(runtime_pan_id) & 0xFFFF,
            "extended_pan_id": runtime_ext_pan,
            "extended_pan_id_hex": _ieee_to_hex(runtime_ext_pan),
            "formed": None if runtime_formed is None else bool(runtime_formed),
            "joined": None if runtime_joined is None else bool(runtime_joined),
            "auto_channel": dict(self._auto_channel_last_decision) if isinstance(self._auto_channel_last_decision, dict) else None,
            "commissioning": self.commissioning_stats(),
            "self_heal": {
                "policy": self.configure_self_heal(),
                "stats": self.self_heal_stats(),
            },
            "profile": self._network_profile.to_dict(),
        }

    def permit_join(self, duration_s=60, auto_discover=True):
        self.auto_discovery = bool(auto_discover)
        self.stack.permit_join(int(duration_s))
        return int(duration_s)

    def process_pending_discovery(self, max_items=4):
        return self._process_discovery_queue(max_items=max_items)

    def pending_discovery(self):
        pending = []
        for short_addr in self._join_order:
            entry = self._join_pending.get(short_addr)
            if entry is None:
                continue
            pending.append(
                {
                    "short_addr": int(short_addr),
                    "attempt": int(entry.get("attempt", 0)),
                    "next_try_ms": int(entry.get("next_try_ms", 0)),
                    "last_error": entry.get("last_error"),
                }
            )
        return tuple(pending)

    def discovery_stats(self):
        stats = dict(self._discovery_stats)
        stats["queue_depth"] = len(self._join_order)
        stats["last_error"] = self._last_discovery_error
        return stats

    def _discover_descriptors_with_fallback(self, short_addr, endpoint_ids=None, strict_mode=False):
        short_addr = int(short_addr) & 0xFFFF
        strict_mode = bool(strict_mode)

        try:
            return self.stack.discover_node_descriptors(
                short_addr,
                endpoint_ids=endpoint_ids,
                include_power_desc=self.include_power_desc,
                timeout_ms=self.discover_timeout_ms,
                poll_ms=self.discover_poll_ms,
                strict=strict_mode,
            )
        except Exception:
            if strict_mode:
                raise
            if not self.include_power_desc:
                raise
            if not self.fallback_without_power_desc:
                raise

        return self.stack.discover_node_descriptors(
            short_addr,
            endpoint_ids=endpoint_ids,
            include_power_desc=False,
            timeout_ms=self.discover_timeout_ms,
            poll_ms=self.discover_poll_ms,
            strict=False,
        )

    def _queue_from_last_joined_hint(self, now_ms=None):
        if not self.opportunistic_last_joined_scan:
            return False
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)
        try:
            short_addr = self.stack.get_last_joined_short_addr()
        except Exception:
            return False
        if short_addr is None:
            return False
        short_addr = int(short_addr) & 0xFFFF
        if short_addr in (0x0000, 0xFFFE, 0xFFFF):
            return False
        if short_addr in self._join_pending:
            return False
        if self.registry.get(short_addr) is not None:
            return False
        return bool(self._queue_discovery(short_addr, now_ms=now_ms))

    def discover_device(self, short_addr, endpoint_ids=None, strict=None):
        short_addr = int(short_addr) & 0xFFFF
        strict_mode = self.strict_discovery if strict is None else bool(strict)
        self._normalize_discovery_timing()

        discovered = self._discover_descriptors_with_fallback(
            short_addr,
            endpoint_ids=endpoint_ids,
            strict_mode=strict_mode,
        )
        device = self._build_device_from_descriptors(discovered)
        device.touch_seen(source="discovery")
        existing = self.registry.get(short_addr)
        self.registry.upsert(device)
        self._post_discovery_automation(device)
        if existing is None:
            if self._on_device_added_cb is not None:
                self._on_device_added_cb(device)
        else:
            if self._on_device_updated_cb is not None:
                self._on_device_updated_cb(device)
        self._remove_pending(short_addr)
        return device

    def get_device(self, short_addr, default=None, online=None):
        device = self.registry.get(short_addr, default)
        if device is default:
            return default
        if online is None:
            return device
        if bool(device.is_online(offline_after_ms=self.offline_after_ms)) != bool(online):
            return default
        return device

    def get_device_by_ieee(self, ieee_addr, default=None):
        ieee_addr = _normalize_ieee_addr(ieee_addr)
        for device in self.registry.values():
            if device.identity.ieee_addr == ieee_addr:
                return device
        return default

    def device_status(self, short_addr, default=None):
        device = self.registry.get(short_addr)
        if device is None:
            return default
        status = device.lifecycle(offline_after_ms=self.offline_after_ms)
        status["short_addr"] = int(device.short_addr)
        return status

    def mark_device_offline(self, short_addr, reason="manual"):
        device = self.registry.get(short_addr)
        if device is None:
            return False
        device.mark_offline(reason=reason)
        return True

    def mark_device_online(self, short_addr, source="manual"):
        device = self.registry.get(short_addr)
        if device is None:
            return False
        device.touch_seen(source=source)
        return True

    def find_devices(
        self,
        feature=None,
        features=None,
        manufacturer_code=None,
        profile_id=None,
        device_id=None,
        ieee_addr=None,
        online=None,
    ):
        required_features = set()
        if feature is not None:
            required_features.add(str(feature))
        for name in (features or ()):
            required_features.add(str(name))

        manufacturer_code = None if manufacturer_code is None else int(manufacturer_code)
        profile_id = None if profile_id is None else int(profile_id)
        device_id = None if device_id is None else int(device_id)
        ieee_addr = _normalize_ieee_addr(ieee_addr) if ieee_addr is not None else None

        out = []
        for device in self.registry.values():
            if online is not None and bool(device.is_online(offline_after_ms=self.offline_after_ms)) != bool(online):
                continue
            if required_features and not all(device.has_feature(name) for name in required_features):
                continue
            identity = device.identity
            if manufacturer_code is not None and identity.manufacturer_code != manufacturer_code:
                continue
            if profile_id is not None and identity.profile_id != profile_id:
                continue
            if device_id is not None and identity.device_id != device_id:
                continue
            if ieee_addr is not None and identity.ieee_addr != ieee_addr:
                continue
            out.append(device)
        out.sort(key=lambda item: int(item.short_addr))
        return tuple(out)

    def select_device(
        self,
        feature=None,
        features=None,
        manufacturer_code=None,
        profile_id=None,
        device_id=None,
        ieee_addr=None,
        online=None,
        default=None,
    ):
        matches = self.find_devices(
            feature=feature,
            features=features,
            manufacturer_code=manufacturer_code,
            profile_id=profile_id,
            device_id=device_id,
            ieee_addr=ieee_addr,
            online=online,
        )
        if not matches:
            return default
        return matches[0]

    def wait_for_device(
        self,
        feature=None,
        features=None,
        manufacturer_code=None,
        profile_id=None,
        device_id=None,
        ieee_addr=None,
        online=None,
        timeout_ms=60000,
        poll_ms=100,
        process_batch=4,
        permit_join_s=None,
        auto_discover=True,
        default=None,
    ):
        timeout_ms = int(timeout_ms)
        poll_ms = _clamp_int(poll_ms, 10, 5000)
        process_batch = _clamp_int(process_batch, 1, 128)

        if permit_join_s is not None:
            self.permit_join(int(permit_join_s), auto_discover=auto_discover)

        deadline_ms = _ticks_add(_ticks_ms(), timeout_ms if timeout_ms > 0 else 0)
        while True:
            device = self.select_device(
                feature=feature,
                features=features,
                manufacturer_code=manufacturer_code,
                profile_id=profile_id,
                device_id=device_id,
                ieee_addr=ieee_addr,
                online=online,
                default=None,
            )
            if device is not None:
                return device

            self._process_discovery_queue(max_items=process_batch)

            device = self.select_device(
                feature=feature,
                features=features,
                manufacturer_code=manufacturer_code,
                profile_id=profile_id,
                device_id=device_id,
                ieee_addr=ieee_addr,
                online=online,
                default=None,
            )
            if device is not None:
                return device

            if timeout_ms <= 0:
                return default
            if _ticks_diff(deadline_ms, _ticks_ms()) <= 0:
                return default
            _sleep_ms(poll_ms)

    def list_devices(self, online=None):
        if online is None:
            return self.registry.values()
        out = []
        for device in self.registry.values():
            if bool(device.is_online(offline_after_ms=self.offline_after_ms)) == bool(online):
                out.append(device)
        out.sort(key=lambda item: int(item.short_addr))
        return tuple(out)

    @property
    def devices(self):
        return self.registry.by_short()

    def _normalize_discovery_timing(self):
        self.discover_poll_ms = _clamp_int(self.discover_poll_ms, _DISCOVERY_POLL_MS_MIN, _DISCOVERY_POLL_MS_MAX)
        self.discover_timeout_ms = _clamp_int(self.discover_timeout_ms, _DISCOVERY_TIMEOUT_MS_MIN, _DISCOVERY_TIMEOUT_MS_MAX)
        min_timeout = int(self.discover_poll_ms) * 2
        if self.discover_timeout_ms < min_timeout:
            self.discover_timeout_ms = min_timeout

    def _remove_pending(self, short_addr):
        short_addr = int(short_addr) & 0xFFFF
        self._join_pending.pop(short_addr, None)
        try:
            self._join_order.remove(short_addr)
        except Exception:
            pass

    def _retry_backoff_ms(self, attempt):
        attempt = _clamp_int(attempt, 1, 30)
        backoff = int(self.discovery_retry_base_ms) << (attempt - 1)
        if backoff > int(self.discovery_retry_max_backoff_ms):
            backoff = int(self.discovery_retry_max_backoff_ms)
        return int(backoff)

    def _queue_discovery(self, short_addr, now_ms=None):
        short_addr = int(short_addr) & 0xFFFF
        now_ms = _ticks_ms() if now_ms is None else int(now_ms)

        last_ms = self._join_last_seen_ms.get(short_addr)
        if last_ms is not None:
            age_ms = _ticks_diff(now_ms, int(last_ms))
            if age_ms >= 0 and age_ms < int(self.join_debounce_ms):
                self._discovery_stats["debounced"] += 1
                return False
        self._join_last_seen_ms[short_addr] = now_ms

        entry = self._join_pending.get(short_addr)
        if entry is not None:
            entry["next_try_ms"] = now_ms
            entry["last_signal_ms"] = now_ms
            self._discovery_stats["queue_refreshed"] += 1
            return True

        if len(self._join_order) >= int(self.discovery_queue_max):
            drop_short = self._join_order.pop(0)
            self._join_pending.pop(drop_short, None)
            self._discovery_stats["queue_overflow_drop"] += 1

        self._join_pending[short_addr] = {
            "short_addr": short_addr,
            "attempt": 0,
            "next_try_ms": now_ms,
            "last_signal_ms": now_ms,
            "last_error": None,
            "last_error_ms": None,
        }
        self._join_order.append(short_addr)
        self._discovery_stats["queue_enqueued"] += 1
        return True

    def _next_due_short(self, now_ms):
        for short_addr in self._join_order:
            entry = self._join_pending.get(short_addr)
            if entry is None:
                continue
            if _ticks_diff(int(now_ms), int(entry.get("next_try_ms", 0))) >= 0:
                return int(short_addr)
        return None

    def _process_discovery_queue(self, max_items=4):
        max_items = _clamp_int(max_items, 1, 128)
        now_ms = _ticks_ms()
        self._queue_from_last_joined_hint(now_ms=now_ms)
        success = 0
        failed = 0
        processed = 0

        while processed < max_items:
            short_addr = self._next_due_short(now_ms)
            if short_addr is None:
                break
            entry = self._join_pending.get(short_addr)
            if entry is None:
                self._remove_pending(short_addr)
                continue

            entry["attempt"] = int(entry.get("attempt", 0)) + 1
            self._discovery_stats["attempts"] += 1

            try:
                self.discover_device(short_addr, strict=False)
                self._discovery_stats["success"] += 1
                success += 1
            except Exception as exc:
                self._discovery_stats["failures"] += 1
                failed += 1
                attempt = int(entry.get("attempt", 1))
                if attempt > int(self.discovery_retry_max):
                    self._remove_pending(short_addr)
                    self._discovery_stats["gave_up"] += 1
                    self._last_discovery_error = {
                        "short_addr": int(short_addr),
                        "attempt": attempt,
                        "error": _error_repr(exc),
                    }
                else:
                    backoff_ms = self._retry_backoff_ms(attempt)
                    entry["next_try_ms"] = _ticks_add(now_ms, backoff_ms)
                    entry["last_error"] = _error_repr(exc)
                    entry["last_error_ms"] = now_ms
                    self._discovery_stats["requeued"] += 1
            processed += 1

        return {
            "processed": int(processed),
            "success": int(success),
            "failed": int(failed),
            "queue_depth": len(self._join_order),
        }

    def _build_device_from_descriptors(self, discovered):
        short_addr = int(discovered.get("short_addr", 0)) & 0xFFFF
        simple_desc_rows = discovered.get("simple_descriptors", ())
        identity = DeviceIdentity.from_discovery(discovered)

        endpoint_clusters = {}
        cluster_to_endpoint = {}
        cluster_to_endpoints = {}
        feature_to_endpoints = {}
        features = set()

        for row in simple_desc_rows:
            endpoint, simple_desc = _extract_simple_descriptor(row)

            input_clusters = [int(cluster_id) for cluster_id in (simple_desc.get("input_clusters") or ())]
            output_clusters = [int(cluster_id) for cluster_id in (simple_desc.get("output_clusters") or ())]
            endpoint_clusters[endpoint] = {
                "input": tuple(input_clusters),
                "output": tuple(output_clusters),
            }

            for cluster_id in input_clusters:
                if cluster_id not in cluster_to_endpoint:
                    cluster_to_endpoint[cluster_id] = endpoint
                cluster_endpoints = list(cluster_to_endpoints.get(cluster_id, ()))
                if endpoint not in cluster_endpoints:
                    cluster_endpoints.append(endpoint)
                cluster_endpoints.sort()
                cluster_to_endpoints[cluster_id] = tuple(cluster_endpoints)
                feature = _FEATURE_BY_CLUSTER.get(cluster_id)
                if feature is not None:
                    features.add(feature)
                    feature_endpoints = list(feature_to_endpoints.get(feature, ()))
                    if endpoint not in feature_endpoints:
                        feature_endpoints.append(endpoint)
                    feature_endpoints.sort()
                    feature_to_endpoints[feature] = tuple(feature_endpoints)

        return DiscoveredDevice(
            stack=self.stack,
            short_addr=short_addr,
            endpoint_clusters=endpoint_clusters,
            cluster_to_endpoint=cluster_to_endpoint,
            cluster_to_endpoints=cluster_to_endpoints,
            feature_to_endpoints=feature_to_endpoints,
            features=features,
            meta={"discovered": discovered},
            identity=identity,
            state_ttl_ms=self.state_ttl_ms,
            stale_read_policy=self.stale_read_policy,
            state_cache_max=self.state_cache_max,
        )

    def _handle_signal(self, signal_id, status):
        signal_id = int(signal_id)
        status = int(status)
        self._update_commissioning_stats_on_signal(signal_id, status)
        if self._on_signal_cb is not None:
            self._on_signal_cb(signal_id, status)

        if status == 0 and signal_id in _NETWORK_PROFILE_SYNC_SIGNALS:
            self._sync_network_profile_from_runtime()

        if signal_id == int(SIGNAL_PANID_CONFLICT_DETECTED):
            self._self_heal_stats["panid_conflicts"] += 1
            self._emit_commissioning_event(
                "panid_conflict_detected",
                reason="panid_conflict_detected",
                signal_id=signal_id,
                status=status,
            )
            self._self_heal_retrigger(
                reason="panid_conflict_detected",
                signal_id=signal_id,
                status=status,
                action="reform",
            )
        elif signal_id in _STEERING_FAILURE_SIGNALS and status != 0:
            self._self_heal_stats["steering_failures"] += 1
            self._self_heal_retrigger(
                reason="steering_failure",
                signal_id=signal_id,
                status=status,
                action="rejoin",
            )

        if not self.auto_discovery:
            return
        if status != 0:
            return
        if signal_id not in _JOIN_SIGNALS:
            return

        try:
            short_addr = self.stack.get_last_joined_short_addr()
        except Exception:
            return
        if short_addr is None:
            return
        short_addr = int(short_addr) & 0xFFFF
        if short_addr in (0x0000, 0xFFFE, 0xFFFF):
            return

        self._queue_discovery(short_addr)
        self._process_discovery_queue(max_items=1)

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
                    self._on_attribute_cb(source_short_addr, endpoint, cluster_id, attr_id, value, attr_type, status)
                else:
                    self._on_attribute_cb(endpoint, cluster_id, attr_id, value, status)
            except TypeError:
                # Backward-compatible fallback for handlers with older signature.
                self._on_attribute_cb(endpoint, cluster_id, attr_id, value, status)

        if status != 0:
            return

        key = (cluster_id, attr_id)
        if source_short_addr is not None:
            device = self.registry.get(source_short_addr)
            if device is None:
                return
            mapped_eps = device.endpoints_for(cluster_id)
            if endpoint not in mapped_eps:
                return
            device._write_state(
                key,
                value,
                source="attribute",
                authoritative=True,
                endpoint_id=endpoint,
                source_short_addr=source_short_addr,
                source_endpoint=endpoint,
                attr_type=attr_type,
            )
            return

        for device in self.registry.values():
            mapped_eps = device.endpoints_for(cluster_id)
            if endpoint not in mapped_eps:
                continue
            device._write_state(
                key,
                value,
                source="attribute",
                authoritative=True,
                endpoint_id=endpoint,
                source_endpoint=endpoint,
                attr_type=attr_type,
            )
