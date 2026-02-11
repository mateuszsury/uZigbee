"""HIL smoke for ZDO Active Endpoint request + snapshot API."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.DimmableSwitch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_active_ep_smoke",
    sw_build_id="demo",
)

try:
    switch.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

time.sleep(1)
short_addr = int(z.get_short_addr())
z.request_active_endpoints(short_addr)

snapshot = None
deadline = time.ticks_add(time.ticks_ms(), 5000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    snapshot = z.get_active_endpoints_snapshot()
    if snapshot is not None:
        break
    time.sleep_ms(200)

print("uzigbee.hil.active_ep.short_addr", hex(short_addr))
print("uzigbee.hil.active_ep.snapshot", snapshot)

assert snapshot is not None
assert isinstance(snapshot["status"], int)
assert isinstance(snapshot["count"], int)
assert isinstance(snapshot["endpoints"], list)

print("uzigbee.hil.active_ep.result PASS")
