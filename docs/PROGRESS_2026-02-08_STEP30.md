# Progress 2026-02-08 Step 30

## Scope
- Wired reporting presets into high-level HA wrappers in `uzigbee.devices`.

## What changed
- `python/uzigbee/devices.py`:
  - `DoorLock.configure_default_reporting(...)`
  - `Thermostat.configure_default_reporting(...)`
  - `OccupancySensor.configure_default_reporting(...)`
  - `IASZone.configure_default_reporting(...)`
  - `ContactSensor.configure_default_reporting(...)`
  - `MotionSensor.configure_default_reporting(...)`
- These methods call `uzigbee.reporting` presets with:
  - `src_endpoint = self.endpoint_id`
  - user-provided destination short address / endpoint.

## Tests
- Host:
  - extended fake stack with `configure_reporting(...)` capture
  - added wrapper integration test:
    - `tests/test_devices_api.py::test_default_reporting_helpers_for_ha_wrappers`
- New HIL:
  - `tests/hil_reporting_wrapper_thermostat_smoke.py`

## Validation
- Host:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_z2m_api.py tests/test_z2m_interview_suite.py tests/test_reporting_api.py`
  - Result: `46 passed`
- Build/flash:
  - rebuild `build-ESP32_GENERIC_C6-uzigbee-step28a`
  - flash to `COM3` with `esptool` successful
  - image size: `0x264f50`, free `0x1860b0` (~39%)
- HIL:
  - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_reporting_wrapper_thermostat_smoke.py tests/hil_reporting_presets_smoke.py tests/hil_reporting_config_smoke.py --retries 3 --timeout 120`
  - Result: `PASS 3 tests`

## Plan status
- Updated `plan.md` with completed item:
  - `Podpięcie presetów reporting do wrapperów HA (configure_default_reporting)`
