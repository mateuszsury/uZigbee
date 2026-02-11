"""HIL smoke for high-level uzigbee.HumiditySensor wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

sensor = uzigbee.HumiditySensor(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_humidity_sensor_01",
    sw_build_id="step19",
)

try:
    sensor.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

sensor.set_humidity_percent(56.78)
raw = sensor.get_humidity_raw()
percent = sensor.get_humidity_percent()

stats = z.event_stats()
print("uzigbee.hil.humidity.raw", raw)
print("uzigbee.hil.humidity.percent", percent)
print("uzigbee.hil.humidity.stats", stats)
assert isinstance(raw, int)
assert percent is None or isinstance(percent, float)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.humidity.result PASS")
