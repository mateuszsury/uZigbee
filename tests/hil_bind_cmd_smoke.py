"""HIL smoke for bind/unbind command wrappers."""

import time
import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.DimmableSwitch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_bind_smoke",
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

ieee = z.get_ieee_addr()
short_addr = int(z.get_short_addr())

# Smoke only: bind and unbind self-addressed entry to verify wrappers execute.
z.send_bind_cmd(
    src_ieee_addr=ieee,
    src_endpoint=1,
    cluster_id=uzigbee.CLUSTER_ID_ON_OFF,
    dst_ieee_addr=ieee,
    dst_endpoint=1,
    req_dst_short_addr=short_addr,
)
z.send_unbind_cmd(
    src_ieee_addr=ieee,
    src_endpoint=1,
    cluster_id=uzigbee.CLUSTER_ID_ON_OFF,
    dst_ieee_addr=ieee,
    dst_endpoint=1,
    req_dst_short_addr=short_addr,
)

print("uzigbee.hil.bind.short_addr", hex(short_addr))
print("uzigbee.hil.bind.result PASS")
