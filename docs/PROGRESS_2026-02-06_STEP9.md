# Progress 2026-02-06 Step 9

Scope:
- Implement the next small `plan.md` milestone for Z2M interview readiness:
  - configurable Basic cluster identity fields on endpoint registration.
- Complete build/flash/HIL validation on device `COM5`.

Implemented:
- `c_module/uzb_core.h`
  - Added Basic identity config model:
    - `uzb_basic_identity_cfg_t`
    - Pascal-style static buffers for:
      - `manufacturer` (max 32)
      - `model` (max 32)
      - `date_code` (max 16)
      - `sw_build_id` (max 16)
      - `power_source`
  - Added API:
    - `uzb_core_set_basic_identity(endpoint, cfg)`.
- `c_module/uzb_core.c`
  - Added staging of Basic identity before registration.
  - Added validation for endpoint, required fields (`manufacturer`, `model`), string lengths, and `power_source` enum range.
  - Integrated Basic identity application into `uzb_core_register_device()` before `esp_zb_device_register(...)`.
  - Implemented safe attribute apply strategy on Basic cluster:
    - `esp_zb_basic_cluster_add_attr(...)`
    - fallback `esp_zb_cluster_update_attr(...)` (no pre-register `esp_zb_zcl_get_attribute` fallback).
  - Fixed a ZBOSS assert/hang regression found during HIL:
    - removed unsafe pre-register attribute-set fallback path.
- `c_module/mod_uzigbee.c`
  - Added `_uzigbee.set_basic_identity(...)`.
  - Added Pascal string conversion helper for Python string inputs.
  - Exported new constants:
    - `CLUSTER_ID_BASIC`
    - `ATTR_BASIC_*` IDs
    - `BASIC_POWER_SOURCE_*` enum values.
- `python/uzigbee/core.py`
  - Added `ZigbeeStack.set_basic_identity(...)`.
  - Added public constants for Basic cluster IDs/attrs and power source enum.
- `python/uzigbee/__init__.py`
  - Re-exported new Basic constants.
- Tests:
  - `tests/test_core_api.py`
    - extended fake backend and wrapper assertion with `set_basic_identity(...)`.
  - `tests/hil_basic_identity_smoke.py`
    - new HIL smoke for Basic identity path, including power source readback.
- Docs:
  - `docs/API.md`: added `set_basic_identity` and related constants.
  - `docs/BUILD.md`: added `hil_basic_identity_smoke.py` to smoke commands.

Host validation:
- `python -m pytest tests/test_core_api.py -q` -> `2 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step9a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x21d8d0`
  - app partition: `0x3eb000`
  - free: `0x1cd730` (~46%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `_uzigbee.set_basic_identity`: `True`
  - `ZigbeeStack.set_basic_identity`: `True`
- New Basic identity HIL:
  - `python -m mpremote connect COM5 soft-reset run tests/hil_basic_identity_smoke.py`
  - PASS
  - observed: `power_source=1`, `identity_set=True`
- Regression HIL:
  - `tests/hil_attr_smoke.py`: PASS
  - `tests/hil_attr_callback_smoke.py`: PASS
  - `tests/hil_signal_smoke.py`: PASS
  - `tests/hil_endpoint_smoke.py`: PASS
  - `tests/hil_onoff_light_smoke.py`: PASS

Notes:
- `COM5` access must remain strictly single-process.
- Immediately after hard reset/flash, first `mpremote` raw-REPL entry may fail once; a retry succeeds.
