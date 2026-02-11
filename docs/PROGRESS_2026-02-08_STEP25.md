# Progress 2026-02-08 - Step 25

Scope:
- implement next plan items from `plan.md`:
  - `ContactSensor`, `MotionSensor` via IAS Zone
  - generic `IASZone`
- add robust HIL batch runner for `COM3/COM5` with reset/retry.

Implemented:
- C core (`c_module/uzb_core.c`, `c_module/uzb_core.h`):
  - added IAS endpoint APIs:
    - `uzb_core_create_ias_zone_endpoint(endpoint, zone_type)`
    - `uzb_core_create_contact_sensor_endpoint(endpoint)`
    - `uzb_core_create_motion_sensor_endpoint(endpoint)`
  - added IAS endpoint registration path:
    - endpoint device id: `ESP_ZB_HA_IAS_ZONE_ID`
    - clusters:
      - Basic (server)
      - Identify (server)
      - IAS Zone (server)
    - IAS config sets `zone_type` from the selected endpoint creation call.
- C module (`c_module/mod_uzigbee.c`):
  - added wrappers:
    - `create_ias_zone(endpoint=1, zone_type=0x0015)`
    - `create_contact_sensor(endpoint=1)`
    - `create_motion_sensor(endpoint=1)`
  - exported constants:
    - `CLUSTER_ID_IAS_ZONE`
    - `ATTR_IAS_ZONE_STATE`, `ATTR_IAS_ZONE_TYPE`, `ATTR_IAS_ZONE_STATUS`, `ATTR_IAS_ZONE_IAS_CIE_ADDRESS`, `ATTR_IAS_ZONE_ID`
    - `DEVICE_ID_IAS_ZONE`, `DEVICE_ID_CONTACT_SENSOR`, `DEVICE_ID_MOTION_SENSOR`
    - `IAS_ZONE_TYPE_MOTION`, `IAS_ZONE_TYPE_CONTACT_SWITCH`
    - `IAS_ZONE_STATUS_ALARM1`, `IAS_ZONE_STATUS_ALARM2`, `IAS_ZONE_STATUS_TAMPER`, `IAS_ZONE_STATUS_BATTERY`
- Python core (`python/uzigbee/core.py`):
  - added constants matching C exports.
  - added API:
    - `create_ias_zone(endpoint_id=1, zone_type=IAS_ZONE_TYPE_CONTACT_SWITCH)`
    - `create_contact_sensor(endpoint_id=1)`
    - `create_motion_sensor(endpoint_id=1)`
- High-level devices (`python/uzigbee/devices.py`):
  - added `IASZone`:
    - zone status read/write
    - alarm bit helpers
    - callback dispatch on IAS Zone status changes
  - added `ContactSensor`:
    - `contact` semantics (`True` = closed contact)
  - added `MotionSensor`:
    - `motion` semantics (`True` = motion detected)
- Public exports (`python/uzigbee/__init__.py`):
  - exported new classes/constants.

Tests:
- Host unit tests:
  - `tests/test_core_api.py`
  - `tests/test_devices_api.py`
  - `tests/test_import.py`
  - result: `31 passed`.
- Added HIL tests:
  - `tests/hil_contact_sensor_smoke.py`
  - `tests/hil_motion_sensor_smoke.py`
- Device HIL results (`COM3`):
  - `tests/hil_contact_sensor_smoke.py`: PASS
  - `tests/hil_motion_sensor_smoke.py`: PASS
  - `tests/hil_zigbee_bridge_addr_smoke.py`: PASS
  - IEEE bridge readback:
    - `644c4efeffca4c40`

Robust HIL runner:
- Added:
  - `tools/hil_runner.py`
- Features:
  - port priority and fallback (`COM3`, `COM5` by default)
  - run-mode reset pulse before attempts
  - retries per test/port
  - tries both:
    - `resume run`
    - `resume soft-reset run`
- Validated run:
  - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_contact_sensor_smoke.py tests/hil_motion_sensor_smoke.py tests/hil_zigbee_bridge_addr_smoke.py --retries 4`
  - result: `PASS 3 tests`.

Build and flash:
- WSL build:
  - `BOARD=ESP32_GENERIC_C6`
  - `BUILD=build-ESP32_GENERIC_C6-uzigbee-step25a`
  - result: PASS
  - `micropython.bin = 0x259000`
  - free app partition: `0x192000` (~40%)
- Flash (Windows):
  - target: `COM3`
  - result: PASS.

Plan updates:
- `plan.md` updated:
  - marked done:
    - `ContactSensor`, `MotionSensor` (IAS Zone)
    - `IASZone` generic (parameterized zone type)
