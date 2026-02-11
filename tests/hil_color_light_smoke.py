"""HIL smoke for high-level uzigbee.ColorLight wrapper on ESP32-C6."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259
temp_events = []
xy_events = []


def _on_temp(value):
    temp_events.append(int(value))


def _on_xy(value):
    xy_events.append((int(value[0]), int(value[1])))


z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

light = uzigbee.ColorLight(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_color_light_01",
    sw_build_id="step15",
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

light.on_color_temperature_change(_on_temp)
light.on_xy_change(_on_xy)
time.sleep_ms(300)

temp_supported = True
t1 = None
t2 = None
try:
    t1 = light.set_color_temperature(180)
    time.sleep_ms(100)
    t2 = light.get_color_temperature()
except OSError:
    temp_supported = False

xy1 = light.set_xy(11000, 22000)
time.sleep_ms(100)
xy2 = light.get_xy()

stats = z.event_stats()
print("uzigbee.hil.color.temp", t1, t2)
print("uzigbee.hil.color.temp_supported", temp_supported)
print("uzigbee.hil.color.xy", xy1, xy2)
print("uzigbee.hil.color.temp_events", temp_events)
print("uzigbee.hil.color.xy_events", xy_events)
print("uzigbee.hil.color.stats", stats)
if temp_supported:
    assert isinstance(t2, int)
    assert t1 == t2
    assert any(v == 180 for v in temp_events)
assert isinstance(xy2, tuple)
assert xy2 == xy1
assert any(v == (11000, 22000) for v in xy_events)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.color.result PASS")
