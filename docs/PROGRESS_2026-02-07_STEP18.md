# Progress 2026-02-07 Step 18

Scope:
- Start next small complete increment in Faza 3:
  - implement `TemperatureSensor` (first part of `TemperatureSensor/HumiditySensor/PressureSensor`).
- Keep full validation:
  - host unit tests
  - WSL build
  - flash + HIL on hardware.

Implemented:
- C bridge / core:
  - `c_module/uzb_core.h`
    - added `uzb_core_create_temperature_sensor_endpoint(...)`.
  - `c_module/uzb_core.c`
    - added endpoint kind `UZB_ENDPOINT_KIND_TEMPERATURE_SENSOR`.
    - added `uzb_core_create_temperature_sensor_endpoint(...)` with device id `ESP_ZB_HA_TEMPERATURE_SENSOR_DEVICE_ID`.
    - added register path using:
      - `esp_zb_temperature_sensor_ep_create(...)`
      - `ESP_ZB_DEFAULT_TEMPERATURE_SENSOR_CONFIG()`.
  - `c_module/mod_uzigbee.c`
    - new API:
      - `_uzigbee.create_temperature_sensor(...)`
    - exported constants:
      - `DEVICE_ID_TEMPERATURE_SENSOR`
      - `CLUSTER_ID_TEMP_MEASUREMENT`
      - `ATTR_TEMP_MEASUREMENT_VALUE`.
- Python core/API:
  - `python/uzigbee/core.py`
    - added:
      - `DEVICE_ID_TEMPERATURE_SENSOR`
      - `CLUSTER_ID_TEMP_MEASUREMENT`
      - `ATTR_TEMP_MEASUREMENT_VALUE`
      - `ZigbeeStack.create_temperature_sensor(...)`.
  - `python/uzigbee/__init__.py`
    - exported all above constants and `TemperatureSensor`.
- High-level devices:
  - `python/uzigbee/devices.py`
    - added `TemperatureSensor`:
      - `provision()`
      - `validate_interview()`
      - `get_temperature_raw()`
      - `get_temperature_c()`
      - `set_temperature_raw()`
      - `set_temperature_c()`
      - `temperature_c` property
      - `on_temperature_change(...)`.
- Tests:
  - updated `tests/test_core_api.py`
  - updated `tests/test_devices_api.py`
  - updated `tests/test_import.py`
  - added `tests/hil_temperature_sensor_smoke.py`.

Validation:
- Host tests:
  - `python -m pytest tests/test_devices_api.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py tests/test_zcl.py -q`
  - result: `23 passed`.
- WSL build:
  - output dir: `build-ESP32_GENERIC_C6-uzigbee-step18a`
  - `micropython.bin`: `0x23a530`
  - app partition: `0x3eb000`
  - free: `0x1b0ad0` (~43%).
- Flash:
  - target detected as ESP32-C6 on `COM3`
  - flash to `COM3`: PASS.
- HIL on device:
  - new:
    - `tests/hil_temperature_sensor_smoke.py`: PASS
  - regression:
    - `tests/hil_switch_smoke.py`: PASS
    - `tests/hil_dimmable_switch_smoke.py`: PASS
    - `tests/hil_light_device_smoke.py`: PASS
    - `tests/hil_dimmable_light_smoke.py`: PASS
    - `tests/hil_color_light_smoke.py`: PASS
    - `tests/hil_basic_identity_smoke.py`: PASS
    - `tests/hil_z2m_validate_smoke.py`: PASS.

Operational notes:
- `COM5` was not present in this session; active ESP32-C6 test target was `COM3`.
- `mpremote` may intermittently fail raw-REPL entry or hang on long batches.
- Stable flow remains: single-process sequential execution + retry/recover per test.
