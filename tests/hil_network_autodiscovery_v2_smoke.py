"""HIL smoke for Coordinator auto-discovery pipeline v2 internals."""

import time

import uzigbee


class _HilCoordinator(uzigbee.Coordinator):
    __slots__ = ("_failures_left", "_success_seen")

    def __init__(self, **kwargs):
        super().__init__(auto_discovery=False, **kwargs)
        self._failures_left = {}
        self._success_seen = {}

    def set_failures(self, short_addr, count):
        self._failures_left[int(short_addr) & 0xFFFF] = int(count)

    def discover_device(self, short_addr, endpoint_ids=None, strict=None):
        short_addr = int(short_addr) & 0xFFFF
        left = int(self._failures_left.get(short_addr, 0))
        if left > 0:
            self._failures_left[short_addr] = left - 1
            raise OSError(110, "simulated timeout")
        self._success_seen[short_addr] = self._success_seen.get(short_addr, 0) + 1
        # Keep queue semantics identical to production discover path.
        self._remove_pending(short_addr)
        return {"short_addr": short_addr}


def _wait_until_due(entry):
    now = time.ticks_ms()
    due = int(entry.get("next_try_ms", now))
    wait_ms = time.ticks_diff(due, now)
    if wait_ms > 0:
        time.sleep_ms(wait_ms + 15)


# 1) Debounce behavior on repeated queue requests for same short address.
debounce = _HilCoordinator(join_debounce_ms=1200, discovery_retry_base_ms=50, discovery_retry_max_backoff_ms=200)
now_ms = time.ticks_ms()
queued_1 = debounce._queue_discovery(0x2222, now_ms=now_ms)
queued_2 = debounce._queue_discovery(0x2222, now_ms=now_ms + 100)
assert queued_1 is True
assert queued_2 is False
debounce_stats = debounce.discovery_stats()
assert int(debounce_stats["debounced"]) >= 1

# 2) Retry/backoff behavior with eventual success.
retry = _HilCoordinator(
    join_debounce_ms=0,
    discovery_retry_max=3,
    discovery_retry_base_ms=50,
    discovery_retry_max_backoff_ms=200,
)
retry.set_failures(0x3333, 2)
assert retry._queue_discovery(0x3333, now_ms=time.ticks_ms()) is True

summary_1 = retry._process_discovery_queue(max_items=1)
assert summary_1["processed"] == 1
assert summary_1["failed"] == 1
pending_1 = retry.pending_discovery()
assert len(pending_1) == 1
_wait_until_due(pending_1[0])

summary_2 = retry._process_discovery_queue(max_items=1)
assert summary_2["processed"] == 1
assert summary_2["failed"] == 1
pending_2 = retry.pending_discovery()
assert len(pending_2) == 1
_wait_until_due(pending_2[0])

summary_3 = retry._process_discovery_queue(max_items=1)
assert summary_3["processed"] == 1
assert summary_3["success"] == 1
assert retry.pending_discovery() == ()

retry_stats = retry.discovery_stats()
assert int(retry_stats["requeued"]) >= 2
assert int(retry_stats["success"]) >= 1

# 3) Hardening timing clamps maintain timeout >= 2 * poll.
retry.discover_poll_ms = 1
retry.discover_timeout_ms = 1
retry._normalize_discovery_timing()
assert int(retry.discover_poll_ms) >= 1
assert int(retry.discover_timeout_ms) >= int(retry.discover_poll_ms) * 2

print("uzigbee.hil.netv2.debounce", {"queued_1": queued_1, "queued_2": queued_2, "stats": debounce_stats})
print("uzigbee.hil.netv2.retry", {"summary_1": summary_1, "summary_2": summary_2, "summary_3": summary_3, "stats": retry_stats})
print(
    "uzigbee.hil.netv2.timing",
    {"poll_ms": int(retry.discover_poll_ms), "timeout_ms": int(retry.discover_timeout_ms)},
)
print("uzigbee.hil.netv2.result PASS")
