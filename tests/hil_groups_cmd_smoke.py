"""HIL smoke for Groups commands (add/remove/remove_all)."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.Switch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_groups_switch_01",
    sw_build_id="step31",
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

dst_short = int(z.get_short_addr())
group_id = 0x1234
switch.add_to_group(dst_short, group_id, dst_endpoint=1)
switch.remove_from_group(dst_short, group_id, dst_endpoint=1)
switch.clear_groups(dst_short, dst_endpoint=1)

stats = z.event_stats()
print("uzigbee.hil.groups.dst_short", hex(dst_short))
print("uzigbee.hil.groups.group_id", hex(group_id))
print("uzigbee.hil.groups.stats", stats)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.groups.result PASS")
