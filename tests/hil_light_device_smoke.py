"""HIL smoke for high-level uzigbee.Light wrapper on ESP32-C6."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259
events = []


def _on_change(state):
    events.append(bool(state))


z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

light = uzigbee.Light(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_light_01",
    sw_build_id="step13",
)

try:
    light.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

light.on_change(_on_change)
time.sleep_ms(300)
light.set_state(True)
time.sleep_ms(150)
state_a = light.get_state()
light.toggle()
time.sleep_ms(150)
state_b = light.get_state()

stats = z.event_stats()
print("uzigbee.hil.light.states", state_a, state_b)
print("uzigbee.hil.light.events", events)
print("uzigbee.hil.light.stats", stats)
assert isinstance(state_a, bool)
assert isinstance(state_b, bool)
assert any(v is True for v in events)
assert any(v is False for v in events)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.light.result PASS")
