import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import uzigbee


class _FakeStack:
    def __init__(self):
        self.calls = []
        self._signal_cb = None
        self._attr_cb = None

    def init(self, role):
        self.calls.append(("init", int(role)))

    def on_signal(self, callback=None):
        self.calls.append(("on_signal", callback is not None))
        self._signal_cb = callback

    def on_attribute(self, callback=None):
        self.calls.append(("on_attribute", callback is not None))
        self._attr_cb = callback

    def register_device(self):
        self.calls.append(("register_device",))

    def start(self, form_network=False):
        self.calls.append(("start", bool(form_network)))

    def start_network_steering(self):
        self.calls.append(("start_network_steering",))

    def set_pan_id(self, pan_id):
        self.calls.append(("set_pan_id", int(pan_id)))

    def set_extended_pan_id(self, ext_pan_id):
        self.calls.append(("set_extended_pan_id", bytes(ext_pan_id)))

    def set_primary_channel_mask(self, channel_mask):
        self.calls.append(("set_primary_channel_mask", int(channel_mask)))

    def get_short_addr(self):
        self.calls.append(("get_short_addr",))
        return 0x3344

    def get_network_runtime(self):
        self.calls.append(("get_network_runtime",))
        return {
            "channel": 15,
            "pan_id": 0x1A62,
            "extended_pan_id": bytes.fromhex("00124b0001c6c6c6"),
            "short_addr": 0x3344,
            "formed": False,
            "joined": True,
        }

    def create_on_off_light(self, endpoint_id=1):
        self.calls.append(("create_on_off_light", int(endpoint_id)))

    def create_dimmable_light(self, endpoint_id=1):
        self.calls.append(("create_dimmable_light", int(endpoint_id)))

    def create_color_light(self, endpoint_id=1):
        self.calls.append(("create_color_light", int(endpoint_id)))

    def create_on_off_switch(self, endpoint_id=1):
        self.calls.append(("create_on_off_switch", int(endpoint_id)))

    def create_dimmable_switch(self, endpoint_id=1):
        self.calls.append(("create_dimmable_switch", int(endpoint_id)))

    def create_temperature_sensor(self, endpoint_id=1):
        self.calls.append(("create_temperature_sensor", int(endpoint_id)))

    def create_air_quality_sensor(self, endpoint_id=1):
        self.calls.append(("create_air_quality_sensor", int(endpoint_id)))

    def create_contact_sensor(self, endpoint_id=1):
        self.calls.append(("create_contact_sensor", int(endpoint_id)))

    def create_motion_sensor(self, endpoint_id=1):
        self.calls.append(("create_motion_sensor", int(endpoint_id)))

    def create_power_outlet(self, endpoint_id=1, with_metering=False):
        self.calls.append(("create_power_outlet", int(endpoint_id), bool(with_metering)))

    def create_ias_zone(self, endpoint_id=1, zone_type=0x0015):
        self.calls.append(("create_ias_zone", int(endpoint_id), int(zone_type)))

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
        self.calls.append(
            (
                "configure_reporting",
                int(dst_short_addr),
                int(cluster_id),
                int(attr_id),
                int(attr_type),
                int(src_endpoint),
                int(dst_endpoint),
                int(min_interval),
                int(max_interval),
                None if reportable_change is None else int(reportable_change),
            )
        )

    def get_ieee_addr(self):
        return bytes.fromhex("00124b0001020304")

    def send_bind_cmd(
        self,
        src_ieee_addr,
        cluster_id,
        dst_ieee_addr,
        req_dst_short_addr,
        src_endpoint=1,
        dst_endpoint=1,
    ):
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

    def set_attribute(self, endpoint_id, cluster_id, attr_id, value, cluster_role=1, check=False):
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


class _BusySteeringStack(_FakeStack):
    def start_network_steering(self):
        self.calls.append(("start_network_steering",))
        raise OSError(-1)


class _RuntimeAwareStack(_FakeStack):
    def __init__(self):
        super().__init__()
        self._runtime_channel = 15
        self._runtime_pan_id = 0x1A62
        self._runtime_ext_pan = bytes.fromhex("00124b0001c6c6c6")
        self._runtime_short_addr = 0x3344

    def set_pan_id(self, pan_id):
        super().set_pan_id(pan_id)
        self._runtime_pan_id = int(pan_id) & 0xFFFF

    def set_extended_pan_id(self, ext_pan_id):
        super().set_extended_pan_id(ext_pan_id)
        self._runtime_ext_pan = bytes(ext_pan_id)

    def set_primary_channel_mask(self, channel_mask):
        super().set_primary_channel_mask(channel_mask)
        mask = int(channel_mask)
        if mask > 0 and (mask & (mask - 1)) == 0:
            channel = 0
            while mask > 1:
                mask >>= 1
                channel += 1
            if 11 <= int(channel) <= 26:
                self._runtime_channel = int(channel)

    def get_network_runtime(self):
        self.calls.append(("get_network_runtime",))
        return {
            "channel": int(self._runtime_channel),
            "pan_id": int(self._runtime_pan_id),
            "extended_pan_id": bytes(self._runtime_ext_pan),
            "short_addr": int(self._runtime_short_addr),
            "formed": False,
            "joined": True,
        }


class _FlakySteeringStack(_FakeStack):
    def __init__(self, failures_before_success=1):
        super().__init__()
        self.failures_before_success = int(failures_before_success)
        self._attempts = 0

    def start_network_steering(self):
        self.calls.append(("start_network_steering",))
        self._attempts += 1
        if self._attempts <= self.failures_before_success:
            raise OSError(-1)
        return None


def test_router_bootstrap_lifecycle_and_auto_endpoints():
    stack = _FakeStack()
    seen = []

    router = (
        uzigbee.Router(stack=stack)
        .add_light()
        .add_switch(dimmable=True)
        .on_signal(lambda signal_id, status: seen.append((int(signal_id), int(status))))
        .start(join_parent=True)
    )

    assert router.endpoints() == (1, 2)
    calls = stack.calls
    assert ("init", uzigbee.ROLE_ROUTER) in calls
    assert ("on_signal", True) in calls
    assert ("on_attribute", True) in calls
    assert ("create_on_off_light", 1) in calls
    assert ("create_dimmable_switch", 2) in calls
    assert len([call for call in calls if call[0] == "register_device"]) == 2
    assert ("start", False) in calls
    assert ("start_network_steering",) in calls

    assert stack._signal_cb is not None
    stack._signal_cb(0x36, 0)
    assert seen == [(0x36, 0)]


def test_router_start_applies_network_identity_settings():
    stack = _FakeStack()
    router = uzigbee.Router(
        stack=stack,
        pan_id=0x6C6C,
        extended_pan_id="00124b0001c6c6c6",
        channel=26,
    ).add_light(endpoint_id=1)
    router.start(join_parent=True)

    assert router.commissioning_mode == "fixed"
    assert ("set_extended_pan_id", bytes.fromhex("00124b0001c6c6c6")) in stack.calls
    assert ("set_pan_id", 0x6C6C) in stack.calls
    assert ("set_primary_channel_mask", 1 << 26) in stack.calls


def test_router_auto_mode_uses_auto_join_mask_and_runtime_profile():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(endpoint_id=1)

    router.start(join_parent=True)
    info = router.network_info()

    assert router.commissioning_mode == "auto"
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]
    expected_mask = 0
    for channel in range(11, 27):
        expected_mask |= (1 << channel)
    assert set_channel_calls == [("set_primary_channel_mask", expected_mask)]
    set_pan_calls = [call for call in stack.calls if call[0] == "set_pan_id"]
    assert set_pan_calls == []
    set_ext_pan_calls = [call for call in stack.calls if call[0] == "set_extended_pan_id"]
    assert set_ext_pan_calls == []
    assert info["commissioning_mode"] == "auto"
    assert info["profile"]["source"] == "auto"
    assert info["profile"]["channel_mask"] == (1 << 15)
    assert info["profile"]["pan_id"] == 0x1A62
    assert info["profile"]["extended_pan_id"] == "00124b0001c6c6c6"
    assert info["auto_join"]["channel_mask"] == expected_mask


def test_router_network_info_includes_runtime_snapshot():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(endpoint_id=1)

    router.start(join_parent=True)
    info = router.network_info()

    assert ("get_network_runtime",) in stack.calls
    assert info["channel"] == 15
    assert info["pan_id"] == 0x1A62
    assert info["extended_pan_id"] == bytes.fromhex("00124b0001c6c6c6")
    assert info["extended_pan_id_hex"] == "00124b0001c6c6c6"
    assert info["short_addr"] == 0x3344
    assert info["formed"] is False
    assert info["joined"] is True


def test_router_configure_auto_join_policy():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(endpoint_id=1)
    cfg = router.configure_auto_join(
        auto_join_channel_mask=(1 << 15) | (1 << 20),
        join_retry_max=2,
        join_retry_base_ms=0,
        join_retry_max_backoff_ms=0,
    )

    assert cfg["auto_join_channel_mask"] == ((1 << 15) | (1 << 20))
    assert cfg["join_retry_max"] == 2
    assert cfg["join_retry_base_ms"] == 0
    assert cfg["join_retry_max_backoff_ms"] == 0

    router.start(join_parent=True)
    info = router.network_info()
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]

    assert set_channel_calls == [("set_primary_channel_mask", (1 << 15) | (1 << 20))]
    assert info["auto_join"]["join_retry_max"] == 2
    assert info["auto_join"]["join_retry_base_ms"] == 0
    assert info["auto_join"]["join_retry_max_backoff_ms"] == 0


def test_router_guided_mode_prefers_restored_profile():
    stack = _RuntimeAwareStack()
    router = uzigbee.Router(stack=stack, commissioning_mode="guided").add_light(endpoint_id=1)
    router._network_profile.update(
        channel_mask=(1 << 20),
        pan_id=0x3344,
        extended_pan_id=bytes.fromhex("1022334455667788"),
        source="restored",
    )

    router.start(join_parent=True)
    info = router.network_info()

    assert ("set_primary_channel_mask", 1 << 20) in stack.calls
    assert ("set_pan_id", 0x3344) in stack.calls
    assert ("set_extended_pan_id", bytes.fromhex("1022334455667788")) in stack.calls
    assert info["commissioning_mode"] == "guided"
    assert info["profile"]["source"] == "guided"
    assert info["profile"]["channel_mask"] == (1 << 20)
    assert info["profile"]["pan_id"] == 0x3344
    assert info["profile"]["extended_pan_id"] == "1022334455667788"


def test_router_guided_mode_falls_back_to_auto_join_mask_without_profile():
    stack = _RuntimeAwareStack()
    router = uzigbee.Router(
        stack=stack,
        commissioning_mode="guided",
        auto_join_channel_mask=(1 << 20),
    ).add_light(endpoint_id=1)

    router.start(join_parent=False)
    info = router.network_info()
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]
    set_pan_calls = [call for call in stack.calls if call[0] == "set_pan_id"]
    set_ext_pan_calls = [call for call in stack.calls if call[0] == "set_extended_pan_id"]

    assert set_channel_calls == [("set_primary_channel_mask", 1 << 20)]
    assert set_pan_calls == []
    assert set_ext_pan_calls == []
    assert info["commissioning_mode"] == "guided"
    assert info["profile"]["source"] == "guided"
    assert info["profile"]["channel_mask"] == (1 << 20)


def test_router_guided_join_parent_fallbacks_to_auto_join_mask_when_guided_trigger_fails():
    stack = _BusySteeringStack()
    router = uzigbee.Router(
        stack=stack,
        commissioning_mode="guided",
        channel=25,
        auto_join_channel_mask=(1 << 20),
        join_retry_max=1,
        join_retry_base_ms=0,
        join_retry_max_backoff_ms=0,
    ).add_light(endpoint_id=1)
    router.start(join_parent=False)
    steering_calls_before = len([call for call in stack.calls if call[0] == "start_network_steering"])

    router.join_parent()
    set_channel_calls = [call for call in stack.calls if call[0] == "set_primary_channel_mask"]
    steering_calls_after = len([call for call in stack.calls if call[0] == "start_network_steering"])

    assert ("set_primary_channel_mask", 1 << 25) in set_channel_calls
    assert ("set_primary_channel_mask", 1 << 20) in set_channel_calls
    assert steering_calls_after >= steering_calls_before + 4


def test_router_self_heal_retriggers_on_steering_failure_signal():
    stack = _FlakySteeringStack(failures_before_success=2)
    events = []
    router = uzigbee.Router(
        stack=stack,
        self_heal_enabled=True,
        self_heal_retry_max=3,
        self_heal_retry_base_ms=0,
        self_heal_retry_max_backoff_ms=0,
    ).add_light(endpoint_id=1)
    router.on_commissioning_event(lambda payload: events.append(dict(payload)))
    router.start(join_parent=False)

    stack._signal_cb(uzigbee.SIGNAL_STEERING, -1)
    info = router.network_info()
    steering_calls = [call for call in stack.calls if call[0] == "start_network_steering"]

    assert len(steering_calls) == 3
    assert info["self_heal"]["stats"]["steering_failures"] == 1
    assert info["self_heal"]["stats"]["attempts"] >= 3
    assert info["self_heal"]["stats"]["success"] >= 1
    assert len(events) >= 1
    assert any(entry["event"] == "self_heal_retry" for entry in events)


def test_router_self_heal_rejoins_after_panid_conflict_signal():
    stack = _FakeStack()
    router = uzigbee.Router(
        stack=stack,
        self_heal_enabled=True,
        self_heal_retry_max=1,
        self_heal_retry_base_ms=0,
        self_heal_retry_max_backoff_ms=0,
    ).add_light(endpoint_id=1)
    router.start(join_parent=False)
    baseline = len([call for call in stack.calls if call[0] == "start_network_steering"])

    stack._signal_cb(0x31, 0)
    info = router.network_info()
    steering_calls = [call for call in stack.calls if call[0] == "start_network_steering"]

    assert len(steering_calls) >= baseline + 1
    assert info["self_heal"]["stats"]["panid_conflicts"] == 1
    assert info["self_heal"]["stats"]["attempts"] >= 1


def test_router_commissioning_stats_tracks_join_timeout_and_conflict():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack, self_heal_enabled=False).add_light(endpoint_id=1)
    router.start(join_parent=True)
    stack._signal_cb(uzigbee.SIGNAL_STEERING, 0)
    stack._signal_cb(uzigbee.SIGNAL_STEERING, 116)
    stack._signal_cb(0x31, 0)

    stats = router.commissioning_stats()
    info = router.network_info()

    assert stats["start_count"] == 1
    assert stats["join_attempts"] >= 1
    assert stats["join_success"] >= 1
    assert stats["join_failures"] >= 1
    assert stats["timeout_events"] >= 1
    assert stats["conflict_events"] == 1
    assert "commissioning" in info
    assert info["commissioning"]["conflict_events"] == 1


def test_router_commissioning_stats_reset():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack, self_heal_enabled=False).add_light(endpoint_id=1)
    router.start(join_parent=True)
    stack._signal_cb(uzigbee.SIGNAL_STEERING, 0)
    before = router.commissioning_stats()
    router.commissioning_stats(reset=True)
    after = router.commissioning_stats()

    assert before["start_count"] == 1
    assert before["join_success"] >= 1
    assert after["start_count"] == 0
    assert after["join_success"] == 0


def test_router_on_attribute_updates_local_actuator_state():
    stack = _FakeStack()
    seen = []

    router = uzigbee.Router(stack=stack).add_power_outlet(endpoint_id=1, name="relay")
    router.on_attribute(lambda *args: seen.append(tuple(args)))
    router.start(join_parent=True)

    assert stack._attr_cb is not None
    stack._attr_cb(
        1,
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        1,
        0,
    )

    row = router.actuator_state("relay", field="on_off")
    assert row["value"] is True
    assert row["changed"] is True
    assert len(seen) == 1


def test_router_join_parent_manual_retrigger():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(endpoint_id=1).start(join_parent=True)
    baseline = len([call for call in stack.calls if call[0] == "start_network_steering"])

    router.join_parent()
    steering_calls = [call for call in stack.calls if call[0] == "start_network_steering"]

    assert len(steering_calls) == baseline + 1


def test_router_join_parent_ignores_steering_busy_error():
    stack = _BusySteeringStack()
    router = uzigbee.Router(
        stack=stack,
        join_retry_max=2,
        join_retry_base_ms=0,
        join_retry_max_backoff_ms=0,
    ).add_light(endpoint_id=1)
    router.start(join_parent=True)
    router.join_parent()

    steering_calls = [call for call in stack.calls if call[0] == "start_network_steering"]
    assert len(steering_calls) >= 6


def test_router_bind_onoff_output_with_custom_writer():
    stack = _FakeStack()
    writes = []

    router = uzigbee.Router(stack=stack).add_power_outlet(endpoint_id=1, name="relay")
    router.bind_onoff_output(actor="relay", writer=lambda state: writes.append(bool(state)), initial=False)
    router.start(join_parent=True)

    assert writes == [False]
    assert stack._attr_cb is not None
    stack._attr_cb(
        1,
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        1,
        0,
    )
    stack._attr_cb(
        1,
        uzigbee.CLUSTER_ID_ON_OFF,
        uzigbee.ATTR_ON_OFF_ON_OFF,
        0,
        0,
    )
    assert writes[-2:] == [True, False]


def test_enddevice_sleepy_status_and_manual_endpoint():
    stack = _FakeStack()
    end_device = uzigbee.EndDevice(
        stack=stack,
        sleepy=True,
        keep_alive_ms=4000,
        poll_interval_ms=1500,
    )
    end_device.add_contact_sensor(endpoint_id=10).register().start(join_parent=True)

    status = end_device.status()
    assert status["role"] == uzigbee.ROLE_END_DEVICE
    assert status["sleepy"] is True
    assert status["keep_alive_ms"] == 4000
    assert status["poll_interval_ms"] == 1500
    assert 10 in status["endpoint_ids"]
    assert ("create_contact_sensor", 10) in stack.calls


def test_router_rejects_duplicate_endpoint():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(endpoint_id=5)

    raised = False
    try:
        router.add_motion_sensor(endpoint_id=5)
    except ValueError:
        raised = True
    assert raised is True


def test_router_ias_zone_builder_passes_zone_type():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack)
    router.add_ias_zone(endpoint_id=7, zone_type=uzigbee.IAS_ZONE_TYPE_MOTION).start()

    assert ("create_ias_zone", 7, uzigbee.IAS_ZONE_TYPE_MOTION) in stack.calls


def test_router_declarative_add_and_add_all():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack)
    router.add("light").add_all(
        (
            "motion",
            {"capability": "switch", "dimmable": True, "endpoint_id": 9},
            {"capability": "power_outlet", "with_metering": True},
        )
    )
    router.register()

    assert router.endpoints() == (1, 2, 3, 9)
    assert ("create_on_off_light", 1) in stack.calls
    assert ("create_motion_sensor", 2) in stack.calls
    assert ("create_power_outlet", 3, True) in stack.calls
    assert ("create_dimmable_switch", 9) in stack.calls


def test_router_capability_aliases_and_template_options():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack)
    router.add("temperature").add("light", dimmable=True).add("ias", zone_type=uzigbee.IAS_ZONE_TYPE_MOTION)
    router.register()

    assert ("create_temperature_sensor", 1) in stack.calls
    assert ("create_dimmable_light", 2) in stack.calls
    assert ("create_ias_zone", 3, uzigbee.IAS_ZONE_TYPE_MOTION) in stack.calls
    assert "temperature_sensor" in router.capabilities()
    assert "ias_zone" in router.capabilities()


def test_router_declarative_builder_rejects_invalid_capability_and_options():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack)

    invalid_capability = False
    try:
        router.add("unknown_capability")
    except ValueError:
        invalid_capability = True
    assert invalid_capability is True

    invalid_options = False
    try:
        router.add("motion_sensor", threshold=10)
    except ValueError:
        invalid_options = True
    assert invalid_options is True


def test_router_sensor_update_pipeline_and_cache():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack)
    router.add_temperature_sensor(endpoint_id=4).add_motion_sensor(endpoint_id=5)

    row_temp = router.update("temperature", 21.75, endpoint_id=4, timestamp_ms=1111)
    row_motion = router.update("motion", True, endpoint_id=5, timestamp_ms=2222)

    assert row_temp["capability"] == "temperature"
    assert row_temp["value"] == 21.75
    assert row_temp["raw_value"] == 2175
    assert row_temp["updated_ms"] == 1111
    assert row_motion["value"] is True
    assert row_motion["raw_value"] == 1

    cached_temp = router.sensor_state("temperature", endpoint_id=4)
    cached_motion = router.sensor_state("motion_sensor", endpoint_id=5)
    assert cached_temp["raw_value"] == 2175
    assert cached_motion["value"] is True
    assert router.status()["sensor_state_count"] == 2


def test_router_climate_update_expands_to_sub_states():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_climate_sensor(endpoint_id=11)
    row = router.update("climate_sensor", {"temperature": 22.5, "humidity": 48.0}, timestamp_ms=3333)

    assert row["capability"] == "climate"
    assert row["value"]["temperature"] == 22.5
    assert row["raw_value"]["temperature"] == 2250
    assert row["updated_ms"] == 3333

    temp_row = router.sensor_state("temperature", endpoint_id=11)
    hum_row = router.sensor_state("humidity", endpoint_id=11)
    assert temp_row["value"] == 22.5
    assert hum_row["raw_value"] == 4800


def test_router_sensor_update_validation_and_ambiguity():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_temperature_sensor(endpoint_id=1).add_temperature_sensor(endpoint_id=2)

    ambiguous_update = False
    try:
        router.update("temperature", 20.0)
    except ValueError:
        ambiguous_update = True
    assert ambiguous_update is True

    invalid_value = False
    try:
        router.update("temperature", 999.0, endpoint_id=1)
    except ValueError:
        invalid_value = True
    assert invalid_value is True


def test_router_actor_on_off_level_and_idempotent_local_mirror():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(endpoint_id=3, name="main").add_switch(
        endpoint_id=4, name="dim", dimmable=True
    )

    main = router.actor("main")
    dim = router.actor("dim")

    first_on = main.on(timestamp_ms=1000)
    second_on = main.on(timestamp_ms=1100)
    first_level = dim.level(128, timestamp_ms=1200)
    second_level = dim.level(128, timestamp_ms=1300)

    assert first_on["changed"] is True
    assert second_on["changed"] is False
    assert first_level["changed"] is True
    assert second_level["changed"] is False

    on_state = router.actuator_state("main", field="on_off")
    level_state = router.actuator_state("dim", field="level")
    assert on_state["value"] is True
    assert level_state["value"] == 128
    assert router.status()["actuator_state_count"] == 2


def test_router_actor_lock_cover_and_thermostat_methods():
    stack = _FakeStack()
    router = (
        uzigbee.Router(stack=stack)
        .add_door_lock(endpoint_id=6, name="front_lock")
        .add_window_covering(endpoint_id=7, name="blind")
        .add_thermostat(endpoint_id=8, name="hvac")
    )

    lock_state = router.actor("front_lock").lock(timestamp_ms=2000)
    unlock_state = router.actor("front_lock").unlock(timestamp_ms=2100)
    cover_state = router.actor("blind").cover(55, timestamp_ms=2200)
    mode_state = router.actor("hvac").thermostat_mode("heat", timestamp_ms=2300)
    setpoint_state = router.actor("hvac").thermostat_heating_setpoint(20.5, timestamp_ms=2400)

    assert lock_state["value"] is True
    assert unlock_state["value"] is False
    assert cover_state["value"] == 55
    assert mode_state["value"] == 4
    assert setpoint_state["raw_value"] == 2050


def test_router_actor_ambiguity_and_validation_errors():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(name="l1").add_power_outlet(name="p1")

    ambiguous = False
    try:
        router.actor()
    except ValueError:
        ambiguous = True
    assert ambiguous is True

    invalid_level = False
    try:
        router.actor("l1").level(10)
    except ValueError:
        invalid_level = True
    assert invalid_level is True

    invalid_cover = False
    try:
        router.actor("l1").cover(50)
    except ValueError:
        invalid_cover = True
    assert invalid_cover is True


def test_router_reporting_policy_defaults_and_apply():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_thermostat(endpoint_id=9, name="hvac")

    configured = router.configure_reporting_policy("thermostat", dst_short_addr=0x0000, dst_endpoint=1)
    assert len(configured) == 1
    assert configured[0]["endpoint_id"] == 9
    assert len(configured[0]["entries"]) == 3

    applied = router.apply_reporting_policy(endpoint_id=9)
    assert len(applied) == 3

    reporting_calls = [call for call in stack.calls if call[0] == "configure_reporting"]
    assert len(reporting_calls) == 3
    assert reporting_calls[0][1] == 0x0000
    assert reporting_calls[0][5] == 9  # src endpoint defaults to local endpoint
    assert router.status()["reporting_policy_count"] == 1


def test_router_reporting_policy_override_replaces_entry():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_contact_sensor(endpoint_id=10, name="door")
    router.configure_reporting_policy(
        "contact",
        endpoint_id=10,
        overrides=(
            {
                "cluster_id": uzigbee.CLUSTER_ID_IAS_ZONE,
                "attr_id": uzigbee.ATTR_IAS_ZONE_STATUS,
                "attr_type": uzigbee.zcl.DATA_TYPE_16BITMAP,
                "min_interval": 2,
                "max_interval": 120,
                "reportable_change": 1,
            },
        ),
    )

    policies = router.reporting_policies()
    assert len(policies) == 1
    entry = policies[0]["entries"][0]
    assert entry[3] == 2
    assert entry[4] == 120

    router.apply_reporting_policy(endpoint_id=10)
    call = [item for item in stack.calls if item[0] == "configure_reporting"][0]
    assert call[7] == 2
    assert call[8] == 120


def test_router_binding_policy_defaults_and_apply():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_thermostat(endpoint_id=12, name="hvac")
    configured = router.configure_binding_policy(
        "thermostat",
        endpoint_id=12,
        dst_ieee_addr="11:22:33:44:55:66:77:88",
        req_dst_short_addr=0x0000,
        dst_endpoint=1,
    )

    assert len(configured) == 1
    assert configured[0]["clusters"] == (uzigbee.CLUSTER_ID_THERMOSTAT,)

    applied = router.apply_binding_policy(endpoint_id=12)
    assert len(applied) == 1
    assert applied[0]["status"] == "ok"
    assert applied[0]["bound"] == 1

    bind_calls = [call for call in stack.calls if call[0] == "send_bind_cmd"]
    assert len(bind_calls) == 1
    assert bind_calls[0][2] == uzigbee.CLUSTER_ID_THERMOSTAT
    assert bind_calls[0][5] == 12
    assert router.status()["binding_policy_count"] == 1


def test_router_binding_policy_missing_dst_ieee_is_skipped():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_switch(endpoint_id=13, name="sw")
    router.configure_binding_policy("switch", endpoint_id=13, dst_ieee_addr=None)
    applied = router.apply_binding_policy(endpoint_id=13)

    assert len(applied) == 1
    assert applied[0]["status"] == "skipped"
    assert applied[0]["reason"] == "missing_dst_ieee"

    bind_calls = [call for call in stack.calls if call[0] == "send_bind_cmd"]
    assert len(bind_calls) == 0


def test_router_binding_policy_ias_enrollment_sets_cie_address():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_ias_zone(endpoint_id=14, name="zone")
    router.configure_binding_policy(
        "ias_zone",
        endpoint_id=14,
        dst_ieee_addr=bytes.fromhex("8899aabbccddeeff"),
        req_dst_short_addr=0x0000,
    )
    applied = router.apply_binding_policy(endpoint_id=14)

    assert len(applied) == 1
    assert applied[0]["status"] == "ok"
    assert applied[0]["enroll"]["status"] == "ok"

    attr_calls = [call for call in stack.calls if call[0] == "set_attribute"]
    assert len(attr_calls) == 1
    assert attr_calls[0][1] == 14
    assert attr_calls[0][2] == uzigbee.CLUSTER_ID_IAS_ZONE
    assert attr_calls[0][3] == uzigbee.ATTR_IAS_ZONE_IAS_CIE_ADDRESS


def test_enddevice_sleepy_profile_timers():
    stack = _FakeStack()
    end_device = uzigbee.EndDevice(
        stack=stack,
        sleepy=True,
        keep_alive_ms=4000,
        poll_interval_ms=1500,
        wake_window_ms=500,
        checkin_interval_ms=20000,
    )

    end_device.mark_wake(now_ms=1000)
    end_device.mark_poll(now_ms=1000)
    end_device.mark_keepalive(now_ms=1000)

    assert end_device.wake_window_active(now_ms=1300) is True
    assert end_device.wake_window_active(now_ms=1700) is False
    assert end_device.should_poll(now_ms=2400) is False
    assert end_device.should_poll(now_ms=2600) is True
    assert end_device.should_keepalive(now_ms=4500) is False
    assert end_device.should_keepalive(now_ms=5100) is True
    assert end_device.next_poll_due_ms(now_ms=2300) == 200

    status = end_device.status()
    assert status["sleepy"] is True
    assert status["wake_window_ms"] == 500
    assert "next_poll_due_ms" in status


def test_enddevice_low_power_reporting_defaults():
    stack = _FakeStack()
    end_device = uzigbee.EndDevice(stack=stack, sleepy=True, low_power_reporting=True)
    end_device.add_contact_sensor(endpoint_id=15, name="door")

    configured = end_device.configure_reporting_policy("contact", endpoint_id=15)
    assert len(configured) == 1
    entry = configured[0]["entries"][0]
    assert entry[3] >= 30
    assert entry[4] >= 900

    end_device.apply_reporting_policy(endpoint_id=15)
    reporting_calls = [call for call in stack.calls if call[0] == "configure_reporting"]
    assert len(reporting_calls) == 1
    assert reporting_calls[0][7] >= 30
    assert reporting_calls[0][8] >= 900


def test_node_state_persistence_roundtrip():
    stack_a = _FakeStack()
    router_a = uzigbee.Router(stack=stack_a).add_light(endpoint_id=1, name="light").add_contact_sensor(
        endpoint_id=5, name="door"
    )
    router_a.update("contact", True, endpoint_id=5, timestamp_ms=1234)
    router_a.actor("light").on(timestamp_ms=2345)
    router_a.configure_reporting_policy("contact", endpoint_id=5)
    router_a.configure_binding_policy("contact", endpoint_id=5, dst_ieee_addr="11:22:33:44:55:66:77:88")
    router_a.configure_persistence(min_interval_ms=10)

    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "node_state.json"
        saved = router_a.save_node_state(path=str(state_path), force=True)
        assert saved["saved"] is True

        stack_b = _FakeStack()
        router_b = uzigbee.Router(stack=stack_b)
        loaded = router_b.load_node_state(path=str(state_path), merge=False)
        assert loaded["loaded"] is True

        assert router_b.endpoints() == (1, 5)
        assert router_b.commissioning_mode == "auto"
        assert router_b.sensor_state("contact", endpoint_id=5)["value"] is True
        assert router_b.actuator_state("light", field="on_off")["value"] is True
        assert len(router_b.reporting_policies()) == 1
        assert len(router_b.binding_policies()) == 1
        expected_mask = 0
        for channel in range(11, 27):
            expected_mask |= (1 << channel)
        assert router_b.status()["auto_join"]["channel_mask"] == expected_mask


def test_node_state_restore_restores_commissioning_profile():
    stack_a = _FakeStack()
    router_a = uzigbee.Router(
        stack=stack_a,
        channel=15,
        pan_id=0x1A62,
        extended_pan_id="00124b0001c6c6c6",
    ).add_light(endpoint_id=1, name="light")
    router_a.configure_auto_join(
        auto_join_channel_mask=(1 << 11) | (1 << 15),
        join_retry_max=2,
        join_retry_base_ms=0,
        join_retry_max_backoff_ms=0,
    )
    router_a.configure_self_heal(
        enabled=True,
        retry_max=3,
        retry_base_ms=25,
        retry_max_backoff_ms=200,
    )
    snapshot = router_a.dump_node_state()

    stack_b = _FakeStack()
    router_b = uzigbee.Router(stack=stack_b)
    restored = router_b.restore_node_state(snapshot, merge=False)
    info = router_b.network_info()

    assert restored["components"] == 1
    assert router_b.commissioning_mode == "fixed"
    assert info["profile"]["source"] == "fixed"
    assert info["profile"]["channel_mask"] == (1 << 15)
    assert info["profile"]["pan_id"] == 0x1A62
    assert info["profile"]["extended_pan_id"] == "00124b0001c6c6c6"
    assert info["auto_join"]["channel_mask"] == ((1 << 11) | (1 << 15))
    assert info["auto_join"]["join_retry_max"] == 2
    assert info["auto_join"]["join_retry_base_ms"] == 0
    assert info["auto_join"]["join_retry_max_backoff_ms"] == 0
    assert info["self_heal"]["policy"]["enabled"] is True
    assert info["self_heal"]["policy"]["retry_max"] == 3
    assert info["self_heal"]["policy"]["retry_base_ms"] == 25
    assert info["self_heal"]["policy"]["retry_max_backoff_ms"] == 200


def test_node_state_persistence_throttle():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_switch(endpoint_id=2, name="sw")
    router.configure_persistence(min_interval_ms=60000)

    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "node_state.json"
        first = router.save_node_state(path=str(state_path), force=True)
        second = router.save_node_state(path=str(state_path), force=False)

    assert first["saved"] is True
    assert second["saved"] is False
    assert second["reason"] == "throttled"


def test_router_custom_capability_template_and_alias():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack)
    router.register_capability(
        name="air_quality_sensor",
        create_method="create_air_quality_sensor",
        aliases=("aqi",),
    )
    router.add("aqi", endpoint_id=21, name="aqi").register()

    assert ("create_air_quality_sensor", 21) in stack.calls
    custom = router.custom_capabilities()
    assert len(custom) == 1
    assert custom[0]["name"] == "air_quality_sensor"
    assert "aqi" in custom[0]["aliases"]


def test_router_policy_hooks_receive_events():
    stack = _FakeStack()
    router = uzigbee.Router(stack=stack).add_light(endpoint_id=1, name="light").add_contact_sensor(
        endpoint_id=5, name="door"
    )
    seen = []
    router.register_policy_hook("collector", lambda event, payload: seen.append((event, payload.get("endpoint_id"))))

    router.actor("light").on(timestamp_ms=100)
    router.update("contact", True, endpoint_id=5, timestamp_ms=200)
    router.configure_reporting_policy("contact", endpoint_id=5)
    router.configure_binding_policy("contact", endpoint_id=5, dst_ieee_addr="11:22:33:44:55:66:77:88")
    router.apply_binding_policy(endpoint_id=5)

    event_names = tuple(row[0] for row in seen)
    assert "actuator_update" in event_names
    assert "sensor_update" in event_names
    assert "reporting_configured" in event_names
    assert "binding_configured" in event_names
    assert "binding_applied" in event_names
