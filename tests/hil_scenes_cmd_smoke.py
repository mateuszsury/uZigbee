"""HIL smoke for Scenes commands (add/remove/remove_all/recall)."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.Switch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_scenes_switch_01",
    sw_build_id="step43",
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
scene_id = 1
switch.add_scene(dst_short, group_id, scene_id, dst_endpoint=1, transition_ds=0)
switch.recall_scene(dst_short, group_id, scene_id, dst_endpoint=1)
switch.remove_scene(dst_short, group_id, scene_id, dst_endpoint=1)
switch.clear_scenes(dst_short, group_id, dst_endpoint=1)

stats = z.event_stats()
print("uzigbee.hil.scenes.dst_short", hex(dst_short))
print("uzigbee.hil.scenes.group_id", hex(group_id))
print("uzigbee.hil.scenes.scene_id", scene_id)
print("uzigbee.hil.scenes.stats", stats)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.scenes.result PASS")
