"""HIL smoke for high-level uzigbee.MotionSensor wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

sensor = uzigbee.MotionSensor(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_motion_sensor_01",
    sw_build_id="step25",
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

sensor.set_motion(True)
motion_true = sensor.get_motion()
sensor.set_motion(False)
motion_false = sensor.get_motion()
zone_status = sensor.get_zone_status()
zone_type = sensor.get_zone_type()
stats = z.event_stats()

print("uzigbee.hil.motion.true", motion_true)
print("uzigbee.hil.motion.false", motion_false)
print("uzigbee.hil.motion.zone_status", zone_status)
print("uzigbee.hil.motion.zone_type", hex(zone_type))
print("uzigbee.hil.motion.stats", stats)
assert isinstance(motion_true, bool)
assert isinstance(motion_false, bool)
assert isinstance(zone_status, int)
assert zone_type == uzigbee.IAS_ZONE_TYPE_MOTION
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.motion.result PASS")
