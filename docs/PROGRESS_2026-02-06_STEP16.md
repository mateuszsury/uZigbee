# Progress 2026-02-06 Step 16

Scope:
- Continue Faza 3 with the next small complete increment:
  - add `Switch` foundation (`OnOffSwitch` endpoint + outgoing On/Off commands).
- Keep full validation:
  - host unit tests
  - WSL build
  - flash + HIL on hardware.

Implemented:
- C bridge / core:
  - `c_module/uzb_core.h`
    - added:
      - `uzb_core_create_on_off_switch_endpoint(...)`
      - `uzb_core_send_on_off_cmd(...)`.
  - `c_module/uzb_core.c`
    - added endpoint kind `UZB_ENDPOINT_KIND_ON_OFF_SWITCH`.
    - added `uzb_core_create_on_off_switch_endpoint(...)` (device id `0x0000`).
    - added register path using
      `esp_zb_on_off_switch_ep_create(...)`.
    - added `uzb_core_send_on_off_cmd(...)`:
      - validates cmd id (`OFF`/`ON`/`TOGGLE`)
      - validates endpoints
      - acquires/releases Zigbee lock around `esp_zb_zcl_on_off_cmd_req(...)`.
  - `c_module/mod_uzigbee.c`
    - new API:
      - `_uzigbee.create_on_off_switch(...)`
      - `_uzigbee.send_on_off_cmd(...)`
    - new constants:
      - `DEVICE_ID_ON_OFF_SWITCH`
      - `CMD_ON_OFF_OFF`
      - `CMD_ON_OFF_ON`
      - `CMD_ON_OFF_TOGGLE`.
- Python core/API:
  - `python/uzigbee/core.py`
    - added:
      - `ZigbeeStack.create_on_off_switch(...)`
      - `ZigbeeStack.send_on_off_cmd(...)`
    - exported constants above.
  - `python/uzigbee/__init__.py`
    - exported `Switch` and switch/on-off command constants.
- High-level devices:
  - `python/uzigbee/devices.py`
    - added `Switch` class:
      - `provision()`
      - `validate_interview()`
      - `send_on(...)`, `send_off(...)`, `toggle(...)`.
- Tests:
  - updated `tests/test_core_api.py`
  - updated `tests/test_devices_api.py`
  - updated `tests/test_import.py`
  - added `tests/hil_switch_smoke.py`.

Validation:
- Host tests:
  - `python -m pytest tests/test_devices_api.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py tests/test_zcl.py -q`
  - result: `19 passed`.
- WSL build:
  - output dir: `build-ESP32_GENERIC_C6-uzigbee-step16a`
  - `micropython.bin`: `0x230020`
  - app partition: `0x3eb000`
  - free: `0x1bafe0` (~44%).
- Flash:
  - target detected as ESP32-C6 on `COM3`
  - flash to `COM3`: PASS.
- HIL on device:
  - new:
    - `tests/hil_switch_smoke.py`: PASS
  - regression:
    - `tests/hil_light_device_smoke.py`: PASS
    - `tests/hil_dimmable_light_smoke.py`: PASS
    - `tests/hil_color_light_smoke.py`: PASS
    - `tests/hil_z2m_validate_smoke.py`: PASS
    - `tests/hil_basic_identity_smoke.py`: PASS.

Operational notes:
- `COM5` not available in this session; active ESP32-C6 test target was `COM3`.
- `mpremote` intermittently hangs or fails raw-REPL entry after reset/flash; sequential single-process execution with retry/recover remains required.
