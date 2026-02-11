"""HIL smoke for last joined short address API."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

try:
    z.start(form_network=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

time.sleep(2)

last_joined = z.get_last_joined_short_addr()
print("uzigbee.hil.last_joined_short", last_joined)

if last_joined is not None:
    assert isinstance(last_joined, int)
    assert 0 <= last_joined <= 0xFFFF
    assert last_joined != 0xFFFF

print("uzigbee.hil.last_joined.result PASS")
