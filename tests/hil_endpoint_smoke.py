"""HIL smoke for endpoint create/register path."""

import time

import uzigbee


events = []
ESP_ERR_INVALID_STATE = 259


def _cb(signal_id, status):
    events.append((signal_id, status))


z = uzigbee.ZigbeeStack()
z.on_signal(_cb)
z.init(uzigbee.ROLE_COORDINATOR)
try:
    z.create_endpoint(1, uzigbee.DEVICE_ID_ON_OFF_LIGHT, uzigbee.PROFILE_ID_ZHA)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    z.register_device()
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

deadline = time.ticks_add(time.ticks_ms(), 5000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    time.sleep_ms(100)

stats = z.event_stats()
print("uzigbee.hil.endpoint.stats", stats)
print("uzigbee.hil.endpoint.events", len(events))
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
assert stats["dispatched"] > 0
if not events:
    print("uzigbee.hil.endpoint.note callback_count_zero_but_dispatched_positive")
print("uzigbee.hil.endpoint.result PASS")
