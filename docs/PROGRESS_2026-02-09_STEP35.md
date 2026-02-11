# Progress Step 35 (2026-02-09)

Scope:
- Fix web-demo control path where commands were sent to coordinator short address (`0x0000`) instead of the joined light.

Implementation:
- Added C-side tracking of the last joined device short address in `c_module/uzb_core.c`:
  - updates on signals: `DEVICE_ANNCE`, `DEVICE_UPDATE`, `DEVICE_AUTHORIZED`,
  - clears value on `LEAVE_INDICATION` (matching short address),
  - exposes getter: `uzb_core_get_last_joined_short_addr(...)`.
- Exposed new API in `_uzigbee`:
  - `get_last_joined_short_addr() -> int | None`
  - `None` is returned when no joined device is known yet.
- Added Python wrapper in `python/uzigbee/core.py`:
  - `ZigbeeStack.get_last_joined_short_addr()`.
- Updated example app `examples/coordinator_web_demo.py`:
  - on join-related signals (`device_announce`, `device_update`, `device_authorized`),
    demo attempts to adopt `get_last_joined_short_addr()` and updates UI target automatically.
- Added HIL smoke:
  - `tests/hil_last_joined_short_smoke.py`.
- Added/updated host tests:
  - `tests/test_core_api.py` for new wrapper call path,
  - `tests/test_example_coordinator_web_demo.py` for auto-target logic.

Validation:
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_example_coordinator_web_demo.py tests/test_devices_api.py tests/test_import.py`
  - result: `44 passed`
- Firmware build (WSL):
  - `build-ESP32_GENERIC_C6-uzigbee-step35a`
  - image size: `0x2721b0` with `0x178e50` free in app partition.
- Flash:
  - successful to `COM3` via `esptool`.
- HIL:
  - `tests/hil_zigbee_bridge_addr_smoke.py` PASS
  - `tests/hil_last_joined_short_smoke.py` PASS
  - `tests/hil_web_demo_startup_smoke.py` PASS
  - `tests/hil_web_demo_sta_smoke.py` PASS
- Runtime web check:
  - launcher `tools/run_web_demo_serial.py --port COM3 --reset`,
  - HTTP endpoints `/`, `/pair`, `/on`, `/off`, `/toggle`, `/level` responded `200`.

Observed runtime note:
- In this run no new join/update/authorized event arrived after startup, so target remained `0x0000` and UI control logs still showed `short=0x0000`.
- Expected behavior after this fix: once a new join/update/authorized signal is received (e.g., re-pair/power-cycle light during permit-join), demo auto-switches target to the joined device short address.

Plan status:
- `plan.md` updated with Step 35 execution log.
