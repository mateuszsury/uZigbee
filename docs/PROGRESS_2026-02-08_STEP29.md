# Progress 2026-02-08 Step 29

## Scope
- Added Python helper layer for reporting presets:
  - `python/uzigbee/reporting.py`
- Target presets:
  - doorlock
  - thermostat
  - occupancy
  - contact sensor
  - motion sensor

## What changed
- New module:
  - `python/uzigbee/reporting.py`
- New presets:
  - `PRESET_DOOR_LOCK`
  - `PRESET_THERMOSTAT`
  - `PRESET_OCCUPANCY`
  - `PRESET_CONTACT_SENSOR`
  - `PRESET_MOTION_SENSOR`
- New helpers:
  - `apply_reporting_preset(...)`
  - `configure_door_lock(...)`
  - `configure_thermostat(...)`
  - `configure_occupancy(...)`
  - `configure_contact_sensor(...)`
  - `configure_motion_sensor(...)`
- Package export:
  - `python/uzigbee/__init__.py` now exports `reporting`.

## Tests
- Added host tests:
  - `tests/test_reporting_api.py`
- Added HIL smoke:
  - `tests/hil_reporting_presets_smoke.py`

## Validation
- Host tests:
  - `pytest -q tests/test_reporting_api.py tests/test_import.py tests/test_core_api.py tests/test_devices_api.py tests/test_z2m_api.py`
  - Result: `40 passed`
- Extra host regression:
  - `pytest -q tests/test_z2m_interview_suite.py tests/test_reporting_api.py`
  - Result: `8 passed`
- HIL device tests (COM3):
  - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_reporting_presets_smoke.py --retries 3 --timeout 120`
  - Result: `PASS 1 tests`
  - output:
    - `uzigbee.hil.reporting_preset.count 3`
- Revalidated reporting core smoke:
  - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_reporting_config_smoke.py --retries 3 --timeout 120`
  - Result: `PASS 1 tests`

## Build/flash
- Rebuild required to freeze new module:
  - `build-ESP32_GENERIC_C6-uzigbee-step28a`
  - `micropython.bin = 0x264d40`, free `0x1862c0` (~39%)
- Flashed to `COM3` with `esptool` successfully.

## Plan status
- Updated `plan.md`:
  - kept `Attribute reporting configuration` as done.
  - added and marked done:
    - `Python helper uzigbee.reporting presets (doorlock/thermostat/occupancy/contact/motion)`
