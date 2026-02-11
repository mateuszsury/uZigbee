"""HIL smoke for high-level uzigbee.ClimateSensor wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

sensor = uzigbee.ClimateSensor(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_climate_sensor_01",
    sw_build_id="step20",
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

sensor.set_temperature_c(24.11)
sensor.set_humidity_percent(51.23)
sensor.set_pressure_hpa(1004.2)
t = sensor.get_temperature_c()
h = sensor.get_humidity_percent()
p = sensor.get_pressure_hpa()

stats = z.event_stats()
print("uzigbee.hil.climate.t", t)
print("uzigbee.hil.climate.h", h)
print("uzigbee.hil.climate.p", p)
print("uzigbee.hil.climate.stats", stats)
assert t is None or isinstance(t, float)
assert h is None or isinstance(h, float)
assert p is None or isinstance(p, float)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.climate.result PASS")
