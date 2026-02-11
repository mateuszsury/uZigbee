"""HIL smoke for composed ZDO descriptor discovery helper."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.DimmableSwitch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_discover_desc_smoke",
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
result = z.discover_node_descriptors(
    short_addr,
    endpoint_ids=None,
    include_power_desc=True,
    include_green_power=False,
    timeout_ms=6000,
    poll_ms=200,
    strict=True,
)

print("uzigbee.hil.discover.short_addr", hex(short_addr))
print("uzigbee.hil.discover.result", result)

assert result["short_addr"] == short_addr
assert isinstance(result["endpoint_ids"], list)
assert isinstance(result["simple_descriptors"], list)
assert result["node_descriptor"] is not None
assert result["power_descriptor"] is not None
assert result["errors"] == []

print("uzigbee.hil.discover.result PASS")
