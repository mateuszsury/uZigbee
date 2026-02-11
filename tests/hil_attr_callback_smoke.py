"""HIL smoke for attribute callback bridge on ESP32-C6."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259
attr_events = []


def _attr_cb(endpoint, cluster_id, attr_id, value, attr_type, status):
    attr_events.append((endpoint, cluster_id, attr_id, value, attr_type, status))


z = uzigbee.ZigbeeStack()
z.on_attribute(_attr_cb)
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

time.sleep_ms(300)
z.set_attribute(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF, 1, uzigbee.CLUSTER_ROLE_SERVER, False)
z.set_attribute(1, uzigbee.CLUSTER_ID_ON_OFF, uzigbee.ATTR_ON_OFF_ON_OFF, 0, uzigbee.CLUSTER_ROLE_SERVER, False)
time.sleep_ms(300)

target = []
for event in attr_events:
    endpoint, cluster_id, attr_id, value, _attr_type, status = event
    if endpoint == 1 and cluster_id == uzigbee.CLUSTER_ID_ON_OFF and attr_id == uzigbee.ATTR_ON_OFF_ON_OFF and status == 0:
        target.append(value)

stats = z.event_stats()
print("uzigbee.hil.attrcb.events", len(attr_events), len(target))
if target:
    print("uzigbee.hil.attrcb.values", target[0], target[-1])
print("uzigbee.hil.attrcb.stats", stats)

assert any(v is True for v in target)
assert any(v is False for v in target)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.attrcb.result PASS")
