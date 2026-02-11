"""HIL smoke for Basic cluster identity configuration on ESP32-C6."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259
TARGET_POWER = uzigbee.BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE
identity_set = False

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)
try:
    z.create_on_off_light(1)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    z.set_basic_identity(
        endpoint_id=1,
        manufacturer="uzigbee",
        model="uzb_light_01",
        date_code="20260206",
        sw_build_id="step9",
        power_source=TARGET_POWER,
    )
    identity_set = True
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

deadline = time.ticks_add(time.ticks_ms(), 2000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    time.sleep_ms(100)

power_source = z.get_attribute(1, uzigbee.CLUSTER_ID_BASIC, uzigbee.ATTR_BASIC_POWER_SOURCE, uzigbee.CLUSTER_ROLE_SERVER)
stats = z.event_stats()
print("uzigbee.hil.basic.power_source", power_source, "identity_set", identity_set)
print("uzigbee.hil.basic.stats", stats)
assert isinstance(power_source, int)
if identity_set:
    assert power_source == TARGET_POWER
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.basic.result PASS")
