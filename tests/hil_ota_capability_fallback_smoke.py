"""HIL smoke for OTA capability-based fallback helpers."""

import uzigbee
from uzigbee import ota


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

light = uzigbee.Light(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_ota_capability_01",
    sw_build_id="step48",
)

try:
    light.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

supported = ota.is_control_supported(z)
set_ok = ota.set_query_interval_if_supported(z, endpoint_id=1, interval_min=5)
query_ok = ota.query_image_if_supported(z, server_ep=1, server_addr=0x00)
stop_ok = ota.stop_query_if_supported(z)
stats = z.event_stats()

print("uzigbee.hil.ota.capability.supported", supported)
print("uzigbee.hil.ota.capability.set_ok", set_ok)
print("uzigbee.hil.ota.capability.query_ok", query_ok)
print("uzigbee.hil.ota.capability.stop_ok", stop_ok)
print("uzigbee.hil.ota.capability.stats", stats)

assert bool(set_ok) is bool(supported)
assert bool(query_ok) is bool(supported)
assert bool(stop_ok) is bool(supported)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0

print("uzigbee.hil.ota.capability.result PASS")
