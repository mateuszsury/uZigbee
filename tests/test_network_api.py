import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import uzigbee
from uzigbee import network


def _descriptor(short_addr, endpoint_clusters, manufacturer_code=0x1234, endpoint_meta=None, power_desc=None, ieee_addr=None):
    endpoint_meta = endpoint_meta or {}
    rows = []
    endpoint_ids = []
    for endpoint, clusters in endpoint_clusters.items():
        endpoint = int(endpoint)
        meta = endpoint_meta.get(endpoint, {})
        profile_id = int(meta.get("profile_id", 0x0104))
        device_id = int(meta.get("device_id", 0x0000))
        device_version = int(meta.get("device_version", 1))
        endpoint_ids.append(endpoint)
        rows.append(
            {
                "endpoint": endpoint,
                "snapshot": {
                    "status": 0,
                    "addr": int(short_addr),
                    "simple_desc": {
                        "endpoint": endpoint,
                        "profile_id": profile_id,
                        "device_id": device_id,
                        "device_version": device_version,
                        "input_clusters": list(clusters),
                        "output_clusters": [],
                    },
                },
            }
        )
    out = {
        "short_addr": int(short_addr),
        "endpoint_ids": endpoint_ids,
        "active_endpoints": {
            "status": 0,
            "count": len(endpoint_ids),
            "endpoints": endpoint_ids,
        },
        "node_descriptor": {
            "status": 0,
            "addr": int(short_addr),
            "node_desc": {
                "manufacturer_code": int(manufacturer_code),
            },
        },
        "simple_descriptors": rows,
        "power_descriptor": {"status": 0, "addr": int(short_addr), "power_desc": dict(power_desc or {})},
        "errors": [],
    }
    if ieee_addr is not None:
        out["ieee_addr"] = bytes(ieee_addr)
    return out


class _FakeStack:
    def __init__(self):
        self.calls = []
        self._signal_cb = None
        self._attr_cb = None
        self._runtime_channel = 20
        self._runtime_pan_id = 0x6C6C
        self._runtime_ext_pan = bytes.fromhex("00124b0001c6c6c6")
        self._runtime_short_addr = 0x0000
        self._last_joined_short = 0x2222
        self._descriptors = {
            0x1111: _descriptor(
                0x1111,
                {
                    1: [uzigbee.CLUSTER_ID_ON_OFF, uzigbee.CLUSTER_ID_LEVEL_CONTROL],
                    2: [uzigbee.CLUSTER_ID_TEMP_MEASUREMENT],
                },
                manufacturer_code=0x1A2B,
                endpoint_meta={
                    1: {"profile_id": 0x0104, "device_id": 0x0101, "device_version": 2},
                    2: {"profile_id": 0x0104, "device_id": 0x0302, "device_version": 1},
                },
                power_desc={
                    "current_power_source": 0x03,
                    "current_power_source_level": 0x07,
                },
            ),
            0x2222: _descriptor(
                0x2222,
                {
                    1: [uzigbee.CLUSTER_ID_DOOR_LOCK, uzigbee.CLUSTER_ID_ON_OFF],
                },
            ),
            0x3333: _descriptor(
                0x3333,
                {
                    1: [uzigbee.CLUSTER_ID_ON_OFF],
                },
            ),
            0x4444: _descriptor(
                0x4444,
                {
                    1: [uzigbee.CLUSTER_ID_ON_OFF],
                },
            ),
            0x6666: _descriptor(
                0x6666,
                {
                    1: [
                        uzigbee.CLUSTER_ID_THERMOSTAT,
                        uzigbee.CLUSTER_ID_WINDOW_COVERING,
                        uzigbee.CLUSTER_ID_IAS_ZONE,
                        uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT,
                    ],
                },
                endpoint_meta={
                    1: {"profile_id": 0x0104, "device_id": uzigbee.DEVICE_ID_THERMOSTAT, "device_version": 1},
                },
            ),
            0x7777: _descriptor(
                0x7777,
                {
                    1: [uzigbee.CLUSTER_ID_ON_OFF],
                },
                ieee_addr=b"\x10\x11\x12\x13\x14\x15\x16\x17",
            ),
            0x8888: _descriptor(
                0x8888,
                {
                    1: [uzigbee.CLUSTER_ID_ON_OFF],
                    2: [uzigbee.CLUSTER_ID_ON_OFF],
                    3: [uzigbee.CLUSTER_ID_TEMP_MEASUREMENT],
                    4: [uzigbee.CLUSTER_ID_TEMP_MEASUREMENT],
                },
                endpoint_meta={
                    1: {"profile_id": 0x0104, "device_id": 0x0000, "device_version": 1},
                    2: {"profile_id": 0x0104, "device_id": 0x0000, "device_version": 1},
                    3: {"profile_id": 0x0104, "device_id": 0x0302, "device_version": 1},
                    4: {"profile_id": 0x0104, "device_id": 0x0302, "device_version": 1},
                },
            ),
            0x9999: _descriptor(
                0x9999,
                {
                    1: [
                        uzigbee.CLUSTER_ID_ON_OFF,
                        uzigbee.CLUSTER_ID_LEVEL_CONTROL,
                        uzigbee.CLUSTER_ID_COLOR_CONTROL,
                    ],
                },
                endpoint_meta={
                    1: {"profile_id": 0x0104, "device_id": uzigbee.DEVICE_ID_COLOR_DIMMABLE_LIGHT, "device_version": 1},
                },
            ),
        }
        self._discover_failures_remaining = {}
        self._attr_values = {
            (1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF): True,
            (1, uzigbee.CLUSTER_ID_LEVEL_CONTROL, uzigbee.ATTR_LEVEL_CONTROL_CURRENT_LEVEL): 120,
            (2, uzigbee.CLUSTER_ID_TEMP_MEASUREMENT, uzigbee.ATTR_TEMP_MEASUREMENT_VALUE): 2150,
            (1, uzigbee.CLUSTER_ID_THERMOSTAT, uzigbee.ATTR_THERMOSTAT_LOCAL_TEMPERATURE): 2235,
            (1, uzigbee.CLUSTER_ID_THERMOSTAT, uzigbee.ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT): 2050,
            (1, uzigbee.CLUSTER_ID_THERMOSTAT, uzigbee.ATTR_THERMOSTAT_SYSTEM_MODE): 4,
            (1, uzigbee.CLUSTER_ID_WINDOW_COVERING, uzigbee.ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE): 65,
            (1, uzigbee.CLUSTER_ID_WINDOW_COVERING, uzigbee.ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE): 10,
            (1, uzigbee.CLUSTER_ID_IAS_ZONE, uzigbee.ATTR_IAS_ZONE_STATUS): 0,
            (1, uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT, uzigbee.ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER): 115,
            (1, uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT, uzigbee.ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE): 231,
            (1, uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT, uzigbee.ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT): 480,
            (2, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF): False,
            (3, uzigbee.CLUSTER_ID_TEMP_MEASUREMENT, uzigbee.ATTR_TEMP_MEASUREMENT_VALUE): 2010,
            (4, uzigbee.CLUSTER_ID_TEMP_MEASUREMENT, uzigbee.ATTR_TEMP_MEASUREMENT_VALUE): 2230,
            (1, uzigbee.CLUSTER_ID_COLOR_CONTROL, uzigbee.ATTR_COLOR_CONTROL_CURRENT_X): 32100,
            (1, uzigbee.CLUSTER_ID_COLOR_CONTROL, uzigbee.ATTR_COLOR_CONTROL_CURRENT_Y): 19700,
            (1, uzigbee.CLUSTER_ID_COLOR_CONTROL, uzigbee.ATTR_COLOR_CONTROL_COLOR_TEMPERATURE): 280,
        }

    def init(self, role):
        self.calls.append(("init", int(role)))

    def on_signal(self, callback=None):
        self.calls.append(("on_signal", callback is not None))
        self._signal_cb = callback

    def on_attribute(self, callback=None):
        self.calls.append(("on_attribute", callback is not None))
        self._attr_cb = callback

    def start(self, form_network=False):
        self.calls.append(("start", bool(form_network)))

    def create_on_off_switch(self, endpoint_id=1):
        self.calls.append(("create_on_off_switch", int(endpoint_id)))

    def register_device(self):
        self.calls.append(("register_device",))

    def set_pan_id(self, pan_id):
        self.calls.append(("set_pan_id", int(pan_id)))
        self._runtime_pan_id = int(pan_id) & 0xFFFF

    def set_extended_pan_id(self, ext_pan_id):
        self.calls.append(("set_extended_pan_id", bytes(ext_pan_id)))
        self._runtime_ext_pan = bytes(ext_pan_id)

    def set_primary_channel_mask(self, channel_mask):
        self.calls.append(("set_primary_channel_mask", int(channel_mask)))
        mask = int(channel_mask)
        if mask > 0 and (mask & (mask - 1)) == 0:
            channel = 0
            while mask > 1:
                mask >>= 1
                channel += 1
            if 11 <= int(channel) <= 26:
                self._runtime_channel = int(channel)

    def enable_wifi_i154_coex(self):
        self.calls.append(("enable_wifi_i154_coex",))

    def permit_join(self, duration_s=60):
        self.calls.append(("permit_join", int(duration_s)))

    def get_last_joined_short_addr(self):
        self.calls.append(("get_last_joined_short_addr",))
        return self._last_joined_short

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
        self.calls.append(
            (
                "discover_node_descriptors",
                int(dst_short_addr),
                endpoint_ids,
                bool(include_power_desc),
                bool(include_green_power),
                int(timeout_ms),
                int(poll_ms),
                bool(strict),
            )
        )
        key = int(dst_short_addr)
        failures_remaining = int(self._discover_failures_remaining.get(key, 0))
        if failures_remaining > 0:
            self._discover_failures_remaining[key] = failures_remaining - 1
            raise OSError(110, "timeout")
        return self._descriptors[int(dst_short_addr)]

    def get_attribute(self, endpoint_id, cluster_id, attr_id, cluster_role=1):
        self.calls.append(("get_attribute", int(endpoint_id), int(cluster_id), int(attr_id), int(cluster_role)))
        return self._attr_values[(int(endpoint_id), int(cluster_id), int(attr_id))]

    def set_attribute(self, endpoint_id, cluster_id, attr_id, value, cluster_role=1, check=False):
        key = (int(endpoint_id), int(cluster_id), int(attr_id))
        self.calls.append(
            (
                "set_attribute",
                int(endpoint_id),
                int(cluster_id),
                int(attr_id),
                value,
                int(cluster_role),
                bool(check),
            )
        )
        self._attr_values[key] = value
        return value

    def configure_reporting(
        self,
        src_endpoint=1,
        dst_short_addr=0x0000,
        dst_endpoint=1,
        cluster_id=0,
        attr_id=0,
        attr_type=0,
        min_interval=0,
        max_interval=300,
        reportable_change=None,
    ):
        self.calls.append(
            (
                "configure_reporting",
                int(src_endpoint),
                int(dst_short_addr),
                int(dst_endpoint),
                int(cluster_id),
                int(attr_id),
                int(attr_type),
                int(min_interval),
                int(max_interval),
                None if reportable_change is None else int(reportable_change),
            )
        )
        return True

    def send_on_off_cmd(self, dst_short_addr, dst_endpoint=1, src_endpoint=1, cmd_id=2):
        self.calls.append(("send_on_off_cmd", int(dst_short_addr), int(dst_endpoint), int(src_endpoint), int(cmd_id)))

    def send_level_cmd(self, dst_short_addr, level, dst_endpoint=1, src_endpoint=1, transition_ds=0, with_onoff=True):
        self.calls.append(
            (
                "send_level_cmd",
                int(dst_short_addr),
                int(level),
                int(dst_endpoint),
                int(src_endpoint),
                int(transition_ds),
                bool(with_onoff),
            )
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
        self.calls.append(
            (
                "send_color_move_to_color_cmd",
                int(dst_short_addr),
                int(color_x),
                int(color_y),
                int(dst_endpoint),
                int(src_endpoint),
                int(transition_ds),
            )
        )

    def send_color_move_to_color_temperature_cmd(
        self,
        dst_short_addr,
        color_temperature,
        dst_endpoint=1,
        src_endpoint=1,
        transition_ds=0,
    ):
        self.calls.append(
            (
                "send_color_move_to_color_temperature_cmd",
                int(dst_short_addr),
                int(color_temperature),
                int(dst_endpoint),
                int(src_endpoint),
                int(transition_ds),
            )
        )

    def send_lock_cmd(self, dst_short_addr, lock=True, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_lock_cmd", int(dst_short_addr), bool(lock), int(dst_endpoint), int(src_endpoint)))

    def send_bind_cmd(self, src_ieee_addr, cluster_id, dst_ieee_addr, req_dst_short_addr, src_endpoint=1, dst_endpoint=1):
        self.calls.append(
            (
                "send_bind_cmd",
                bytes(src_ieee_addr),
                int(cluster_id),
                bytes(dst_ieee_addr),
                int(req_dst_short_addr),
                int(src_endpoint),
                int(dst_endpoint),
            )
        )

    def get_ieee_addr(self):
        self.calls.append(("get_ieee_addr",))
        return b"\x01\x02\x03\x04\x05\x06\x07\x08"

    def get_network_runtime(self):
        self.calls.append(("get_network_runtime",))
        return {
            "channel": int(self._runtime_channel),
            "pan_id": int(self._runtime_pan_id),
            "extended_pan_id": bytes(self._runtime_ext_pan),
            "short_addr": int(self._runtime_short_addr),
            "formed": True,
            "joined": True,
        }


def test_discover_device_maps_features_and_endpoints():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x1111)

    assert device.short_addr == 0x1111
    assert device.endpoint_for(uzigbee.CLUSTER_ID_ON_OFF) == 1
    assert device.endpoint_for(uzigbee.CLUSTER_ID_LEVEL_CONTROL) == 1
    assert device.endpoint_for(uzigbee.CLUSTER_ID_TEMP_MEASUREMENT) == 2
    assert device.has_feature("on_off") is True
    assert device.has_feature("level") is True
    assert device.has_feature("temperature") is True
    assert coordinator.get_device(0x1111) is device


def test_coordinator_start_applies_network_identity_settings():
    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        pan_id=0x6C6C,
        extended_pan_id="00124b0001c6c6c6",
        channel=26,
    )

    coordinator.start(form_network=True)

    assert coordinator.network_mode == "fixed"
    assert ("set_extended_pan_id", bytes.fromhex("00124b0001c6c6c6")) in stack.calls
    assert ("set_pan_id", 0x6C6C) in stack.calls
    assert ("set_primary_channel_mask", 1 << 26) in stack.calls
    assert ("enable_wifi_i154_coex",) in stack.calls
    assert ("create_on_off_switch", 1) in stack.calls
    assert ("register_device",) in stack.calls


def test_coordinator_auto_mode_without_overrides_selects_dynamic_channel():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, auto_channel_scan_wifi=False)

    coordinator.start(form_network=True)
    info = coordinator.network_info()

    assert coordinator.network_mode == "auto"
    assert ("set_extended_pan_id", bytes.fromhex("00124b0001c6c6c6")) not in stack.calls
    assert ("set_pan_id", 0x6C6C) not in stack.calls
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]
    assert set_channel_calls == [("set_primary_channel_mask", 1 << 15)]
    assert info["network_mode"] == "auto"
    assert info["profile"]["source"] == "auto"
    assert info["profile"]["channel_mask"] == (1 << 15)
    assert info["profile"]["pan_id"] == 0x6C6C
    assert info["profile"]["extended_pan_id"] == "00124b0001c6c6c6"
    assert info["started"] is True
    assert info["form_network"] is True
    assert info["auto_channel"]["strategy"] == "preferred_fallback"
    assert info["auto_channel"]["selected_channel"] == 15


def test_coordinator_auto_mode_syncs_profile_from_runtime_after_formation_signal():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, auto_channel_scan_wifi=False)
    coordinator.start(form_network=True)

    stack.get_network_runtime = lambda: {
        "channel": 21,
        "pan_id": 0x1A62,
        "extended_pan_id": bytes.fromhex("1022334455667788"),
        "short_addr": 0x0000,
        "formed": True,
        "joined": True,
    }
    stack._signal_cb(uzigbee.SIGNAL_FORMATION, 0)
    info = coordinator.network_info()

    assert info["profile"]["channel_mask"] == (1 << 21)
    assert info["profile"]["pan_id"] == 0x1A62
    assert info["profile"]["extended_pan_id"] == "1022334455667788"
    assert info["profile"]["formed_at_ms"] is not None


def test_coordinator_auto_mode_wifi_aware_channel_selection():
    stack = _FakeStack()
    wifi_scan = (
        (b"ap1", b"", 1, -35, 0, 0),
        (b"ap2", b"", 6, -30, 0, 0),
        (b"ap3", b"", 11, -40, 0, 0),
    )
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        auto_channel_scan_wifi=True,
        auto_channel_scan_fn=lambda: wifi_scan,
    )

    coordinator.start(form_network=True)
    info = coordinator.network_info()
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]

    assert set_channel_calls == [("set_primary_channel_mask", 1 << 25)]
    assert info["profile"]["channel_mask"] == (1 << 25)
    assert info["auto_channel"]["strategy"] == "wifi_aware"
    assert info["auto_channel"]["selected_channel"] == 25
    assert info["auto_channel"]["wifi_scan_count"] == 3


def test_coordinator_auto_mode_honors_channel_blacklist():
    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        auto_channel_scan_wifi=False,
        auto_channel_blacklist=(15, 20, 25),
    )

    coordinator.start(form_network=True)
    info = coordinator.network_info()
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]

    assert set_channel_calls == [("set_primary_channel_mask", 1 << 11)]
    assert info["profile"]["channel_mask"] == (1 << 11)
    assert info["auto_channel"]["selected_channel"] == 11


def test_coordinator_guided_mode_prefers_restored_profile():
    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        network_mode="guided",
        auto_channel_scan_wifi=False,
    )
    coordinator._network_profile.update(
        channel_mask=(1 << 20),
        pan_id=0x3344,
        extended_pan_id=bytes.fromhex("1022334455667788"),
        source="restored",
    )

    coordinator.start(form_network=True)
    info = coordinator.network_info()

    assert ("set_primary_channel_mask", 1 << 20) in stack.calls
    assert ("set_pan_id", 0x3344) in stack.calls
    assert ("set_extended_pan_id", bytes.fromhex("1022334455667788")) in stack.calls
    assert info["network_mode"] == "guided"
    assert info["auto_channel"]["strategy"] == "guided_restored_profile"
    assert info["profile"]["source"] == "guided"
    assert info["profile"]["channel_mask"] == (1 << 20)
    assert info["profile"]["pan_id"] == 0x3344
    assert info["profile"]["extended_pan_id"] == "1022334455667788"


def test_coordinator_guided_mode_falls_back_to_auto_channel_when_profile_unknown():
    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        network_mode="guided",
        auto_channel_scan_wifi=False,
    )

    coordinator.start(form_network=True)
    info = coordinator.network_info()
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]
    set_pan_calls = [call for call in stack.calls if call[0] == "set_pan_id"]
    set_ext_pan_calls = [call for call in stack.calls if call[0] == "set_extended_pan_id"]

    assert set_channel_calls == [("set_primary_channel_mask", 1 << 15)]
    assert set_pan_calls == []
    assert set_ext_pan_calls == []
    assert info["network_mode"] == "guided"
    assert info["auto_channel"]["strategy"] == "guided_preferred_fallback"
    assert info["auto_channel"]["selected_channel"] == 15
    assert info["profile"]["source"] == "guided"
    assert info["profile"]["channel_mask"] == (1 << 15)


def test_coordinator_self_heal_reforms_after_panid_conflict_signal():
    stack = _FakeStack()
    events = []
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        self_heal_enabled=True,
        self_heal_retry_max=1,
        self_heal_retry_base_ms=0,
        self_heal_retry_max_backoff_ms=0,
    )
    coordinator.on_commissioning_event(lambda payload: events.append(dict(payload)))
    coordinator.start(form_network=True)
    baseline_start_calls = len([call for call in stack.calls if call[0] == "start"])

    stack._signal_cb(network.SIGNAL_PANID_CONFLICT_DETECTED, 0)
    info = coordinator.network_info()
    start_calls = [call for call in stack.calls if call[0] == "start"]

    assert len(start_calls) >= baseline_start_calls + 1
    assert start_calls[-1] == ("start", True)
    assert info["self_heal"]["stats"]["panid_conflicts"] == 1
    assert info["self_heal"]["stats"]["attempts"] >= 1
    assert info["self_heal"]["stats"]["success"] >= 1
    assert len(events) >= 2
    assert events[0]["event"] == "panid_conflict_detected"
    assert events[1]["event"] == "self_heal_retry"


def test_coordinator_self_heal_retriggers_after_steering_failure_signal():
    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        self_heal_enabled=True,
        self_heal_retry_max=1,
        self_heal_retry_base_ms=0,
        self_heal_retry_max_backoff_ms=0,
    )
    coordinator.start(form_network=True)
    baseline_start_calls = len([call for call in stack.calls if call[0] == "start"])

    stack._signal_cb(network.SIGNAL_STEERING, -1)
    info = coordinator.network_info()
    start_calls = [call for call in stack.calls if call[0] == "start"]

    assert len(start_calls) >= baseline_start_calls + 1
    assert start_calls[-1] == ("start", False)
    assert info["self_heal"]["stats"]["steering_failures"] == 1
    assert info["self_heal"]["stats"]["attempts"] >= 1


def test_coordinator_commissioning_stats_tracks_form_join_timeout_and_conflict():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, self_heal_enabled=False)
    coordinator.start(form_network=True)
    stack._signal_cb(network.SIGNAL_FORMATION, 0)
    stack._signal_cb(network.SIGNAL_STEERING, 116)
    stack._signal_cb(network.SIGNAL_PANID_CONFLICT_DETECTED, 0)

    stats = coordinator.commissioning_stats()
    info = coordinator.network_info()

    assert stats["start_count"] == 1
    assert stats["form_attempts"] >= 1
    assert stats["form_success"] >= 1
    assert stats["join_failures"] >= 1
    assert stats["timeout_events"] >= 1
    assert stats["conflict_events"] == 1
    assert "commissioning" in info
    assert info["commissioning"]["conflict_events"] == 1


def test_coordinator_commissioning_stats_reset():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, self_heal_enabled=False)
    coordinator.start(form_network=True)
    stack._signal_cb(network.SIGNAL_FORMATION, 0)
    before = coordinator.commissioning_stats()
    coordinator.commissioning_stats(reset=True)
    after = coordinator.commissioning_stats()

    assert before["start_count"] == 1
    assert before["form_success"] >= 1
    assert after["start_count"] == 0
    assert after["form_success"] == 0


def test_coordinator_configure_auto_channel_updates_policy():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    cfg = coordinator.configure_auto_channel(
        auto_channel_mask=(1 << 15) | (1 << 20),
        auto_channel_preferred=(20, 15),
        auto_channel_blacklist=(15,),
        auto_channel_scan_wifi=False,
        auto_channel_scan_fn=lambda: (),
    )

    assert cfg["auto_channel_mask"] == ((1 << 15) | (1 << 20))
    assert cfg["auto_channel_preferred"] == (20, 15)
    assert cfg["auto_channel_blacklist"] == (15,)
    assert cfg["auto_channel_scan_wifi"] is False
    assert cfg["scan_fn_configured"] is True

    coordinator.start(form_network=True)
    info = coordinator.network_info()
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]

    assert set_channel_calls == [("set_primary_channel_mask", 1 << 20)]
    assert info["auto_channel"]["selected_channel"] == 20


def test_coordinator_self_heal_policy_roundtrip_in_registry_snapshot():
    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        self_heal_enabled=False,
    )
    coordinator.configure_self_heal(
        enabled=True,
        retry_max=3,
        retry_base_ms=25,
        retry_max_backoff_ms=200,
    )
    snapshot = coordinator.dump_registry()

    restored = network.Coordinator(stack=_FakeStack(), auto_discovery=False)
    restored.restore_registry(snapshot, merge=False)
    info = restored.network_info()

    assert info["self_heal"]["policy"]["enabled"] is True
    assert info["self_heal"]["policy"]["retry_max"] == 3
    assert info["self_heal"]["policy"]["retry_base_ms"] == 25
    assert info["self_heal"]["policy"]["retry_max_backoff_ms"] == 200


def test_coordinator_network_info_includes_runtime_snapshot():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)

    coordinator.start(form_network=True)
    info = coordinator.network_info()

    assert ("get_network_runtime",) in stack.calls
    assert info["channel"] == 15
    assert info["pan_id"] == 0x6C6C
    assert info["extended_pan_id"] == bytes.fromhex("00124b0001c6c6c6")
    assert info["extended_pan_id_hex"] == "00124b0001c6c6c6"
    assert info["short_addr"] == 0x0000
    assert info["formed"] is True
    assert info["joined"] is True


def test_discover_device_maps_duplicate_features_to_multiple_endpoints():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x8888)

    assert device.endpoint_for(uzigbee.CLUSTER_ID_ON_OFF) == 1
    assert device.endpoints_for(uzigbee.CLUSTER_ID_ON_OFF) == (1, 2)
    assert device.endpoints_for(uzigbee.CLUSTER_ID_TEMP_MEASUREMENT) == (3, 4)
    assert device.feature_endpoints("on_off") == (1, 2)
    assert device.feature_endpoints("temperature") == (3, 4)
    assert device.endpoints() == (1, 2, 3, 4)


def test_endpoint_selector_api_for_duplicate_features():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x8888)

    assert device.switch(2).read.on_off() is False
    assert device.temperature_sensor(1).read.temperature() == 20.1
    assert device.temperature_sensor(2).read.temperature() == 22.3

    assert device.switch(2).on() is True
    assert ("send_on_off_cmd", 0x8888, 2, 1, uzigbee.CMD_ON_OFF_ON) in stack.calls

    assert device.endpoint(1).off() is False
    assert ("send_on_off_cmd", 0x8888, 1, 1, uzigbee.CMD_ON_OFF_OFF) in stack.calls

    assert device.get_state(
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        endpoint_id=2,
    ) is True
    assert device.get_state(
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        endpoint_id=1,
    ) is False

    try:
        device.feature("on_off", selector=None)
        raised = False
    except uzigbee.ZigbeeError:
        raised = True
    assert raised is True


def test_discovered_device_identity_model():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x1111)
    identity = device.identity

    assert identity.short_addr == 0x1111
    assert identity.manufacturer_code == 0x1A2B
    assert identity.endpoints == (1, 2)
    assert identity.primary_endpoint == 1
    assert identity.profile_id == 0x0104
    assert identity.device_id == 0x0101
    assert identity.device_version == 2
    assert identity.power_source == 0x03
    assert identity.power_source_level == 0x07
    ep2 = identity.endpoint(2)
    assert ep2["device_id"] == 0x0302
    assert ep2["input_clusters"] == (uzigbee.CLUSTER_ID_TEMP_MEASUREMENT,)

    as_dict = device.to_dict()
    assert as_dict["identity"]["manufacturer_code"] == 0x1A2B
    assert as_dict["identity"]["device_id"] == 0x0101


def test_discovered_device_identity_ieee_export():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x7777)

    assert device.identity.ieee_addr == b"\x10\x11\x12\x13\x14\x15\x16\x17"
    assert device.ieee_addr == b"\x10\x11\x12\x13\x14\x15\x16\x17"
    assert device.ieee_hex == "1011121314151617"
    as_dict = device.to_dict()
    assert as_dict["identity"]["ieee_addr"] == "1011121314151617"


def test_identity_fallback_when_descriptors_missing():
    stack = _FakeStack()
    stack._descriptors[0x5555] = {
        "short_addr": 0x5555,
        "endpoint_ids": [],
        "active_endpoints": {"status": 0, "count": 0, "endpoints": []},
        "node_descriptor": {"status": 0, "addr": 0x5555, "node_desc": None},
        "simple_descriptors": [],
        "power_descriptor": None,
        "errors": [],
    }

    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x5555)

    assert device.identity.short_addr == 0x5555
    assert device.identity.manufacturer_code is None
    assert device.identity.endpoints == ()
    assert device.identity.primary_endpoint is None
    assert device.identity.endpoint() is None


def test_find_devices_filters_and_select_device():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    coordinator.discover_device(0x1111)
    coordinator.discover_device(0x6666)
    coordinator.discover_device(0x7777)

    temp_devices = coordinator.find_devices(feature="temperature")
    assert len(temp_devices) == 1
    assert temp_devices[0].short_addr == 0x1111

    thermostat_devices = coordinator.find_devices(
        features=("thermostat", "cover"),
        device_id=uzigbee.DEVICE_ID_THERMOSTAT,
    )
    assert len(thermostat_devices) == 1
    assert thermostat_devices[0].short_addr == 0x6666

    by_mfg = coordinator.find_devices(manufacturer_code=0x1234)
    assert len(by_mfg) >= 2

    selected = coordinator.select_device(feature="on_off", ieee_addr="10:11:12:13:14:15:16:17")
    assert selected is not None
    assert selected.short_addr == 0x7777


def test_get_device_by_ieee_roundtrip_with_registry_persistence():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    coordinator.discover_device(0x7777)

    first = coordinator.get_device_by_ieee(b"\x10\x11\x12\x13\x14\x15\x16\x17")
    assert first is not None
    assert first.short_addr == 0x7777

    snapshot = coordinator.dump_registry()
    restored = network.Coordinator(stack=_FakeStack(), auto_discovery=False)
    restored.restore_registry(snapshot, merge=False)
    second = restored.get_device_by_ieee("1011121314151617")
    assert second is not None
    assert second.short_addr == 0x7777


def test_device_lifecycle_online_filters_and_manual_marking(monkeypatch):
    now_ms = {"value": 1000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        offline_after_ms=100,
    )
    device = coordinator.discover_device(0x1111)
    assert device.short_addr == 0x1111

    assert coordinator.get_device(0x1111, online=True) is device
    assert len(coordinator.list_devices(online=True)) == 1
    assert len(coordinator.find_devices(feature="on_off", online=True)) == 1

    now_ms["value"] += 150
    assert coordinator.get_device(0x1111, online=True) is None
    offline_devices = coordinator.list_devices(online=False)
    assert len(offline_devices) == 1
    assert offline_devices[0].short_addr == 0x1111

    status = coordinator.device_status(0x1111)
    assert status["online"] is False
    assert status["last_seen_age_ms"] >= 100

    assert coordinator.mark_device_online(0x1111, source="test") is True
    assert coordinator.get_device(0x1111, online=True) is not None
    status = coordinator.device_status(0x1111)
    assert status["online"] is True
    assert status["last_seen_source"] == "test"

    assert coordinator.mark_device_offline(0x1111, reason="manual_test") is True
    assert coordinator.select_device(feature="on_off", online=True) is None
    selected_offline = coordinator.select_device(feature="on_off", online=False)
    assert selected_offline is not None
    assert selected_offline.short_addr == 0x1111
    status = coordinator.device_status(0x1111)
    assert status["forced_offline"] is True
    assert status["offline_reason"] == "manual_test"


def test_device_read_and_control_paths():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x1111)

    assert device.read.on_off() is True
    assert device.read.level() == 120
    assert device.read.temperature_raw() == 2150
    assert device.read.temperature() == 21.5

    assert device.on() is True
    assert device.set_level(99, transition_ds=5, with_onoff=True) == 99
    assert ("send_on_off_cmd", 0x1111, 1, 1, uzigbee.CMD_ON_OFF_ON) in stack.calls
    assert ("send_level_cmd", 0x1111, 99, 1, 1, 5, True) in stack.calls
    onoff_meta = device.state_info(uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF)
    assert onoff_meta["source"] == "control"
    assert onoff_meta["authoritative"] is False


def test_remote_direct_read_uses_cache_when_local_short_is_known():
    stack = _FakeStack()
    stack.get_short_addr = lambda: 0x0000
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x1111)

    device.switch(1).on()
    stack.calls.clear()

    assert device.switch(1).read.on_off(use_cache=False) is True
    assert not any(call and call[0] == "get_attribute" for call in stack.calls)


def test_remote_direct_read_raises_when_cache_is_missing():
    stack = _FakeStack()
    stack.get_short_addr = lambda: 0x0000
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x1111)

    try:
        device.temperature_sensor().read.temperature(use_cache=False)
        raised = False
    except uzigbee.ZigbeeError:
        raised = True

    assert raised is True
    assert not any(call and call[0] == "get_attribute" for call in stack.calls)


def test_state_engine_refresh_policy_refreshes_stale_cache(monkeypatch):
    now_ms = {"value": 1000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        state_ttl_ms=100,
        stale_read_policy="refresh",
    )
    device = coordinator.discover_device(0x1111)

    assert device.read.on_off() is True
    stack._attr_values[(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF)] = False
    now_ms["value"] += 150
    assert device.read.on_off() is False

    attr_reads = [
        call for call in stack.calls
        if call and call[0] == "get_attribute" and call[1] == 1 and call[2] == uzigbee.CLUSTER_ID_ON_OFF
    ]
    assert len(attr_reads) == 2


def test_state_engine_raise_policy_raises_on_stale_cache(monkeypatch):
    now_ms = {"value": 2000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        state_ttl_ms=100,
        stale_read_policy="raise",
    )
    device = coordinator.discover_device(0x1111)

    assert device.read.on_off() is True
    now_ms["value"] += 200

    try:
        device.read.on_off()
        raised = False
    except uzigbee.ZigbeeError:
        raised = True
    assert raised is True


def test_configure_state_engine_updates_existing_devices():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, state_cache_max=8)
    device = coordinator.discover_device(0x1111)
    cfg = coordinator.configure_state_engine(state_ttl_ms=3210, stale_read_policy="refresh", state_cache_max=24)

    assert cfg["state_ttl_ms"] == 3210
    assert cfg["stale_read_policy"] == "refresh"
    assert cfg["state_cache_max"] == 24
    assert device.state_ttl_ms == 3210
    assert device.stale_read_policy == "refresh"
    assert device.state_cache_max == 24


def test_state_cache_max_prunes_oldest_entries(monkeypatch):
    now_ms = {"value": 1000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, state_cache_max=2)
    device = coordinator.discover_device(0x1111)
    assert device.state_cache_max == 8

    first_key = (0x9000, 0x0001)
    last_key = (0x9008, 0x0001)
    for idx in range(9):
        device._write_state(
            (0x9000 + idx, 0x0001),
            idx,
            source="test",
            authoritative=True,
            endpoint_id=1,
        )
        now_ms["value"] += 1

    assert len(device.state) == 8
    assert len(device.state_meta) == 8
    assert len(device.state_by_endpoint) == 8
    assert len(device.state_meta_by_endpoint) == 8
    assert device.get_state(first_key[0], first_key[1], default=None) is None
    assert device.get_state(last_key[0], last_key[1], default=None) == 8


def test_capability_matrix_advanced_read_wrappers():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x6666)

    assert device.has_feature("thermostat") is True
    assert device.has_feature("cover") is True
    assert device.has_feature("ias_zone") is True
    assert device.has_feature("energy") is True

    assert device.read.thermostat_temperature() == 22.35
    assert device.read.thermostat_heating_setpoint() == 20.5
    assert device.read.thermostat_system_mode() == 4
    assert device.read.cover_lift() == 65
    assert device.read.cover_tilt() == 10
    assert device.read.ias_zone_status() == 0
    assert device.read.ias_alarm() is False
    assert device.read.power_w() == 115
    assert device.read.voltage_v() == 231
    assert device.read.current_a() == 0.48


def test_capability_matrix_advanced_control_wrappers():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x6666)

    assert device.set_thermostat_heating_setpoint(21.75) == 21.75
    assert device.set_thermostat_mode(3) == 3
    assert device.set_cover_position(42) == 42
    assert device.set_cover_tilt(17) == 17
    assert device.set_ias_alarm(True) is True
    assert device.set_power_w(180) == 180
    assert device.set_voltage_v(229) == 229
    assert device.set_current_a(1.25) == 1.25

    set_calls = [call for call in stack.calls if call and call[0] == "set_attribute"]
    assert len(set_calls) >= 8
    assert stack._attr_values[(1, uzigbee.CLUSTER_ID_THERMOSTAT, uzigbee.ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT)] == 2175
    assert stack._attr_values[(1, uzigbee.CLUSTER_ID_THERMOSTAT, uzigbee.ATTR_THERMOSTAT_SYSTEM_MODE)] == 3
    assert stack._attr_values[(1, uzigbee.CLUSTER_ID_WINDOW_COVERING, uzigbee.ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE)] == 42
    assert stack._attr_values[(1, uzigbee.CLUSTER_ID_WINDOW_COVERING, uzigbee.ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE)] == 17
    zone_status = stack._attr_values[(1, uzigbee.CLUSTER_ID_IAS_ZONE, uzigbee.ATTR_IAS_ZONE_STATUS)]
    assert (int(zone_status) & int(uzigbee.IAS_ZONE_STATUS_ALARM1)) != 0
    assert stack._attr_values[(1, uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT, uzigbee.ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER)] == 180
    assert stack._attr_values[(1, uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT, uzigbee.ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE)] == 229
    assert stack._attr_values[(1, uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT, uzigbee.ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT)] == 1250


def test_color_control_wrappers_and_reads():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x9999)

    assert device.has_feature("color") is True
    assert device.read.color_xy() == (32100, 19700)
    assert device.read.color_temperature() == 280

    xy = device.set_color_xy(30000, 20000, transition_ds=15)
    temp = device.set_color_temperature(325, transition_ds=20)
    assert xy == (30000, 20000)
    assert temp == 325

    assert (
        "send_color_move_to_color_cmd",
        0x9999,
        30000,
        20000,
        1,
        1,
        15,
    ) in stack.calls
    assert (
        "send_color_move_to_color_temperature_cmd",
        0x9999,
        325,
        1,
        1,
        20,
    ) in stack.calls


def test_automation_auto_reporting_per_capability():
    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        auto_configure_reporting=True,
        local_endpoint=1,
    )
    device = coordinator.discover_device(0x6666)

    reporting_calls = [call for call in stack.calls if call and call[0] == "configure_reporting"]
    assert len(reporting_calls) == 9
    automation = device.meta["automation"]
    assert automation["auto_configure_reporting"] is True
    report_summary = automation["reporting"]
    ok_entries = [entry for entry in report_summary if entry["status"] == "ok"]
    assert len(ok_entries) >= 4
    stats = coordinator.automation_stats()
    assert stats["reporting_applied"] == 9


def test_automation_auto_bind_skips_without_remote_ieee():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, auto_bind=True)
    device = coordinator.discover_device(0x6666)

    bind_meta = device.meta["automation"]["bind"]
    assert bind_meta["status"] == "skipped"
    assert bind_meta["reason"] == "missing_remote_ieee"
    stats = coordinator.automation_stats()
    assert stats["bind_attempted"] == 1
    assert stats["bind_skipped"] == 1


def test_automation_auto_bind_executes_when_ieee_present():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False, auto_bind=True)
    device = coordinator.discover_device(0x7777)

    bind_calls = [call for call in stack.calls if call and call[0] == "send_bind_cmd"]
    assert len(bind_calls) >= 1
    bind_meta = device.meta["automation"]["bind"]
    assert bind_meta["status"] in ("ok", "partial")


def test_registry_dump_restore_roundtrip():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x6666)
    assert device.read.power_w() == 115

    snapshot = coordinator.dump_registry()
    assert snapshot["schema"] == 1
    assert snapshot["network_mode"] == "auto"
    assert snapshot["network_profile"]["source"] == "auto"
    assert len(snapshot["devices"]) >= 1

    restored_coordinator = network.Coordinator(stack=_FakeStack(), auto_discovery=False)
    restored_count = restored_coordinator.restore_registry(snapshot, merge=False)
    assert restored_count >= 1

    restored = restored_coordinator.get_device(0x6666)
    assert restored is not None
    assert restored.identity.device_id == uzigbee.DEVICE_ID_THERMOSTAT
    assert restored.get_state(
        uzigbee.CLUSTER_ID_ELECTRICAL_MEASUREMENT,
        uzigbee.ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER,
    ) == 115


def test_registry_save_load_with_write_throttle(tmp_path, monkeypatch):
    now_ms = {"value": 20000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])
    db_path = tmp_path / "uzigbee_registry.json"

    stack = _FakeStack()
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        persistence_path=str(db_path),
        persistence_min_interval_ms=1000,
    )
    coordinator.discover_device(0x1111)

    first = coordinator.save_registry()
    assert first["saved"] is True

    second = coordinator.save_registry()
    assert second["saved"] is False
    assert second["reason"] == "throttled"

    now_ms["value"] += 1000
    third = coordinator.save_registry()
    assert third["saved"] is True

    loaded = network.Coordinator(
        stack=_FakeStack(),
        auto_discovery=False,
        persistence_path=str(db_path),
    )
    result = loaded.load_registry()
    assert result["loaded"] is True
    assert result["restored"] >= 1
    assert loaded.get_device(0x1111) is not None


def test_registry_restore_restores_network_profile():
    source = network.Coordinator(
        stack=_FakeStack(),
        auto_discovery=False,
        channel=15,
        pan_id=0x1A62,
        extended_pan_id="00124b0001c6c6c6",
    )
    snapshot = source.dump_registry()

    restored = network.Coordinator(stack=_FakeStack(), auto_discovery=False)
    restored.restore_registry(snapshot, merge=False)
    info = restored.network_info()

    assert restored.network_mode == "fixed"
    assert info["profile"]["source"] == "fixed"
    assert info["profile"]["channel_mask"] == (1 << 15)
    assert info["profile"]["pan_id"] == 0x1A62
    assert info["profile"]["extended_pan_id"] == "00124b0001c6c6c6"


def test_attribute_callback_updates_cached_state():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x1111)

    coordinator._handle_attribute(
        1,
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        False,
        0,
    )
    assert device.state[(uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF)] is False
    meta = device.state_info(uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF)
    assert meta["source"] == "attribute"
    assert meta["authoritative"] is True


def test_attribute_callback_with_source_short_updates_only_target():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device_a = coordinator.discover_device(0x1111)
    device_b = coordinator.discover_device(0x3333)

    assert device_a.read.on_off() is True
    assert device_b.read.on_off() is True

    coordinator._handle_attribute(
        0x3333,
        1,
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        False,
        0x10,
        0,
    )

    assert device_b.state[(uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF)] is False
    assert device_a.state[(uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF)] is True
    b_meta = device_b.state_info(uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF)
    assert b_meta["source_short_addr"] == 0x3333
    assert b_meta["attr_type"] == 0x10


def test_attribute_callback_with_source_short_routes_to_matching_endpoint():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=False)
    device = coordinator.discover_device(0x8888)

    assert device.switch(1).read.on_off() is True
    assert device.switch(2).read.on_off() is False

    coordinator._handle_attribute(
        0x8888,
        2,
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        True,
        0x10,
        0,
    )

    assert device.get_state(
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        endpoint_id=1,
    ) is True
    assert device.get_state(
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        endpoint_id=2,
    ) is True
    meta = device.state_info(
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        endpoint_id=2,
    )
    assert meta["source_short_addr"] == 0x8888
    assert meta["source_endpoint"] == 2


def test_auto_discovery_on_join_signal():
    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=True)
    coordinator.start(form_network=True)
    assert stack._signal_cb is not None

    stack._signal_cb(uzigbee.SIGNAL_DEVICE_ANNCE, 0)
    discovered = coordinator.get_device(0x2222)
    assert discovered is not None
    assert discovered.endpoint_for(uzigbee.CLUSTER_ID_DOOR_LOCK) == 1


def test_auto_discovery_debounce_blocks_repeated_join_signals(monkeypatch):
    now_ms = {"value": 1000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    coordinator = network.Coordinator(stack=stack, auto_discovery=True, join_debounce_ms=3000)
    coordinator.start(form_network=True)

    stack._last_joined_short = 0x2222
    stack._signal_cb(uzigbee.SIGNAL_DEVICE_ANNCE, 0)
    stack._signal_cb(network.SIGNAL_DEVICE_UPDATE, 0)

    discover_calls = [call for call in stack.calls if call and call[0] == "discover_node_descriptors"]
    assert len(discover_calls) == 1
    assert coordinator.discovery_stats()["debounced"] >= 1


def test_auto_discovery_retry_backoff_then_success(monkeypatch):
    now_ms = {"value": 1000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    stack._last_joined_short = 0x3333
    stack._discover_failures_remaining[0x3333] = 2

    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=True,
        join_debounce_ms=0,
        discovery_retry_max=3,
        discovery_retry_base_ms=100,
        discovery_retry_max_backoff_ms=800,
        fallback_without_power_desc=False,
    )
    coordinator.start(form_network=True)

    stack._signal_cb(uzigbee.SIGNAL_DEVICE_ANNCE, 0)
    assert coordinator.get_device(0x3333) is None
    assert coordinator.pending_discovery()

    now_ms["value"] += 90
    summary = coordinator.process_pending_discovery(max_items=1)
    assert summary["processed"] == 0

    now_ms["value"] += 10
    summary = coordinator.process_pending_discovery(max_items=1)
    assert summary["processed"] == 1
    assert summary["failed"] == 1

    now_ms["value"] += 200
    summary = coordinator.process_pending_discovery(max_items=1)
    assert summary["processed"] == 1
    assert summary["success"] == 1

    discovered = coordinator.get_device(0x3333)
    assert discovered is not None
    assert discovered.endpoint_for(uzigbee.CLUSTER_ID_ON_OFF) == 1
    stats = coordinator.discovery_stats()
    assert stats["requeued"] == 2
    assert stats["success"] >= 1


def test_auto_discovery_gives_up_after_retry_limit(monkeypatch):
    now_ms = {"value": 5000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    stack._last_joined_short = 0x4444
    stack._discover_failures_remaining[0x4444] = 9

    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=True,
        join_debounce_ms=0,
        discovery_retry_max=1,
        discovery_retry_base_ms=100,
        discovery_retry_max_backoff_ms=100,
    )
    coordinator.start(form_network=True)

    stack._signal_cb(uzigbee.SIGNAL_DEVICE_ANNCE, 0)
    assert coordinator.get_device(0x4444) is None
    assert coordinator.pending_discovery()

    now_ms["value"] += 100
    summary = coordinator.process_pending_discovery(max_items=2)
    assert summary["processed"] >= 1
    assert coordinator.get_device(0x4444) is None
    assert coordinator.pending_discovery() == ()
    stats = coordinator.discovery_stats()
    assert stats["gave_up"] == 1
    assert stats["last_error"]["short_addr"] == 0x4444


def test_discover_device_fallback_without_power_desc():
    stack = _FakeStack()
    original = stack.discover_node_descriptors
    attempts = {"count": 0}

    def _patched(
        dst_short_addr,
        endpoint_ids=None,
        include_power_desc=True,
        include_green_power=False,
        timeout_ms=5000,
        poll_ms=200,
        strict=True,
    ):
        attempts["count"] += 1
        if bool(include_power_desc):
            raise OSError(110, "timeout")
        return original(
            dst_short_addr,
            endpoint_ids=endpoint_ids,
            include_power_desc=include_power_desc,
            include_green_power=include_green_power,
            timeout_ms=timeout_ms,
            poll_ms=poll_ms,
            strict=strict,
        )

    stack.discover_node_descriptors = _patched
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=False,
        include_power_desc=True,
        fallback_without_power_desc=True,
    )
    device = coordinator.discover_device(0x1111, strict=False)

    assert device is not None
    assert attempts["count"] == 2
    assert device.endpoint_for(uzigbee.CLUSTER_ID_ON_OFF) == 1


def test_process_pending_discovery_queues_from_last_joined_hint(monkeypatch):
    now_ms = {"value": 9000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])

    stack = _FakeStack()
    stack._last_joined_short = 0x2222
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=True,
        join_debounce_ms=0,
        opportunistic_last_joined_scan=True,
    )
    coordinator.start(form_network=True)

    summary = coordinator.process_pending_discovery(max_items=2)
    assert summary["processed"] >= 1
    discovered = coordinator.get_device(0x2222)
    assert discovered is not None
    assert discovered.endpoint_for(uzigbee.CLUSTER_ID_DOOR_LOCK) == 1
    stats = coordinator.discovery_stats()
    assert stats["queue_enqueued"] >= 1


def test_auto_discovery_on_device_associated_signal():
    stack = _FakeStack()
    stack._last_joined_short = 0x2222
    coordinator = network.Coordinator(stack=stack, auto_discovery=True, join_debounce_ms=0)
    coordinator.start(form_network=True)

    stack._signal_cb(uzigbee.SIGNAL_DEVICE_ASSOCIATED, 0)
    discovered = coordinator.get_device(0x2222)
    assert discovered is not None
    assert discovered.endpoint_for(uzigbee.CLUSTER_ID_ON_OFF) == 1


def test_wait_for_device_auto_discovery_and_permit_join():
    stack = _FakeStack()
    stack._last_joined_short = 0x2222
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=True,
        join_debounce_ms=0,
        opportunistic_last_joined_scan=True,
    )
    coordinator.start(form_network=True)

    device = coordinator.wait_for_device(
        feature="on_off",
        timeout_ms=2000,
        poll_ms=20,
        process_batch=2,
        permit_join_s=120,
        auto_discover=True,
    )
    assert device is not None
    assert device.short_addr == 0x2222
    assert ("permit_join", 120) in stack.calls


def test_wait_for_device_timeout_returns_default(monkeypatch):
    now_ms = {"value": 1000}
    monkeypatch.setattr(network, "_ticks_ms", lambda: now_ms["value"])
    monkeypatch.setattr(network, "_sleep_ms", lambda ms: now_ms.__setitem__("value", int(now_ms["value"]) + int(ms)))

    stack = _FakeStack()
    stack._last_joined_short = 0xFFFF
    coordinator = network.Coordinator(
        stack=stack,
        auto_discovery=True,
        join_debounce_ms=0,
        opportunistic_last_joined_scan=True,
    )
    coordinator.start(form_network=True)

    missing = coordinator.wait_for_device(
        feature="on_off",
        timeout_ms=120,
        poll_ms=40,
        process_batch=1,
        default="missing",
    )
    assert missing == "missing"


def test_auto_discovery_ignores_unknown_short_fffe():
    stack = _FakeStack()
    stack._last_joined_short = 0xFFFE
    coordinator = network.Coordinator(stack=stack, auto_discovery=True, join_debounce_ms=0)
    coordinator.start(form_network=True)

    stack._signal_cb(uzigbee.SIGNAL_DEVICE_ANNCE, 0)
    assert coordinator.get_device(0xFFFE) is None

    discover_calls = [call for call in stack.calls if call and call[0] == "discover_node_descriptors"]
    assert discover_calls == []
