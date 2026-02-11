# Progress 2026-02-06 Step 13

Scope:
- Start Faza 3 with the smallest complete high-level device milestone:
  - implement `uzigbee.devices.Light` (On/Off).
- Keep full validation workflow:
  - host unit tests
  - WSL build
  - flash and HIL on `COM5`.

Implemented:
- `python/uzigbee/devices.py`
  - Added `Light` wrapper with:
    - `provision(register=True)` for endpoint creation + identity setup + optional register
    - `validate_interview()`
    - `get_state()`, `set_state(...)`, `toggle(...)`
    - `state` property
    - `on_change(callback)` for filtered On/Off attribute events.
  - Added lightweight module-level dispatcher/registry for `Light` callbacks per stack/endpoint.
- `python/uzigbee/__init__.py`
  - Exported `Light` in public API.
- Tests:
  - Added `tests/test_devices_api.py`.
  - Updated `tests/test_import.py` (`uzigbee.Light` presence).
  - Added HIL test `tests/hil_light_device_smoke.py`.
- Docs:
  - `docs/API.md` updated with `uzigbee.devices.Light` API.
  - `docs/BUILD.md` updated with new HIL command and latest validated image size.
- Plan:
  - Kept Faza 3 combined checkbox unchecked (because `DimmableLight` and `ColorLight` are not done).
  - Added progress note in `plan.md`:
    - `[partial: Light implemented]`.

Host validation:
- `python -m pytest tests/test_devices_api.py tests/test_import.py tests/test_core_api.py tests/test_z2m_api.py tests/test_zcl.py -q`
- Result: `13 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step13a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x222130`
  - app partition: `0x3eb000`
  - free: `0x1c8ed0` (~46%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `hasattr(uzigbee, "Light")` -> `True`
- New HIL:
  - `tests/hil_light_device_smoke.py`: PASS
    - observed state transitions `True -> False`
    - callback events `[True, False]`
- Regression HIL:
  - `tests/hil_z2m_validate_smoke.py`: PASS
  - `tests/hil_z2m_setters_smoke.py`: PASS
  - `tests/hil_basic_identity_smoke.py`: PASS
  - `tests/hil_attr_smoke.py`: PASS
  - `tests/hil_attr_callback_smoke.py`: PASS
  - `tests/hil_signal_smoke.py`: PASS
  - `tests/hil_endpoint_smoke.py`: PASS
  - `tests/hil_onoff_light_smoke.py`: PASS

Operational note:
- Batch execution of many HIL tests in one mpremote process timed out twice.
- Stable method is per-test sequential invocation with retry and strict single-process access to `COM5`.
