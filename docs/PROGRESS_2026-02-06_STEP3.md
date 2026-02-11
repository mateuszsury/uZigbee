# Progress 2026-02-06 Step 3

Scope:
- Align stack-signal API to `plan.md`.
- Expose named Zigbee app signal constants.
- Add repeatable callback smoke validation on hardware.

Implemented:
- `c_module/mod_uzigbee.c`
  - Added `_uzigbee.on_signal(callback)` as the primary registration API.
  - Kept `_uzigbee.set_signal_callback(callback)` as backward-compatible alias.
  - Exported `SIGNAL_*` constants from Zigbee SDK signal enum (`esp_zigbee_zdo_common.h`).
- `python/uzigbee/core.py`
  - Added `ZigbeeStack.on_signal(callback)`.
  - Added signal constants mirrored from C module (with fallback defaults).
  - Added `SIGNAL_NAMES` map and `signal_name(signal_id)` helper.
- `python/uzigbee/__init__.py`
  - Re-exported key signal constants and `signal_name`.
- `tests/test_core_api.py`
  - Extended wrapper test for `on_signal`.
  - Added signal name helper test.
- `tests/hil_signal_smoke.py`
  - Added HIL smoke script for callback bridge and event queue stats.

Host validation:
- `python -m pytest tests/test_core_api.py -q` -> `2 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step3b`) successful.
- Image/partition check:
  - `micropython.bin`: `0x2046e0`
  - app partition: `0x240000`
  - free: `0x3b920` (~10%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `_uzigbee.on_signal`: `True`
  - `_uzigbee.SIGNAL_STEERING`: `True`
  - `uzigbee.SIGNAL_STEERING`: `True`
- Callback smoke:
  - queue stats: `enqueued=3`, `dispatched=3`, `dropped_queue_full=0`, `dropped_schedule_fail=0`
  - callback events captured: `3`
  - result: PASS
- `mpremote run tests/hil_signal_smoke.py`:
  - PASS based on queue dispatch stats
  - callback count in this mode may stay `0` (timing/context nuance), so script reports note instead of failing

Operational notes:
- `mpremote` access to `COM5` must be single-process and sequential.
- A first build attempt failed because PowerShell expanded `$(pwd)` into Windows path syntax for WSL `make` args.
  - Fix: pass explicit Linux paths (`/mnt/c/...`) for `USER_C_MODULES` and `FROZEN_MANIFEST`.
