"""HIL smoke for local get/set attribute path."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259
events = []


def _cb(signal_id, status):
    events.append((signal_id, status))


z = uzigbee.ZigbeeStack()
z.on_signal(_cb)
z.init(uzigbee.ROLE_COORDINATOR)
try:
    z.create_on_off_light(1)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    z.register_device()
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

deadline = time.ticks_add(time.ticks_ms(), 3000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    time.sleep_ms(100)

v0 = z.get_attribute(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF, uzigbee.CLUSTER_ROLE_SERVER)
z.set_attribute(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF, 1, uzigbee.CLUSTER_ROLE_SERVER, False)
v1 = z.get_attribute(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF, uzigbee.CLUSTER_ROLE_SERVER)
z.set_attribute(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF, 0, uzigbee.CLUSTER_ROLE_SERVER, False)
v2 = z.get_attribute(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF, uzigbee.CLUSTER_ROLE_SERVER)

stats = z.event_stats()
print("uzigbee.hil.attr.values", v0, v1, v2)
print("uzigbee.hil.attr.stats", stats)
assert isinstance(v0, bool)
assert v1 is True
assert v2 is False
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.attr.result PASS")
