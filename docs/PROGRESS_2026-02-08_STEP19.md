# Progress 2026-02-08 Step 19

Scope:
- Continue next small increment in Faza 3:
  - add `HumiditySensor` (second part of `TemperatureSensor/HumiditySensor/PressureSensor`).
- Keep full validation:
  - host unit tests
  - WSL build
  - flash + HIL on hardware.

Implemented:
- C bridge / core:
  - `c_module/uzb_core.h`
    - added `uzb_core_create_humidity_sensor_endpoint(...)`.
  - `c_module/uzb_core.c`
    - added endpoint kind `UZB_ENDPOINT_KIND_HUMIDITY_SENSOR`.
    - added `uzb_core_create_humidity_sensor_endpoint(...)`:
      - profile `ESP_ZB_AF_HA_PROFILE_ID`
      - device id `ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID`.
    - added register path for humidity endpoint:
      - basic cluster (server)
      - identify cluster (server)
      - relative humidity measurement cluster (server).
  - `c_module/mod_uzigbee.c`
    - new API:
      - `_uzigbee.create_humidity_sensor(...)`
    - new constants:
      - `DEVICE_ID_SIMPLE_SENSOR`
      - `DEVICE_ID_HUMIDITY_SENSOR`
      - `CLUSTER_ID_REL_HUMIDITY_MEASUREMENT`
      - `ATTR_REL_HUMIDITY_MEASUREMENT_VALUE`.
- Python core/API:
  - `python/uzigbee/core.py`
    - added:
      - `DEVICE_ID_SIMPLE_SENSOR`
      - `DEVICE_ID_HUMIDITY_SENSOR`
      - `CLUSTER_ID_REL_HUMIDITY_MEASUREMENT`
      - `ATTR_REL_HUMIDITY_MEASUREMENT_VALUE`
      - `ZigbeeStack.create_humidity_sensor(...)`.
  - `python/uzigbee/__init__.py`
    - exported new constants and class `HumiditySensor`.
- High-level devices:
  - `python/uzigbee/devices.py`
    - added `HumiditySensor`:
      - `provision()`
      - `validate_interview()`
      - `get_humidity_raw()`
      - `get_humidity_percent()`
      - `set_humidity_raw()`
      - `set_humidity_percent()`
      - `humidity_percent` property
      - `on_humidity_change(...)`.
- Tests:
  - updated `tests/test_core_api.py`
  - updated `tests/test_devices_api.py`
  - updated `tests/test_import.py`
  - added `tests/hil_humidity_sensor_smoke.py`.

Validation:
- Host tests:
  - `python -m pytest tests/test_devices_api.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py tests/test_zcl.py -q`
  - result: `25 passed`.
- WSL build:
  - output dir: `build-ESP32_GENERIC_C6-uzigbee-step19a`
  - `micropython.bin`: `0x23c7a0`
  - app partition: `0x3eb000`
  - free: `0x1ae860` (~43%).
- Flash:
  - target detected as ESP32-C6 on `COM3`
  - flash to `COM3`: PASS.
- HIL on device:
  - new:
    - `tests/hil_humidity_sensor_smoke.py`: PASS
  - regression:
    - `tests/hil_temperature_sensor_smoke.py`: PASS
    - `tests/hil_switch_smoke.py`: PASS
    - `tests/hil_dimmable_switch_smoke.py`: PASS
    - `tests/hil_light_device_smoke.py`: PASS
    - `tests/hil_dimmable_light_smoke.py`: PASS
    - `tests/hil_color_light_smoke.py`: PASS
    - `tests/hil_basic_identity_smoke.py`: PASS
    - `tests/hil_z2m_validate_smoke.py`: PASS.

Operational notes:
- `COM5` was not present in this session; active ESP32-C6 test target was `COM3`.
- `mpremote` can still intermittently fail raw-REPL entry or hang in long sessions.
- Stable procedure remains: sequential single-process execution + per-test retry/recover.
