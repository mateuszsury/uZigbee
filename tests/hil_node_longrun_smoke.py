"""HIL long-run smoke for local node API stability (Phase 4.6)."""

import gc
import sys
import time

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
    .add_light(endpoint_id=1, name="lr_light")
    .add_contact_sensor(endpoint_id=2, name="lr_contact")
    .add_motion_sensor(endpoint_id=3, name="lr_motion")
)

loops = 120
for idx in range(loops):
    if idx % 2 == 0:
        router.actor("lr_light").on()
        router.update("contact", True, endpoint_id=2)
        router.update("motion", False, endpoint_id=3)
    else:
        router.actor("lr_light").off()
        router.update("contact", False, endpoint_id=2)
        router.update("motion", True, endpoint_id=3)
    if idx % 20 == 0:
        gc.collect()
    time.sleep(0.1)

status = router.status()
sensor_states = router.sensor_states()
actuator_states = router.actuator_states()
stack_stats = stack.event_stats()

print("uzigbee.hil.node.longrun.loops", loops)
print("uzigbee.hil.node.longrun.status", status)
print("uzigbee.hil.node.longrun.sensor_states", sensor_states)
print("uzigbee.hil.node.longrun.actuator_states", actuator_states)
print("uzigbee.hil.node.longrun.stats", stack_stats)

assert status["sensor_state_count"] >= 2
assert status["actuator_state_count"] >= 1
assert len(sensor_states) >= 2
assert len(actuator_states) >= 1
assert stack_stats["dropped_queue_full"] == 0
assert stack_stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.node.longrun.result PASS")
