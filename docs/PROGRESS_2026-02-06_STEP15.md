# Progress 2026-02-06 Step 15

Scope:
- Continue Faza 3 with the next smallest complete increment:
  - add `ColorLight` (On/Off + Level + Color Control XY).
- Keep full validation:
  - host unit tests
  - WSL build
  - flash + HIL.

Implemented:
- C bridge / core:
  - `c_module/uzb_core.h`
    - added `uzb_core_create_color_light_endpoint(...)`.
  - `c_module/uzb_core.c`
    - new endpoint kind `UZB_ENDPOINT_KIND_COLOR_LIGHT`.
    - new API `uzb_core_create_color_light_endpoint(...)`.
    - register path for color endpoint via
      `esp_zb_color_dimmable_light_ep_create(...)`.
  - `c_module/mod_uzigbee.c`
    - added `_uzigbee.create_color_light(...)`.
    - exported constants:
      - `CLUSTER_ID_COLOR_CONTROL`
      - `ATTR_COLOR_CONTROL_CURRENT_X`
      - `ATTR_COLOR_CONTROL_CURRENT_Y`
      - `ATTR_COLOR_CONTROL_COLOR_TEMPERATURE`
      - `DEVICE_ID_COLOR_DIMMABLE_LIGHT`.
- Python core/API:
  - `python/uzigbee/core.py`
    - added `ZigbeeStack.create_color_light(...)`.
    - added constants:
      - `CLUSTER_ID_COLOR_CONTROL`
      - `ATTR_COLOR_CONTROL_CURRENT_X`
      - `ATTR_COLOR_CONTROL_CURRENT_Y`
      - `ATTR_COLOR_CONTROL_COLOR_TEMPERATURE`
      - `DEVICE_ID_COLOR_DIMMABLE_LIGHT`.
  - `python/uzigbee/__init__.py`
    - exported `ColorLight` and new color constants.
- High-level devices:
  - `python/uzigbee/devices.py`
    - added `ColorLight`:
      - `get_xy()`, `set_xy(x, y, check=False)`, `on_xy_change(callback)`
      - `get_color_temperature()`, `set_color_temperature(value, check=False)`,
        `color_temperature` property,
        `on_color_temperature_change(callback)`.
- Tests:
  - updated `tests/test_devices_api.py`
  - updated `tests/test_core_api.py`
  - updated `tests/test_import.py`
  - added `tests/hil_color_light_smoke.py`.

Validation:
- Host tests:
  - `python -m pytest tests/test_devices_api.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py tests/test_zcl.py -q`
  - result: `17 passed`.
- WSL build:
  - output dir: `build-ESP32_GENERIC_C6-uzigbee-step15a`
  - `micropython.bin`: `0x2295e0`
  - app partition: `0x3eb000`
  - free: `0x1c1a20` (~45%).
- Flash:
  - target detected as ESP32-C6 on `COM3`
  - flash to `COM3`: PASS.
- HIL on device:
  - `tests/hil_color_light_smoke.py`: PASS
    - XY set/get verified (`11000`, `22000`)
    - event queue counters healthy (`dropped_* == 0`)
    - color temperature optional path detected as unsupported on current default config (`OSError 261`), test handles this explicitly.
  - Regression PASS:
    - `tests/hil_basic_identity_smoke.py`
    - `tests/hil_attr_smoke.py`
    - `tests/hil_attr_callback_smoke.py`
    - `tests/hil_endpoint_smoke.py`
    - `tests/hil_onoff_light_smoke.py`
    - `tests/hil_signal_smoke.py`
    - `tests/hil_z2m_validate_smoke.py`
    - `tests/hil_z2m_setters_smoke.py`
    - `tests/hil_light_device_smoke.py`
    - `tests/hil_dimmable_light_smoke.py`.

Operational notes:
- `COM5` was not present during this session; detected C6 test target was `COM3`.
- `mpremote` can occasionally fail raw-REPL entry right after hard reset/flash; retry (`resume`) is reliable.
