"""HIL smoke for local configure_reporting command path."""

import uzigbee


ESP_ERR_INVALID_STATE = 259
ATTR_TYPE_S16 = 0x29

z = uzigbee.ZigbeeStack()
print("uzigbee.hil.reporting.step init")
z.init(uzigbee.ROLE_COORDINATOR)

try:
    print("uzigbee.hil.reporting.step create_temperature_sensor")
    z.create_temperature_sensor(1)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    print("uzigbee.hil.reporting.step register_device")
    z.register_device()
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    print("uzigbee.hil.reporting.step start")
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

print("uzigbee.hil.reporting.step get_short_addr")
dst = z.get_short_addr()
print("uzigbee.hil.reporting.step configure_with_change")
z.configure_reporting(
    src_endpoint=1,
    dst_short_addr=dst,
    dst_endpoint=1,
    cluster_id=uzigbee.CLUSTER_ID_TEMP_MEASUREMENT,
    attr_id=uzigbee.ATTR_TEMP_MEASUREMENT_VALUE,
    attr_type=ATTR_TYPE_S16,
    min_interval=10,
    max_interval=300,
    reportable_change=50,
)
print("uzigbee.hil.reporting.step configure_without_change")
z.configure_reporting(
    src_endpoint=1,
    dst_short_addr=dst,
    dst_endpoint=1,
    cluster_id=uzigbee.CLUSTER_ID_TEMP_MEASUREMENT,
    attr_id=uzigbee.ATTR_TEMP_MEASUREMENT_VALUE,
    attr_type=ATTR_TYPE_S16,
    min_interval=1,
    max_interval=300,
    reportable_change=None,
)

stats = z.event_stats()
print("uzigbee.hil.reporting.dst", hex(dst))
print("uzigbee.hil.reporting.stats", stats)
assert isinstance(dst, int)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.reporting.result PASS")
