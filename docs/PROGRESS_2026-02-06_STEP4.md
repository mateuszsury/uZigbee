# Progress 2026-02-06 Step 4

Scope:
- Start "network info queries" from Faza 1 in `plan.md` with minimal, safe primitives:
  - short network address
  - IEEE long address

Implemented:
- `c_module/uzb_core.h`
  - Added:
    - `uzb_core_get_short_addr(uint16_t *out_short_addr)`
    - `uzb_core_get_ieee_addr(uint8_t out_ieee_addr[8])`
- `c_module/uzb_core.c`
  - Implemented both getters.
  - Enforced Zigbee lock on each call.
  - Returned clear errors for invalid state (`not started`), invalid args, and lock timeout.
- `c_module/mod_uzigbee.c`
  - Added:
    - `_uzigbee.get_short_addr() -> int`
    - `_uzigbee.get_ieee_addr() -> bytes(8)`
- `python/uzigbee/core.py`
  - Added:
    - `ZigbeeStack.get_short_addr()`
    - `ZigbeeStack.get_ieee_addr()`
    - properties: `short_address`, `ieee_address`
- `tests/test_core_api.py`
  - Extended fake backend and assertions for both new getters.

Host validation:
- `python -m pytest tests/test_core_api.py -q` -> `2 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step4a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x204a90`
  - app partition: `0x240000`
  - free: `0x3b570` (~10%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- HIL runtime check after `init/start`:
  - `get_short_addr()` -> `65534` (`0xFFFE`, coordinator during startup)
  - `get_ieee_addr()` -> `b'644c4efeffca4c40'` (hex-encoded bytes)
  - callback events still received: `3`
  - event stats: `dropped_queue_full=0`, `dropped_schedule_fail=0`
  - result: PASS

Notes:
- Immediately after flash, `mpremote soft-reset` can occasionally fail to enter raw REPL.
  - Retry with `mpremote ... resume exec ...` solved this reliably.
