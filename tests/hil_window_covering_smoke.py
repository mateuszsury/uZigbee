"""HIL smoke for high-level uzigbee.WindowCovering wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

cover = uzigbee.WindowCovering(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_window_covering_01",
    sw_build_id="step26",
)

try:
    cover.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

cover.set_lift_percentage(25)
cover.set_tilt_percentage(70)
lift = cover.get_lift_percentage()
tilt = cover.get_tilt_percentage()
position = cover.position
stats = z.event_stats()

print("uzigbee.hil.window_covering.lift", lift)
print("uzigbee.hil.window_covering.tilt", tilt)
print("uzigbee.hil.window_covering.position", position)
print("uzigbee.hil.window_covering.stats", stats)
assert lift == 25
assert tilt == 70
assert position == 25
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.window_covering.result PASS")
