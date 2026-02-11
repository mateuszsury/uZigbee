import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

import uzigbee


class _MatrixStack:
    def __init__(self):
        self.calls = []
        self._signal_cb = None

    def init(self, role):
        self.calls.append(("init", int(role)))

    def on_signal(self, callback=None):
        self.calls.append(("on_signal", callback is not None))
        self._signal_cb = callback

    def register_device(self):
        self.calls.append(("register_device",))

    def start(self, form_network=False):
        self.calls.append(("start", bool(form_network)))

    def create_on_off_light(self, endpoint_id=1):
        self.calls.append(("create_on_off_light", int(endpoint_id)))

    def create_dimmable_switch(self, endpoint_id=1):
        self.calls.append(("create_dimmable_switch", int(endpoint_id)))

    def create_contact_sensor(self, endpoint_id=1):
        self.calls.append(("create_contact_sensor", int(endpoint_id)))

    def create_motion_sensor(self, endpoint_id=1):
        self.calls.append(("create_motion_sensor", int(endpoint_id)))

    def create_thermostat(self, endpoint_id=1):
        self.calls.append(("create_thermostat", int(endpoint_id)))

    def create_window_covering(self, endpoint_id=1):
        self.calls.append(("create_window_covering", int(endpoint_id)))

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


@pytest.mark.parametrize(
    "definitions, expected_calls",
    (
        (
            ("light", {"capability": "switch", "dimmable": True, "endpoint_id": 7}),
            (("create_on_off_light", 1), ("create_dimmable_switch", 7)),
        ),
        (
            ({"capability": "contact", "endpoint_id": 2}, {"capability": "motion", "endpoint_id": 3}),
            (("create_contact_sensor", 2), ("create_motion_sensor", 3)),
        ),
    ),
)
def test_node_matrix_builder_variants(definitions, expected_calls):
    stack = _MatrixStack()
    router = uzigbee.Router(stack=stack).add_all(definitions).register()

    for expected_call in expected_calls:
        assert expected_call in stack.calls
    assert len(router.components()) == len(expected_calls)


@pytest.mark.parametrize(
    "builder_call, action_name, action_value, expect_actor_missing",
    (
        ("add_contact_sensor", "on", None, True),
        ("add_thermostat", "cover", 20, False),
        ("add_window_covering", "lock", None, False),
    ),
)
def test_node_matrix_actor_profile_conflicts(builder_call, action_name, action_value, expect_actor_missing):
    stack = _MatrixStack()
    router = uzigbee.Router(stack=stack)
    getattr(router, builder_call)(endpoint_id=11, name="actor")

    if expect_actor_missing:
        with pytest.raises(ValueError):
            router.actor("actor")
        return

    actor = router.actor("actor")
    with pytest.raises(ValueError):
        if action_value is None:
            getattr(actor, action_name)()
        else:
            getattr(actor, action_name)(action_value)


def test_node_matrix_state_and_reporting_edge_cases():
    stack = _MatrixStack()
    router = uzigbee.Router(stack=stack).add_contact_sensor(endpoint_id=3, name="door")

    with pytest.raises(ValueError):
        router.update("temperature", 22.0, endpoint_id=3)

    router.update("contact", True, endpoint_id=3)
    assert router.sensor_state("contact", endpoint_id=3)["raw_value"] == 1

    with pytest.raises(ValueError):
        router.configure_reporting_policy("unknown_capability")

    configured = router.configure_reporting_policy(
        "contact",
        endpoint_id=3,
        overrides=(
            {
                "cluster_id": uzigbee.CLUSTER_ID_IAS_ZONE,
                "attr_id": uzigbee.ATTR_IAS_ZONE_STATUS,
                "attr_type": uzigbee.zcl.DATA_TYPE_16BITMAP,
                "min_interval": 5,
                "max_interval": 30,
                "reportable_change": 1,
            },
        ),
    )
    assert configured[0]["entries"][0][3] == 5
    assert configured[0]["entries"][0][4] == 30


def test_node_matrix_binding_edge_cases_and_overrides():
    stack = _MatrixStack()
    router = uzigbee.Router(stack=stack).add_ias_zone(endpoint_id=9, name="zone")
    router.configure_binding_policy("ias_zone", endpoint_id=9, dst_ieee_addr=None)

    skipped = router.apply_binding_policy(endpoint_id=9)
    assert skipped[0]["status"] == "skipped"
    assert skipped[0]["reason"] == "missing_dst_ieee"

    applied = router.apply_binding_policy(endpoint_id=9, dst_ieee_addr="11:22:33:44:55:66:77:88")
    assert applied[0]["status"] in ("ok", "partial")
    bind_calls = [call for call in stack.calls if call[0] == "send_bind_cmd"]
    assert len(bind_calls) >= 1
    assert bind_calls[-1][3] == bytes.fromhex("1122334455667788")


def test_node_matrix_enddevice_sleepy_conflict_resolution():
    stack = _MatrixStack()
    end_device = uzigbee.EndDevice(
        stack=stack,
        sleepy=True,
        keep_alive_ms=3000,
        poll_interval_ms=1000,
        wake_window_ms=400,
        low_power_reporting=True,
    ).add_contact_sensor(endpoint_id=4)

    end_device.mark_wake(now_ms=1000)
    assert end_device.wake_window_active(now_ms=1300) is True
    assert end_device.wake_window_active(now_ms=1600) is False

    end_device.configure_sleepy_profile(sleepy=False)
    assert end_device.should_poll(now_ms=2000) is False
    assert end_device.should_keepalive(now_ms=2000) is False
    assert end_device.wake_window_active(now_ms=999999) is True


def test_node_matrix_integration_router_enddevice_roundtrip_and_hooks():
    stack_a = _MatrixStack()
    events = []
    router = (
        uzigbee.Router(stack=stack_a)
        .add_light(endpoint_id=1, name="light")
        .add_contact_sensor(endpoint_id=2, name="door")
    )
    router.register_policy_hook("collector", lambda event, payload: events.append((event, payload.get("endpoint_id"))))
    router.update("contact", False, endpoint_id=2, timestamp_ms=100)
    router.actor("light").on(timestamp_ms=120)
    router.configure_reporting_policy("contact", endpoint_id=2)
    router.configure_binding_policy("contact", endpoint_id=2, dst_ieee_addr="11:22:33:44:55:66:77:88")

    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "matrix_state.json"
        save = router.save_node_state(path=str(state_path), force=True)
        assert save["saved"] is True

        stack_b = _MatrixStack()
        end_device = uzigbee.EndDevice(stack=stack_b, sleepy=True)
        load = end_device.load_node_state(path=str(state_path), merge=False)
        assert load["loaded"] is True
        assert end_device.sensor_state("contact", endpoint_id=2)["value"] is False
        assert end_device.actuator_state("light", field="on_off")["value"] is True
        assert len(end_device.reporting_policies()) == 1
        assert len(end_device.binding_policies()) == 1

    event_names = tuple(item[0] for item in events)
    assert "sensor_update" in event_names
    assert "actuator_update" in event_names
    assert "reporting_configured" in event_names
    assert "binding_configured" in event_names
