"""HIL smoke for high-level uzigbee.DoorLockController wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

controller = uzigbee.DoorLockController(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_door_lock_controller_01",
    sw_build_id="step23",
)

try:
    controller.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

short_addr = z.get_short_addr()
controller.send_lock(short_addr, 1)
controller.send_unlock(short_addr, 1)
stats = z.event_stats()

print("uzigbee.hil.door_lock_controller.short_addr", hex(short_addr))
print("uzigbee.hil.door_lock_controller.stats", stats)
assert isinstance(short_addr, int)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.door_lock_controller.result PASS")
