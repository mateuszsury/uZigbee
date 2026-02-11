# Progress Step 31 (2026-02-08)

Scope:
- Implemented `Group management` from Phase 4 plan.

Implementation:
- Added C core APIs in `c_module/uzb_core.c` / `c_module/uzb_core.h`:
  - `uzb_core_send_group_add_cmd(...)`
  - `uzb_core_send_group_remove_cmd(...)`
  - `uzb_core_send_group_remove_all_cmd(...)`
- Added MicroPython bindings in `c_module/mod_uzigbee.c`:
  - `_uzigbee.send_group_add_cmd(...)`
  - `_uzigbee.send_group_remove_cmd(...)`
  - `_uzigbee.send_group_remove_all_cmd(...)`
  - exported `CLUSTER_ID_GROUPS`
- Extended `ZigbeeStack` in `python/uzigbee/core.py`:
  - `send_group_add_cmd(...)`
  - `send_group_remove_cmd(...)`
  - `send_group_remove_all_cmd(...)`
- Added Python helper module:
  - `python/uzigbee/groups.py`
  - functions: `add_group`, `remove_group`, `remove_all_groups`
- Wired high-level wrapper methods:
  - `Switch.add_to_group(...)`
  - `Switch.remove_from_group(...)`
  - `Switch.clear_groups(...)`
  - in `python/uzigbee/devices.py`
- Public API export updates:
  - `python/uzigbee/__init__.py` exports `groups`
  - added `CLUSTER_ID_GROUPS`

Tests added/updated:
- `tests/test_groups_api.py` (new)
- `tests/test_core_api.py` (group command coverage + missing API guard)
- `tests/test_devices_api.py` (Switch group helpers)
- `tests/test_import.py` (public export checks)
- `tests/hil_groups_cmd_smoke.py` (new HIL smoke)

Validation:
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_groups_api.py tests/test_devices_api.py tests/test_import.py tests/test_reporting_api.py tests/test_z2m_api.py tests/test_z2m_interview_suite.py`
  - Result: `50 passed`
- Firmware build (WSL):
  - `BUILD=build-ESP32_GENERIC_C6-uzigbee-step31a`
  - `micropython.bin` size: `0x271df0`
  - app free: `0x179210` (~38%)
- Flash:
  - flashed to `COM3` with `esptool`
- HIL (device):
  - `python -m mpremote connect COM3 resume soft-reset run tests/hil_groups_cmd_smoke.py` -> PASS
  - `python -m mpremote connect COM3 resume soft-reset run tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - IEEE readback observed through bridge:
    - `644c4efeffca4c40`

Plan status:
- Marked as done in `plan.md`:
  - `- [x] Group management`
