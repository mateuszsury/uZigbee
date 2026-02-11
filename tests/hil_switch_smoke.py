"""HIL smoke for high-level uzigbee.Switch wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.Switch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_switch_01",
    sw_build_id="step16",
)

try:
    switch.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

dst_short = 0x0000
try:
    dst_short = int(z.get_short_addr())
except Exception:
    pass

switch.send_on(dst_short, 1)
switch.send_off(dst_short, 1)
switch.toggle(dst_short, 1)

stats = z.event_stats()
print("uzigbee.hil.switch.dst_short", dst_short)
print("uzigbee.hil.switch.stats", stats)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.switch.result PASS")
