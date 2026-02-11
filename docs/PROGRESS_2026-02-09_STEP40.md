# Progress Report: 2026-02-09 Step 40

## Scope
- Added ZDO Simple Descriptor read path:
  - `_uzigbee.request_simple_descriptor(dst_short_addr, endpoint)`
  - `_uzigbee.get_simple_descriptor_snapshot()`
  - `uzigbee.core.ZigbeeStack.request_simple_descriptor(...)`
  - `uzigbee.core.ZigbeeStack.get_simple_descriptor_snapshot()`

## Implementation
- C core (`c_module/uzb_core.c`, `c_module/uzb_core.h`):
  - Added lock-protected snapshot for `Simple_Desc_rsp`.
  - Added bounded cluster storage (`UZB_SIMPLE_DESC_MAX_CLUSTERS = 16`) for input/output cluster lists.
  - Added API:
    - `uzb_core_request_simple_descriptor(...)`
    - `uzb_core_get_simple_descriptor_snapshot(...)`
- MicroPython C bridge (`c_module/mod_uzigbee.c`):
  - Added wrappers:
    - `request_simple_descriptor(...)`
    - `get_simple_descriptor_snapshot()`
- Python API (`python/uzigbee/core.py`):
  - Added methods:
    - `request_simple_descriptor(dst_short_addr, endpoint)`
    - `get_simple_descriptor_snapshot()` returning `{"status", "addr", "simple_desc"}`

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py`
  - Result: `49 passed`
- WSL build:
  - Build dir: `build-ESP32_GENERIC_C6-uzigbee-step40a`
  - App size: `0x28b8f0`
  - Free in app partition (`0x3eb000`): `0x15f710` (~35%)
- Flash:
  - Target: ESP32-C6 on `COM3`
  - Status: success
- HIL:
  - `tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - `tests/hil_active_endpoints_read_smoke.py` -> PASS
  - `tests/hil_node_desc_read_smoke.py` -> PASS
  - `tests/hil_simple_desc_read_smoke.py` -> PASS
  - `tests/hil_binding_table_read_smoke.py` -> PASS

## Runtime Snapshot (Step 40)
- `uzigbee.hil.simple_desc.snapshot {'simple_desc': {'device_version': 0, 'device_id': 260, 'input_clusters': [0, 3], 'output_clusters': [4, 5, 6, 3, 8], 'endpoint': 1, 'profile_id': 260}, 'addr': 0, 'status': 0}`

## Notes
- ZDO discovery read paths now include:
  - Mgmt_Bind
  - Active Endpoint
  - Node Descriptor
  - Simple Descriptor
- Main task `ZDO commands (device discovery, descriptor requests)` remains open for additional helpers/workflows (e.g., composed discovery flow and further descriptor handling).
