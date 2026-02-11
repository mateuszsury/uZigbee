# Progress Step 36 (2026-02-09)

Scope:
- Implement binding-table management primitives (bind/unbind commands) in the library API.

Implementation:
- Added C core APIs:
  - `uzb_core_send_bind_cmd(...)`
  - `uzb_core_send_unbind_cmd(...)`
  - files: `c_module/uzb_core.h`, `c_module/uzb_core.c`
- Added MicroPython C-module wrappers:
  - `_uzigbee.send_bind_cmd(...)`
  - `_uzigbee.send_unbind_cmd(...)`
  - file: `c_module/mod_uzigbee.c`
- Added Python core wrappers:
  - `ZigbeeStack.send_bind_cmd(...)`
  - `ZigbeeStack.send_unbind_cmd(...)`
  - IEEE address coercion/validation (`8-byte bytes-like`)
  - file: `python/uzigbee/core.py`
- Added tests:
  - host: `tests/test_core_api.py` updates for bind/unbind call path + missing-feature guard.
  - HIL: `tests/hil_bind_cmd_smoke.py`.

Validation:
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_example_coordinator_web_demo.py tests/test_devices_api.py tests/test_import.py`
  - result: `45 passed`
- Firmware build (WSL):
  - `build-ESP32_GENERIC_C6-uzigbee-step35a`
  - image size: `0x27fb00`, free app space: `0x16b500` (~36%).
- Flash:
  - successful to `COM3`.
- HIL:
  - `tests/hil_zigbee_bridge_addr_smoke.py` PASS
  - `tests/hil_bind_cmd_smoke.py` PASS
  - `tests/hil_last_joined_short_smoke.py` PASS

Notes:
- This step adds bind/unbind management commands.
- Full remote binding-table enumeration (`Mgmt_Bind_req` response parsing) is still a separate next step.

Plan status:
- `plan.md` updated with Step 36 execution log and binding management milestone.
