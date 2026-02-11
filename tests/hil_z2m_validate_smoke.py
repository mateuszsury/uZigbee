"""HIL smoke for z2m interview helpers on ESP32-C6."""

import time

import uzigbee
from uzigbee import z2m


ESP_ERR_INVALID_STATE = 259
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
        sw_build_id="step10",
        power_source=uzigbee.BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
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

deadline = time.ticks_add(time.ticks_ms(), 1500)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    time.sleep_ms(100)

report = z2m.validate(endpoint_id=1)
stats = z.event_stats()
print("uzigbee.hil.z2m.ok", report["ok"], "identity_set", identity_set)
print("uzigbee.hil.z2m.errors", report["errors"])
print("uzigbee.hil.z2m.warnings", report["warnings"])
print("uzigbee.hil.z2m.attrs", report["attrs"])
print("uzigbee.hil.z2m.stats", stats)

if identity_set:
    assert report["ok"] is True
    assert report["attrs"]["manufacturer_name"] == "uzigbee"
    assert report["attrs"]["model_identifier"] == "uzb_light_01"
    assert report["attrs"]["power_source"] == uzigbee.BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE
else:
    assert "attrs" in report
    assert isinstance(report["errors"], list)

assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.z2m.result PASS")
