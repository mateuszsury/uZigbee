# Progress 2026-02-08 - Step 21

Scope:
- finish `PowerOutlet` from `plan.md` with real HIL verification on ESP32-C6.
- keep WSL build isolation and sequential COM access due parallel ESP-IDF activity in another process.

Implemented:
- `c_module/uzb_core.c`
  - for endpoint kind `UZB_ENDPOINT_KIND_POWER_OUTLET_METERING`, added explicit Electrical Measurement attributes on cluster creation:
    - `ACTIVE_POWER` (`0x050B`, `int16_t`)
    - `RMSVOLTAGE` (`0x0505`, `uint16_t`)
    - `RMSCURRENT` (`0x0508`, `uint16_t`)
  - fallback strategy: if `esp_zb_electrical_meas_cluster_add_attr(...)` returns `ESP_ERR_INVALID_ARG`, try `esp_zb_cluster_update_attr(...)`.
  - this fixes runtime `OSError: 261` (`ESP_ERR_NOT_FOUND`) seen in `PowerOutlet.set_power(...)`.
- `plan.md`
  - marked `PowerOutlet` task as done in Faza 3.
- `docs/API.md`
  - added C/Python API entries and constants for PowerOutlet + Electrical Measurement cluster/attrs.
- `docs/BUILD.md`
  - added `hil_power_outlet_smoke.py` to smoke commands.
  - updated latest validated image to `build-ESP32_GENERIC_C6-uzigbee-step21b`.
  - documented retry pattern for `mpremote` raw-REPL instability.

Validation:
- Host tests:
  - `python -m pytest tests/test_core_api.py tests/test_devices_api.py tests/test_import.py`
  - result: `24 passed`.
- WSL build:
  - `BUILD=build-ESP32_GENERIC_C6-uzigbee-step21b`
  - result: PASS
  - `micropython.bin = 0x2436c0`
  - free app partition: `0x1a7940` (~42%).
- Flash:
  - target: `COM3` (`ESP32-C6`)
  - `esptool_exit=0`
- HIL (sequential, with retry/fallback between `resume` and `soft-reset`):
  - `tests/hil_basic_identity_smoke.py`: PASS
  - `tests/hil_light_device_smoke.py`: PASS
  - `tests/hil_temperature_sensor_smoke.py`: PASS
  - `tests/hil_climate_sensor_smoke.py`: PASS
  - `tests/hil_power_outlet_smoke.py`: PASS
  - `tests/hil_z2m_validate_smoke.py`: PASS

Operational notes:
- During long batch runs, single tests can hang on raw-REPL entry; process cleanup and immediate retry is reliable.
- Sequential single-process access to `COM3` is required (no parallel `mpremote`/`esptool`).
- Another agent process currently uses `COM14`; no conflict with `COM3` after enforcing single-process COM3 access.
