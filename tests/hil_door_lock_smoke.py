"""HIL smoke for high-level uzigbee.DoorLock wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

lock = uzigbee.DoorLock(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_door_lock_01",
    sw_build_id="step23",
)

try:
    lock.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

lock.lock()
state_locked = lock.get_lock_state()
is_locked = lock.locked
lock.unlock()
state_unlocked = lock.get_lock_state()

stats = z.event_stats()
print("uzigbee.hil.door_lock.state_locked", state_locked)
print("uzigbee.hil.door_lock.state_unlocked", state_unlocked)
print("uzigbee.hil.door_lock.is_locked", is_locked)
print("uzigbee.hil.door_lock.stats", stats)
assert isinstance(state_locked, int)
assert isinstance(state_unlocked, int)
assert isinstance(is_locked, bool)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.door_lock.result PASS")
