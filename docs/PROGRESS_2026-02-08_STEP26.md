# Progress 2026-02-08 Step 26

## Scope
- Implemented next `plan.md` item in Faza 3:
  - `WindowCovering` (Z2M cover expose with position).

## What changed
- C module:
  - Added endpoint creator:
    - `_uzigbee.create_window_covering(...)`
    - `uzb_core_create_window_covering_endpoint(...)`
  - Added Window Covering constants:
    - cluster/device/attrs/cmd IDs exported to Python.
  - Added Window Covering endpoint registration path in `uzb_core_register_device`.
  - Added explicit position attributes to Window Covering cluster:
    - `CURRENT_POSITION_LIFT (0x0003)`
    - `CURRENT_POSITION_TILT (0x0004)`
    - `CURRENT_POSITION_LIFT_PERCENTAGE (0x0008)`
    - `CURRENT_POSITION_TILT_PERCENTAGE (0x0009)`
- Python API:
  - `ZigbeeStack.create_window_covering(endpoint_id=1)`
  - New high-level device `uzigbee.WindowCovering` with:
    - `get_lift_percentage`, `set_lift_percentage`
    - `get_tilt_percentage`, `set_tilt_percentage`
    - `position` property (lift alias)
    - `on_change(callback)` payload with lift/tilt percentages
- Tests:
  - Host:
    - extended `tests/test_core_api.py`
    - extended `tests/test_devices_api.py`
    - extended `tests/test_import.py`
  - HIL:
    - added `tests/hil_window_covering_smoke.py`
- Docs:
  - updated `docs/API.md`
  - updated `docs/BUILD.md`
  - marked plan item done in `plan.md`

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py`
  - Result: `32 passed`

- Firmware build (WSL, isolated ESP-IDF, unique build dir):
  - `BUILD=build-ESP32_GENERIC_C6-uzigbee-step26a`
  - Result: PASS
  - `micropython.bin` size: `0x25bbf0`
  - Free app partition: `0x18f410` (~40%)

- Flash:
  - Flashed to `COM3` with `esptool` using build `flash_args`
  - Result: PASS

- HIL tests on device (`COM3`):
  - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_window_covering_smoke.py tests/hil_zigbee_bridge_addr_smoke.py tests/hil_contact_sensor_smoke.py tests/hil_motion_sensor_smoke.py --retries 4 --timeout 180`
  - Result: `PASS 4 tests`
  - IEEE bridge check:
    - `ieee_api = 644c4efeffca4c40`
    - `ieee_core = 644c4efeffca4c40`

## Plan status
- Updated:
  - `plan.md`: `WindowCovering` marked as done (`[x]`).
