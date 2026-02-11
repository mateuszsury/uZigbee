"""HIL smoke for z2m setter helpers on ESP32-C6."""

import time

import uzigbee
from uzigbee import z2m


ESP_ERR_INVALID_STATE = 259
set_ok = False

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)
try:
    z.create_on_off_light(1)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z2m.set_model_id("uzb_light_step11", endpoint_id=1)
    z2m.set_manufacturer("uzigbee", endpoint_id=1)
    z2m.set_identity(endpoint_id=1, date_code="20260206", sw_build_id="step11")
    set_ok = True
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

attrs = z2m.get_interview_attrs(endpoint_id=1)
report = z2m.validate(endpoint_id=1)
stats = z.event_stats()
print("uzigbee.hil.z2mset.ok", report["ok"], "set_ok", set_ok)
print("uzigbee.hil.z2mset.attrs", attrs)
print("uzigbee.hil.z2mset.stats", stats)

if set_ok:
    assert attrs["manufacturer_name"] == "uzigbee"
    assert attrs["model_identifier"] == "uzb_light_step11"
    assert attrs["date_code"] == "20260206"
    assert attrs["sw_build_id"] == "step11"
assert report["ok"] is True
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.z2mset.result PASS")
