# Progress 2026-02-06 Step 10

Scope:
- Implement the next small `plan.md` milestone toward Z2M interview tooling:
  - read back Basic interview attributes from firmware
  - add Python-side Z2M interview validation helper.
- Complete build/flash/HIL validation on device `COM5`.

Implemented:
- `c_module/uzb_core.h`
  - Added API:
    - `uzb_core_get_basic_identity(endpoint, out_cfg)`.
- `c_module/uzb_core.c`
  - Added locked readback path for Basic cluster identity:
    - mandatory: `manufacturer_name`, `model_identifier`, `power_source`
    - optional: `date_code`, `sw_build_id`
  - Added robust Pascal-string decode helper for Basic attributes.
- `c_module/mod_uzigbee.c`
  - Added `_uzigbee.get_basic_identity(endpoint=1)`.
  - Returns tuple:
    - `(manufacturer_name, model_identifier, date_code, sw_build_id, power_source)`.
- `python/uzigbee/core.py`
  - Added `ZigbeeStack.get_basic_identity(endpoint_id=1) -> dict`.
- `python/uzigbee/z2m.py`
  - Added:
    - `get_interview_attrs(stack=None, endpoint_id=1)`
    - `validate(stack=None, endpoint_id=1)`
  - Validation checks:
    - required: manufacturer, model, power source range
    - warnings: missing optional `date_code` and `sw_build_id`.
- `python/uzigbee/__init__.py`
  - Re-exported `z2m` module.
- Tests:
  - `tests/test_core_api.py` updated with `get_basic_identity` wrapper checks.
  - `tests/test_z2m_api.py` added for host validation of `z2m.validate`.
  - `tests/hil_z2m_validate_smoke.py` added for HIL validation on device.
- Docs:
  - `docs/API.md` updated with `get_basic_identity` and `uzigbee.z2m` helpers.
  - `docs/BUILD.md` updated with new HIL command and latest size marker.

Host validation:
- `python -m pytest tests/test_core_api.py tests/test_z2m_api.py -q` -> `4 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step10a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x21f940`
  - app partition: `0x3eb000`
  - free: `0x1cb6c0` (~46%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `_uzigbee.get_basic_identity`: `True`
  - `ZigbeeStack.get_basic_identity`: `True`
  - `uzigbee.z2m.validate`: `True`
- New HIL:
  - `tests/hil_basic_identity_smoke.py`: PASS
  - `tests/hil_z2m_validate_smoke.py`: PASS
- Regression HIL:
  - `tests/hil_attr_smoke.py`: PASS
  - `tests/hil_attr_callback_smoke.py`: PASS
  - `tests/hil_signal_smoke.py`: PASS
  - `tests/hil_endpoint_smoke.py`: PASS
  - `tests/hil_onoff_light_smoke.py`: PASS

Notes:
- `COM5` must stay single-process; parallel `mpremote` commands collide.
- First raw-REPL attempt right after flash/reset may fail once; retry succeeds.
