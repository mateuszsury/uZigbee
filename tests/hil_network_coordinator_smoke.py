"""HIL smoke for high-level coordinator/network scaffold."""

import uzigbee


ESP_ERR_INVALID_STATE = 259
ESP_FAIL = -1

stack = uzigbee.ZigbeeStack()
stack.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.DimmableSwitch(
    endpoint_id=1,
    stack=stack,
    manufacturer="uzigbee",
    model="uzb_net_smoke_01",
    sw_build_id="step49",
)

try:
    switch.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

coordinator = uzigbee.Coordinator(
    stack=stack,
    auto_discovery=False,
    strict_discovery=False,
)
coordinator.start(form_network=False)

permit_join_ok = True
permit_join_errno = None
try:
    coordinator.permit_join(5, auto_discover=False)
except OSError as exc:
    permit_join_ok = False
    permit_join_errno = exc.args[0] if exc.args else None
    if permit_join_errno not in (ESP_ERR_INVALID_STATE, ESP_FAIL):
        raise

fake_discovered = {
    "short_addr": 0x1234,
    "endpoint_ids": [1, 2],
    "simple_descriptors": [
        {
            "endpoint": 1,
            "snapshot": {
                "status": 0,
                "addr": 0x1234,
                "simple_desc": {
                    "endpoint": 1,
                    "profile_id": 0x0104,
                    "device_id": 0x0000,
                    "device_version": 1,
                    "input_clusters": [uzigbee.CLUSTER_ID_ON_OFF, uzigbee.CLUSTER_ID_LEVEL_CONTROL],
                    "output_clusters": [],
                },
            },
        },
        {
            "endpoint": 2,
            "snapshot": {
                "status": 0,
                "addr": 0x1234,
                "simple_desc": {
                    "endpoint": 2,
                    "profile_id": 0x0104,
                    "device_id": 0x0000,
                    "device_version": 1,
                    "input_clusters": [uzigbee.CLUSTER_ID_TEMP_MEASUREMENT],
                    "output_clusters": [],
                },
            },
        },
    ],
}

device = coordinator._build_device_from_descriptors(fake_discovered)
coordinator.registry.upsert(device)

print("uzigbee.hil.network.short", hex(device.short_addr))
print("uzigbee.hil.network.features", sorted(device.features))
print("uzigbee.hil.network.map.onoff", device.endpoint_for(uzigbee.CLUSTER_ID_ON_OFF))
print("uzigbee.hil.network.map.temp", device.endpoint_for(uzigbee.CLUSTER_ID_TEMP_MEASUREMENT))
print("uzigbee.hil.network.registry_size", len(coordinator.list_devices()))
print("uzigbee.hil.network.permit_join", {"ok": permit_join_ok, "errno": permit_join_errno})

assert device.endpoint_for(uzigbee.CLUSTER_ID_ON_OFF) == 1
assert device.endpoint_for(uzigbee.CLUSTER_ID_TEMP_MEASUREMENT) == 2
assert device.has_feature("on_off") is True
assert device.has_feature("temperature") is True
assert len(coordinator.list_devices()) >= 1

stats = stack.event_stats()
print("uzigbee.hil.network.stats", stats)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.network.result PASS")
