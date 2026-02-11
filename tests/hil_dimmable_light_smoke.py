"""HIL smoke for high-level uzigbee.DimmableLight wrapper on ESP32-C6."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259
brightness_events = []


def _on_brightness(level):
    brightness_events.append(int(level))


z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

light = uzigbee.DimmableLight(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_dimmable_light_01",
    sw_build_id="step14",
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

light.on_brightness_change(_on_brightness)
time.sleep_ms(300)

a = light.set_brightness(180)
time.sleep_ms(150)
b = light.get_brightness()
c = light.set_brightness(12)
time.sleep_ms(150)
d = light.get_brightness()

stats = z.event_stats()
print("uzigbee.hil.dimmable.levels", a, b, c, d)
print("uzigbee.hil.dimmable.events", brightness_events)
print("uzigbee.hil.dimmable.stats", stats)
assert isinstance(b, int)
assert isinstance(d, int)
assert b == a
assert d == c
assert any(v == 180 for v in brightness_events)
assert any(v == 12 for v in brightness_events)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.dimmable.result PASS")
