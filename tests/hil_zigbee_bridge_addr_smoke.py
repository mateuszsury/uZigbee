"""HIL smoke for Zigbee bridge runtime + IEEE/short address readback."""

import ubinascii
import uzigbee
import time


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

time.sleep(1)

ieee_api = z.get_ieee_addr()
short_api = z.get_short_addr()
stats = z.event_stats()

print("uzigbee.hil.bridge.ieee_api", ubinascii.hexlify(ieee_api).decode())
print("uzigbee.hil.bridge.short_api", hex(short_api))
print("uzigbee.hil.bridge.stats", stats)
assert isinstance(ieee_api, (bytes, bytearray)) and len(ieee_api) == 8
assert isinstance(short_api, int)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.bridge.result PASS")
