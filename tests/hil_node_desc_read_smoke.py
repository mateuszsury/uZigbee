"""HIL smoke for ZDO Node Descriptor request + snapshot API."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.DimmableSwitch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_node_desc_smoke",
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
z.request_node_descriptor(short_addr)

snapshot = None
deadline = time.ticks_add(time.ticks_ms(), 5000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    snapshot = z.get_node_descriptor_snapshot()
    if snapshot is not None:
        break
    time.sleep_ms(200)

print("uzigbee.hil.node_desc.short_addr", hex(short_addr))
print("uzigbee.hil.node_desc.snapshot", snapshot)

assert snapshot is not None
assert isinstance(snapshot["status"], int)
assert isinstance(snapshot["addr"], int)
if snapshot["node_desc"] is not None:
    assert isinstance(snapshot["node_desc"]["manufacturer_code"], int)
    assert isinstance(snapshot["node_desc"]["mac_capability_flags"], int)

print("uzigbee.hil.node_desc.result PASS")
