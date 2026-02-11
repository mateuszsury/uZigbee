"""HIL smoke for Router high-level node API (Phase 4.6)."""

import sys

if "/remote/python" not in sys.path:
    sys.path.insert(0, "/remote/python")

import uzigbee


ESP_ERR_INVALID_STATE = 259

stack = uzigbee.ZigbeeStack()
stack.init(uzigbee.ROLE_COORDINATOR)
try:
    stack.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

router = (
    uzigbee.Router(stack=stack, auto_register=False)
    .add_light(endpoint_id=1, name="light_main")
    .add_switch(endpoint_id=2, name="switch_main", dimmable=True)
    .add_contact_sensor(endpoint_id=3, name="door_main")
)

on_row = router.actor("light_main").on()
level_row = router.actor("switch_main").level(123)
sensor_row = router.update("contact", True, endpoint_id=3)
status = router.status()
stack_stats = stack.event_stats()

rejoin_guard = True
try:
    stack.start(form_network=False)
except OSError as exc:
    rejoin_guard = False
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

print("uzigbee.hil.node.router.endpoints", router.endpoints())
print("uzigbee.hil.node.router.on_row", on_row)
print("uzigbee.hil.node.router.level_row", level_row)
print("uzigbee.hil.node.router.sensor_row", sensor_row)
print("uzigbee.hil.node.router.status", status)
print("uzigbee.hil.node.router.rejoin_guard", rejoin_guard)
print("uzigbee.hil.node.router.stats", stack_stats)

assert router.endpoints() == (1, 2, 3)
assert on_row["value"] is True
assert level_row["value"] == 123
assert sensor_row["value"] is True
assert status["actuator_state_count"] >= 2
assert status["sensor_state_count"] >= 1
assert stack_stats["dropped_queue_full"] == 0
assert stack_stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.node.router.result PASS")
