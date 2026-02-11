# Progress 2026-02-06 Step 11

Scope:
- Implement next small `plan.md` Z2M helper milestone:
  - `z2m.set_model_id(model)`
  - `z2m.set_manufacturer(name)`
- Keep step fully validated (build + flash + HIL on `COM5`).

Implemented:
- `python/uzigbee/z2m.py`
  - Added:
    - `set_identity(...)`
    - `set_model_id(...)`
    - `set_manufacturer(...)`
  - Added lightweight per-endpoint pending cache for identity values.
  - Setters preserve existing values (cache/live readback/defaults), then call `ZigbeeStack.set_basic_identity(...)`.
- Tests:
  - `tests/test_z2m_api.py`
    - Added setter tests:
      - preserve identity across updates
      - merge with live values when available
  - `tests/hil_z2m_setters_smoke.py`
    - New HIL smoke for `set_model_id` + `set_manufacturer` + `set_identity`.
- Docs:
  - `docs/API.md` updated with new `uzigbee.z2m` setter helpers.
  - `docs/BUILD.md` updated with new HIL command and latest image size marker.

Host validation:
- `python -m pytest tests/test_z2m_api.py tests/test_core_api.py -q` -> `6 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step11a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x21fc10`
  - app partition: `0x3eb000`
  - free: `0x1cb3f0` (~46%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `uzigbee.z2m.set_model_id`: `True`
  - `uzigbee.z2m.set_manufacturer`: `True`
  - `uzigbee.z2m.set_identity`: `True`
- New HIL:
  - `tests/hil_z2m_setters_smoke.py`: PASS
- Regression HIL:
  - `tests/hil_z2m_validate_smoke.py`: PASS
  - `tests/hil_basic_identity_smoke.py`: PASS
  - `tests/hil_attr_smoke.py`: PASS
  - `tests/hil_attr_callback_smoke.py`: PASS
  - `tests/hil_signal_smoke.py`: PASS
  - `tests/hil_endpoint_smoke.py`: PASS
  - `tests/hil_onoff_light_smoke.py`: PASS

Notes:
- `COM5` access must stay single-process; parallel `mpremote` calls collide.
- First raw REPL entry after hard reset may fail once; retry succeeds.
