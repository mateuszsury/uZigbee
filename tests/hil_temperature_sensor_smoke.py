"""HIL smoke for high-level uzigbee.TemperatureSensor wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

sensor = uzigbee.TemperatureSensor(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_temperature_sensor_01",
    sw_build_id="step18",
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

sensor.set_temperature_c(23.45)
raw = sensor.get_temperature_raw()
celsius = sensor.get_temperature_c()

stats = z.event_stats()
print("uzigbee.hil.temp.raw", raw)
print("uzigbee.hil.temp.c", celsius)
print("uzigbee.hil.temp.stats", stats)
assert isinstance(raw, int)
assert celsius is None or isinstance(celsius, float)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.temp.result PASS")
