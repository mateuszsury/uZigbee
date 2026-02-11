# Progress 2026-02-08 - Step 20

Scope:
- complete `PressureSensor` and `ClimateSensor` (next small steps from `plan.md`).
- keep full validation as one batch at the end (host tests + build + flash + HIL).

Implemented:
- `c_module/uzb_core.h`
  - added:
    - `uzb_core_create_pressure_sensor_endpoint(...)`
    - `uzb_core_create_climate_sensor_endpoint(...)`.
- `c_module/uzb_core.c`
  - added endpoint kinds:
    - `UZB_ENDPOINT_KIND_PRESSURE_SENSOR`
    - `UZB_ENDPOINT_KIND_CLIMATE_SENSOR`.
  - added endpoint creators:
    - pressure sensor endpoint (`ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID`).
    - climate sensor endpoint (`ESP_ZB_HA_SIMPLE_SENSOR_DEVICE_ID`).
  - added register branches:
    - pressure: Basic + Identify + Pressure Measurement server clusters.
    - climate: Basic + Identify + Temperature + Humidity + Pressure server clusters.
  - fixed SDK API call name for current library version:
    - `esp_zb_cluster_list_add_temperature_meas_cluster(...)`.
- `c_module/mod_uzigbee.c`
  - exported:
    - `_uzigbee.create_pressure_sensor(...)`
    - `_uzigbee.create_climate_sensor(...)`.
  - exported constants:
    - `CLUSTER_ID_PRESSURE_MEASUREMENT`
    - `ATTR_PRESSURE_MEASUREMENT_VALUE`
    - `DEVICE_ID_PRESSURE_SENSOR`
    - `DEVICE_ID_CLIMATE_SENSOR`.
- `python/uzigbee/core.py`
  - added constants:
    - `CLUSTER_ID_PRESSURE_MEASUREMENT`
    - `ATTR_PRESSURE_MEASUREMENT_VALUE`
    - `DEVICE_ID_PRESSURE_SENSOR`
    - `DEVICE_ID_CLIMATE_SENSOR`.
  - added stack methods:
    - `create_pressure_sensor(...)`
    - `create_climate_sensor(...)`.
- `python/uzigbee/devices.py`
  - added `PressureSensor` class (read/write + callback for pressure measured value).
  - added `ClimateSensor` class (combined temperature/humidity/pressure read/write + callbacks).
- `python/uzigbee/__init__.py`
  - exported new constants and classes:
    - `PressureSensor`
    - `ClimateSensor`.
- tests:
  - updated host tests:
    - `tests/test_core_api.py`
    - `tests/test_devices_api.py`
    - `tests/test_import.py`.
  - added HIL tests:
    - `tests/hil_pressure_sensor_smoke.py`
    - `tests/hil_climate_sensor_smoke.py`.

Validation:
- Host tests:
  - `python -m pytest tests`
  - result: `29 passed`.
- WSL build:
  - board: `ESP32_GENERIC_C6`
  - output dir: `build-ESP32_GENERIC_C6-uzigbee-step20a`
  - binary size:
    - `micropython.bin = 0x240dc0`
    - free in app partition `0x1aa240` (~42%).
- Flash:
  - target: ESP32-C6 on `COM3`
  - result: PASS.
- HIL (sequential, with retry on transient port/raw-REPL issues):
  - `tests/hil_basic_identity_smoke.py`: PASS
  - `tests/hil_light_device_smoke.py`: PASS
  - `tests/hil_temperature_sensor_smoke.py`: PASS
  - `tests/hil_humidity_sensor_smoke.py`: PASS
  - `tests/hil_pressure_sensor_smoke.py`: PASS
  - `tests/hil_climate_sensor_smoke.py`: PASS
  - `tests/hil_z2m_validate_smoke.py`: PASS.

Notes:
- During the HIL batch, first attempt for some sensor scripts hit a Zigbee stack assert and device rebooted; immediate retry passed consistently.
- Build/flash/HIL were kept isolated from other agents by:
  - WSL env from `tools/wsl-env.sh`
  - unique build dir `build-ESP32_GENERIC_C6-uzigbee-step20a`
  - single-process sequential access to `COM3`.
