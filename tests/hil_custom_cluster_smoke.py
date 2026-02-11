"""HIL smoke for manufacturer-specific custom cluster path."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)
z.clear_custom_clusters()
z.add_custom_cluster(0xFC00, cluster_role=uzigbee.CLUSTER_ROLE_SERVER)
z.add_custom_attr(
    cluster_id=0xFC00,
    attr_id=0x0001,
    attr_type=uzigbee.zcl.DATA_TYPE_U16,
    attr_access=uzigbee.ATTR_ACCESS_READ_WRITE,
    initial_value=7,
)

light = uzigbee.Light(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_custom_light_01",
    sw_build_id="step45",
)

try:
    light.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

z.set_attribute(
    endpoint_id=1,
    cluster_id=0xFC00,
    attr_id=0x0001,
    value=11,
    cluster_role=uzigbee.CLUSTER_ROLE_SERVER,
    check=False,
)
custom_value = z.get_attribute(
    endpoint_id=1,
    cluster_id=0xFC00,
    attr_id=0x0001,
    cluster_role=uzigbee.CLUSTER_ROLE_SERVER,
)

dst_short = int(z.get_short_addr())
send_result = {"ok": True, "errno": None}
try:
    z.send_custom_cmd(
        dst_short_addr=dst_short,
        cluster_id=0xFC00,
        custom_cmd_id=0x0001,
        payload=b"\x01\x02",
        src_endpoint=1,
        dst_endpoint=1,
        profile_id=uzigbee.PROFILE_ID_ZHA,
        direction=uzigbee.CMD_DIRECTION_TO_SERVER,
        disable_default_resp=False,
        manuf_specific=False,
        manuf_code=0x0000,
        data_type=uzigbee.zcl.DATA_TYPE_OCTET_STRING,
    )
except OSError as exc:
    send_result["ok"] = False
    send_result["errno"] = exc.args[0] if exc.args else None

stats = z.event_stats()
print("uzigbee.hil.custom.cluster_id", hex(0xFC00))
print("uzigbee.hil.custom.attr_value", custom_value)
print("uzigbee.hil.custom.dst_short", hex(dst_short))
print("uzigbee.hil.custom.send_result", send_result)
print("uzigbee.hil.custom.stats", stats)
assert int(custom_value) == 11
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.custom.result PASS")
