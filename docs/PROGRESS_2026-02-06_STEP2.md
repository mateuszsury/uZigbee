# Progress 2026-02-06 Step 2

Scope:
- Implement minimal production-grade Zigbee -> MicroPython callback bridge:
  - static event ring buffer
  - scheduler handoff (`mp_sched_schedule`)
  - Python callback registration
  - event queue diagnostics
- Increase app partition margin for next iterations.

Implemented:
- `c_module/uzb_core.h`
  - Added `uzb_app_signal_event_t`, `uzb_event_stats_t`, dispatch callback type, and queue APIs.
- `c_module/uzb_core.c`
  - Added static ring buffer (`UZB_EVENT_QUEUE_LEN=16`).
  - Added thread-safe queue bookkeeping with critical section.
  - Added dispatch request flow with `pending` state and schedule-fail accounting.
  - Added event stats reporting.
  - Wired `esp_zb_app_signal_handler` to enqueue signals only.
- `c_module/mod_uzigbee.c`
  - Added GC-rooted Python callback pointer.
  - Added `_uzigbee.set_signal_callback(callback|None)`.
  - Added `_uzigbee.get_event_stats()`.
  - Added scheduler dispatch function that drains queue in MicroPython context and invokes Python callback.
- `python/uzigbee/core.py`
  - Added `ZigbeeStack.set_signal_callback`.
  - Added `ZigbeeStack.event_stats`.
- `firmware/partitions.csv`
  - Extended app partition:
    - `factory` `0x210000 -> 0x240000`
  - Shifted storage offsets accordingly.

Host validation:
- `pytest` unavailable in current Windows venv (`No module named pytest`).
- Executed manual host smoke for wrappers: PASS.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`) successful.
- Image/partition check:
  - `micropython.bin`: `0x203920`
  - app partition: `0x240000`
  - free: `0x3c6e0` (~10%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `_uzigbee.set_signal_callback`: `True`
  - `_uzigbee.get_event_stats`: `True`
  - `ZigbeeStack.set_signal_callback`: `True`
  - `ZigbeeStack.event_stats`: `True`
- Runtime callback smoke:
  - callback invoked with real Zigbee signals (example seen: `23,-1`, `1,0`, `10,0`)
  - queue stats after run:
    - `enqueued=3`
    - `dispatched=3`
    - `dropped_queue_full=0`
    - `dropped_schedule_fail=0`
    - `max_depth=3`
    - `depth=0`

Notes:
- `mpremote` tests must be executed sequentially on one COM port; parallel invocations lock `COM5`.
- Current implementation is intentionally minimal and safe; next step can extend typed events beyond app signals.
