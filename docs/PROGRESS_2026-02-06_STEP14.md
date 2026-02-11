# Progress 2026-02-06 Step 14

Scope:
- Continue Faza 3 with the next smallest complete increment:
  - add `DimmableLight` (On/Off + Level Control).
- Keep full validation:
  - host unit tests
  - WSL build
  - flash + HIL on `COM5`.

Implemented:
- C bridge / core:
  - `c_module/uzb_core.h`
    - added `uzb_core_create_dimmable_light_endpoint(...)`.
  - `c_module/uzb_core.c`
    - new endpoint kind `UZB_ENDPOINT_KIND_DIMMABLE_LIGHT`.
    - new API `uzb_core_create_dimmable_light_endpoint(...)`.
    - register path for dimmable endpoint with server clusters:
      - Basic, Identify, Groups, Scenes, On/Off, Level Control.
  - `c_module/mod_uzigbee.c`
    - added Python-facing `_uzigbee.create_dimmable_light(...)`.
    - exported constants:
      - `CLUSTER_ID_LEVEL_CONTROL`
      - `ATTR_LEVEL_CONTROL_CURRENT_LEVEL`
      - `DEVICE_ID_DIMMABLE_LIGHT`.
- Python core API:
  - `python/uzigbee/core.py`
    - added `ZigbeeStack.create_dimmable_light(...)`.
    - added constants:
      - `DEVICE_ID_DIMMABLE_LIGHT`
      - `CLUSTER_ID_LEVEL_CONTROL`
      - `ATTR_LEVEL_CONTROL_CURRENT_LEVEL`.
  - `python/uzigbee/__init__.py`
    - exported new constants and `DimmableLight`.
- High-level devices:
  - `python/uzigbee/devices.py`
    - refactored `Light.provision()` to use `_create_endpoint()` hook.
    - added `DimmableLight`:
      - `get_brightness()`
      - `set_brightness(value, check=False)` (clamp `0..254`)
      - `brightness` property
      - `on_brightness_change(callback)`.
- Tests:
  - updated `tests/test_core_api.py`
  - updated `tests/test_import.py`
  - expanded `tests/test_devices_api.py` with dimmable cases
  - added `tests/hil_dimmable_light_smoke.py`.
- Docs/plan:
  - updated `docs/API.md`
  - updated `docs/BUILD.md`
  - updated `plan.md` Faza 3 line with partial status:
    - `[partial: Light + DimmableLight implemented]`

Host validation:
- `python -m pytest tests/test_devices_api.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py tests/test_zcl.py -q`
- Result: `15 passed`.

Build/flash validation:
- WSL build successful:
  - `build-ESP32_GENERIC_C6-uzigbee-step14a`
- Size:
  - `micropython.bin`: `0x224b30`
  - app partition: `0x3eb000`
  - free: `0x1c64d0` (~45%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `hasattr(uzigbee, "DimmableLight")` -> `True`
  - `hasattr(uzigbee.ZigbeeStack(), "create_dimmable_light")` -> `True`
- New HIL:
  - `tests/hil_dimmable_light_smoke.py`: PASS
    - levels written/read: `180 -> 180`, `12 -> 12`
    - brightness callbacks: `[180, 12]`
- Regression HIL:
  - `tests/hil_light_device_smoke.py`: PASS
  - `tests/hil_z2m_validate_smoke.py`: PASS
  - `tests/hil_z2m_setters_smoke.py`: PASS
  - `tests/hil_basic_identity_smoke.py`: PASS
  - `tests/hil_attr_smoke.py`: PASS
  - `tests/hil_attr_callback_smoke.py`: PASS
  - `tests/hil_signal_smoke.py`: PASS
  - `tests/hil_endpoint_smoke.py`: PASS
  - `tests/hil_onoff_light_smoke.py`: PASS

Operational notes:
- `mpremote` may occasionally fail to enter raw REPL right after reset; reliable flow is per-test sequential invocation with retry.
- C static Zigbee state survives soft-reset patterns enough that identity-related tests may report `identity_set=False` while still passing via existing guarded assertions.
