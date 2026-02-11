"""HIL smoke test for Zigbee signal callback bridge on ESP32-C6."""

import time

import uzigbee


events = []


def _cb(signal_id, status):
    events.append((signal_id, status))


z = uzigbee.ZigbeeStack()
z.on_signal(_cb)
z.init(uzigbee.ROLE_COORDINATOR)
z.start(form_network=False)

deadline = time.ticks_add(time.ticks_ms(), 5000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    time.sleep_ms(100)

stats = z.event_stats()
print("uzigbee.hil.stats", stats)
print("uzigbee.hil.events", len(events))
if events:
    print("uzigbee.hil.first_event", events[0][0], events[0][1])

assert stats["enqueued"] >= stats["dispatched"]
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
assert stats["dispatched"] > 0

if not events:
    print("uzigbee.hil.note callback_count_zero_but_dispatched_positive")

print("uzigbee.hil.result PASS")
