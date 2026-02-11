# Progress 2026-02-06 Step 17

Scope:
- Complete `DimmableSwitch` as the next small full increment in Faza 3.
- Keep full validation:
  - host unit tests
  - WSL build
  - flash + HIL on hardware.

Implemented:
- C bridge / core:
  - `c_module/uzb_core.h`
    - added:
      - `uzb_core_create_dimmable_switch_endpoint(...)`
      - `uzb_core_send_level_cmd(...)`.
  - `c_module/uzb_core.c`
    - added endpoint kind `UZB_ENDPOINT_KIND_DIMMABLE_SWITCH`.
    - added endpoint creator for dimmable switch with level-control client cluster.
    - added level command sender (MoveToLevel / MoveToLevelWithOnOff) with:
      - argument validation
      - zigbee lock acquire/release around send call.
  - `c_module/mod_uzigbee.c`
    - new API:
      - `_uzigbee.create_dimmable_switch(...)`
      - `_uzigbee.send_level_cmd(...)`
    - new constants:
      - `DEVICE_ID_LEVEL_CONTROL_SWITCH`
      - `DEVICE_ID_DIMMER_SWITCH`
      - `CMD_LEVEL_MOVE_TO_LEVEL`
      - `CMD_LEVEL_MOVE_TO_LEVEL_WITH_ONOFF`.
- Python core/API:
  - `python/uzigbee/core.py`
    - added:
      - `ZigbeeStack.create_dimmable_switch(...)`
      - `ZigbeeStack.send_level_cmd(...)`
    - exported new switch/level constants.
  - `python/uzigbee/__init__.py`
    - exported `DimmableSwitch` and new constants.
- High-level devices:
  - `python/uzigbee/devices.py`
    - added `DimmableSwitch` class:
      - `provision()`
      - `send_level(...)`
      - `set_brightness(...)`.
- Tests:
  - updated `tests/test_core_api.py`
  - updated `tests/test_devices_api.py`
  - updated `tests/test_import.py`
  - added `tests/hil_dimmable_switch_smoke.py`.

Validation:
- Host tests:
  - `python -m pytest tests/test_devices_api.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py tests/test_zcl.py -q`
  - result: `21 passed`.
- WSL build:
  - output dir: `build-ESP32_GENERIC_C6-uzigbee-step17a`
  - `micropython.bin`: `0x238310`
  - app partition: `0x3eb000`
  - free: `0x1b2cf0` (~43%).
- Flash:
  - target detected as ESP32-C6 on `COM3`
  - flash to `COM3`: PASS.
- HIL on device:
  - new:
    - `tests/hil_dimmable_switch_smoke.py`: PASS
  - regression:
    - `tests/hil_switch_smoke.py`: PASS
    - `tests/hil_light_device_smoke.py`: PASS
    - `tests/hil_dimmable_light_smoke.py`: PASS
    - `tests/hil_color_light_smoke.py`: PASS
    - `tests/hil_basic_identity_smoke.py`: PASS
    - `tests/hil_z2m_validate_smoke.py`: PASS
    - `tests/hil_z2m_setters_smoke.py`: PASS
    - `tests/hil_signal_smoke.py`: PASS
    - `tests/hil_endpoint_smoke.py`: PASS
    - `tests/hil_onoff_light_smoke.py`: PASS
    - `tests/hil_attr_smoke.py`: PASS
    - `tests/hil_attr_callback_smoke.py`: PASS.

Operational notes:
- `COM5` was not present in this session; active ESP32-C6 test target was `COM3`.
- `mpremote` on `COM3` is reliable in sequential single-process mode with `resume`.
- `soft-reset` can intermittently hang while entering raw REPL right after flash or previous runs; retry/recover remains required.
