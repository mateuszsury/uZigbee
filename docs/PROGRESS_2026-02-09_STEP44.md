# Progress Report: 2026-02-09 Step 44

## Scope
- Implemented Security command path end-to-end:
  - install-code policy controls
  - install-code management calls
  - network security + network-key management
  - Python helper module `uzigbee.security`

## Implementation
- C core (`c_module/uzb_core.c`, `c_module/uzb_core.h`):
  - added security APIs:
    - `uzb_core_set_install_code_policy(...)`
    - `uzb_core_get_install_code_policy(...)`
    - `uzb_core_set_network_security_enabled(...)`
    - `uzb_core_get_network_security_enabled(...)`
    - `uzb_core_set_network_key(...)`
    - `uzb_core_get_primary_network_key(...)`
    - `uzb_core_switch_network_key(...)`
    - `uzb_core_broadcast_network_key(...)`
    - `uzb_core_broadcast_network_key_switch(...)`
    - `uzb_core_add_install_code(...)`
    - `uzb_core_set_local_install_code(...)`
    - `uzb_core_remove_install_code(...)`
    - `uzb_core_remove_all_install_codes(...)`
  - in `uzb_core_init(...)`:
    - applies `install_code_policy`
    - applies `network_security_enabled`
    - applies optional pending preconfigured network key
- MicroPython C bridge (`c_module/mod_uzigbee.c`):
  - added wrappers for all security APIs listed above
  - added key parser for strict 16-byte network keys
  - exported install-code type constants:
    - `IC_TYPE_48`, `IC_TYPE_64`, `IC_TYPE_96`, `IC_TYPE_128`
- Python API:
  - `python/uzigbee/core.py`:
    - added `IC_TYPE_*` constants
    - added `ZigbeeStack` methods for install-code and network-key/security operations
  - `python/uzigbee/security.py`:
    - added helper functions for key normalization and common security flows
  - `python/uzigbee/__init__.py`:
    - exports `security` module and `IC_TYPE_*` constants

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_security_api.py tests/test_import.py tests/test_scenes_api.py tests/test_groups_api.py tests/test_devices_api.py tests/test_reporting_api.py`
  - Result: `62 passed`
- WSL build:
  - Build dir: `build-ESP32_GENERIC_C6-uzigbee-step44a`
  - App size: `0x2b3450`
  - Free in app partition (`0x3eb000`): `0x137bb0` (~31%)
- Flash:
  - Target: ESP32-C6 on `COM3`
  - Status: success
- HIL batch:
  - `tests/hil_security_smoke.py` -> PASS
  - `tests/hil_scenes_cmd_smoke.py` -> PASS
  - `tests/hil_groups_cmd_smoke.py` -> PASS
  - `tests/hil_discover_node_descriptors_smoke.py` -> PASS
  - `tests/hil_zigbee_bridge_addr_smoke.py` -> PASS

## Runtime Snapshot (Step 44)
- `uzigbee.hil.security.install_code_policy True`
- `uzigbee.hil.security.get_key {'ok': True, 'value': b'\\x00\\x11\\x22\\x33\\x44\\x55\\x66\\x77\\x88\\x99\\xaa\\xbb\\xcc\\xdd\\xee\\xff', 'errno': None}`
- `uzigbee.hil.security.stats {'dropped_queue_full': 0, 'dropped_schedule_fail': 0, ...}`

## Notes
- Phase 4 `Security (install codes, network key management)` is now marked complete in `plan.md`.
- Remaining Phase 4 advanced items: custom clusters, OTA, gateway mode, green power, touchlink, NCP/RCP.
