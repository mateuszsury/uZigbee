"""HIL smoke for high-level uzigbee.OccupancySensor wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

sensor = uzigbee.OccupancySensor(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_occupancy_sensor_01",
    sw_build_id="step23",
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

sensor.set_occupied(True)
state_true = sensor.get_occupied()
sensor.set_occupied(False)
state_false = sensor.get_occupied()
stats = z.event_stats()

print("uzigbee.hil.occupancy.true", state_true)
print("uzigbee.hil.occupancy.false", state_false)
print("uzigbee.hil.occupancy.stats", stats)
assert isinstance(state_true, bool)
assert isinstance(state_false, bool)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.occupancy.result PASS")
