"""HIL smoke for high-level uzigbee.PressureSensor wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

sensor = uzigbee.PressureSensor(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_pressure_sensor_01",
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

sensor.set_pressure_hpa(1008.6)
raw = sensor.get_pressure_raw()
hpa = sensor.get_pressure_hpa()

stats = z.event_stats()
print("uzigbee.hil.pressure.raw", raw)
print("uzigbee.hil.pressure.hpa", hpa)
print("uzigbee.hil.pressure.stats", stats)
assert isinstance(raw, int)
assert hpa is None or isinstance(hpa, float)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.pressure.result PASS")
