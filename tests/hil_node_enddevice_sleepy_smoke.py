"""HIL smoke for EndDevice sleepy profile API (Phase 4.6)."""

import sys

if "/remote/python" not in sys.path:
    sys.path.insert(0, "/remote/python")

import uzigbee


ESP_ERR_INVALID_STATE = 259

stack = uzigbee.ZigbeeStack()
stack.init(uzigbee.ROLE_COORDINATOR)
end_device = (
    uzigbee.EndDevice(
        stack=stack,
        auto_register=False,
        sleepy=True,
        keep_alive_ms=4000,
        poll_interval_ms=1500,
        wake_window_ms=500,
        checkin_interval_ms=20000,
        low_power_reporting=True,
    )
    .add_contact_sensor(endpoint_id=4, name="door_end")
)

end_device.mark_wake(now_ms=1000)
end_device.mark_poll(now_ms=1000)
end_device.mark_keepalive(now_ms=1000)
configured = end_device.configure_reporting_policy("contact", endpoint_id=4)
profile = end_device.sleepy_profile()
status = end_device.status()
stack_stats = stack.event_stats()

print("uzigbee.hil.node.enddevice.configured", configured)
print("uzigbee.hil.node.enddevice.profile", profile)
print("uzigbee.hil.node.enddevice.status", status)
print("uzigbee.hil.node.enddevice.stats", stack_stats)

entry = configured[0]["entries"][0]
assert entry[3] >= 30
assert entry[4] >= 900
assert profile["sleepy"] is True
assert end_device.wake_window_active(now_ms=1300) is True
assert end_device.wake_window_active(now_ms=1800) is False
assert end_device.should_poll(now_ms=2600) is True
assert end_device.should_keepalive(now_ms=5200) is True
assert status["reporting_policy_count"] >= 1
assert stack_stats["dropped_queue_full"] == 0
assert stack_stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.node.enddevice.result PASS")
