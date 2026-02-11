# Progress 2026-02-06 Step 12

Scope:
- Complete remaining `plan.md` item in Faza 2:
  - `Stałe ZCL (cluster IDs, attribute IDs, typy danych)`.
- Keep the step fully validated (host tests + build + flash + HIL on `COM5`).

Implemented:
- `python/uzigbee/zcl.py`
  - Expanded cluster ID constants (`CLUSTER_ID_*`) for core HA areas:
    - basic/onoff/level/color
    - measurement (temperature/humidity/pressure/occupancy)
    - IAS/thermostat/metering/electrical/etc.
  - Expanded attribute ID constants:
    - Basic (`ATTR_BASIC_*`)
    - On/Off (`ATTR_ON_OFF_*`)
    - Level Control (`ATTR_LEVEL_CONTROL_*`)
    - Color Control (`ATTR_COLOR_CONTROL_*`)
    - selected sensor and IAS attributes.
  - Added ZCL data type constants (`DATA_TYPE_*`) aligned with `ESP_ZB_ZCL_ATTR_TYPE_*`.
  - Added lightweight helpers:
    - `cluster_name(cluster_id)`
    - `data_type_name(data_type)`
    - `data_type_size(data_type)`
    - `is_string_type(data_type)`
  - Kept backward-compatible aliases used by existing tests/examples.
- Tests:
  - Added `tests/test_zcl.py`.
- Docs:
  - Updated `docs/API.md` with `uzigbee.zcl` constant/helper surface.
  - Updated `docs/BUILD.md` with latest validated image size.
- Plan:
  - Marked Faza 2 item `Stałe ZCL (...)` as done in `plan.md`.

Host validation:
- `python -m pytest tests/test_zcl.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py -q`
- Result: `10 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step12a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x221b30`
  - app partition: `0x3eb000`
  - free: `0x1c94d0` (~46%)
- Flash to `COM5`: PASS.
- `esptool` flash detection on `COM5`: `4MB`.

Device validation (`COM5`):
- ZCL sanity:
  - `CLUSTER_ID_LEVEL_CONTROL`: `0x8`
  - `cluster_name(CLUSTER_ID_ON_OFF)`: `on_off`
  - `data_type_size(DATA_TYPE_BOOL)`: `1`
  - `is_string_type(DATA_TYPE_CHAR_STRING)`: `True`
- HIL regression suite:
  - `tests/hil_z2m_validate_smoke.py`: PASS
  - `tests/hil_z2m_setters_smoke.py`: PASS
  - `tests/hil_basic_identity_smoke.py`: PASS
  - `tests/hil_attr_smoke.py`: PASS
  - `tests/hil_attr_callback_smoke.py`: PASS
  - `tests/hil_signal_smoke.py`: PASS
  - `tests/hil_endpoint_smoke.py`: PASS
  - `tests/hil_onoff_light_smoke.py`: PASS

Notes:
- `COM5` access remains strictly single-process; a combined long-running mpremote batch timed out once and was replaced with per-test sequential runs.
- Existing behavior remains unchanged where firmware may return `ESP_ERR_INVALID_STATE` when setters run before full stack readiness; test scripts already handle this safely.
