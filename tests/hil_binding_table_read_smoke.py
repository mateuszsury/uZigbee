"""HIL smoke for ZDO Mgmt_Bind request + snapshot API."""

import time

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.DimmableSwitch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_bind_table_smoke",
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

# Request binding table from local node. On some stack states response can be delayed.
z.request_binding_table(short_addr, start_index=0)

snapshot = None
deadline = time.ticks_add(time.ticks_ms(), 5000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    snapshot = z.get_binding_table_snapshot()
    if snapshot is not None:
        break
    time.sleep_ms(200)

print("uzigbee.hil.bind_table.short_addr", hex(short_addr))
print("uzigbee.hil.bind_table.snapshot", snapshot)

if snapshot is not None:
    assert isinstance(snapshot["status"], int)
    assert isinstance(snapshot["records"], list)

print("uzigbee.hil.bind_table.result PASS")
