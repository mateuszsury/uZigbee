# Progress Report: 2026-02-09 Step 41

## Scope
- Added ZDO Power Descriptor read path:
  - `_uzigbee.request_power_descriptor(dst_short_addr)`
  - `_uzigbee.get_power_descriptor_snapshot()`
  - `uzigbee.core.ZigbeeStack.request_power_descriptor(...)`
  - `uzigbee.core.ZigbeeStack.get_power_descriptor_snapshot()`

## Implementation
- C core (`c_module/uzb_core.c`, `c_module/uzb_core.h`):
  - Added lock-protected snapshot for `Power_Desc_rsp`.
  - Added API:
    - `uzb_core_request_power_descriptor(...)`
    - `uzb_core_get_power_descriptor_snapshot(...)`
  - Snapshot fields:
    - `status`, `addr`
    - `current_power_mode`
    - `available_power_sources`
    - `current_power_source`
    - `current_power_source_level`
- MicroPython C bridge (`c_module/mod_uzigbee.c`):
  - Added wrappers:
    - `request_power_descriptor(...)`
    - `get_power_descriptor_snapshot()`
- Python API (`python/uzigbee/core.py`):
  - Added methods:
    - `request_power_descriptor(dst_short_addr)`
    - `get_power_descriptor_snapshot()` returning `{"status", "addr", "power_desc"}`

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py`
  - Result: `50 passed`
- WSL build:
  - Build dir: `build-ESP32_GENERIC_C6-uzigbee-step41a`
  - App size: `0x28daa0`
  - Free in app partition (`0x3eb000`): `0x15d560` (~35%)
- Flash:
  - Target: ESP32-C6 on `COM3`
  - Status: success
- HIL:
  - `tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - `tests/hil_active_endpoints_read_smoke.py` -> PASS
  - `tests/hil_node_desc_read_smoke.py` -> PASS
  - `tests/hil_simple_desc_read_smoke.py` -> PASS
  - `tests/hil_power_desc_read_smoke.py` -> PASS
  - `tests/hil_binding_table_read_smoke.py` -> PASS

## Runtime Snapshot (Step 41)
- `uzigbee.hil.power_desc.snapshot {'power_desc': {'current_power_mode': 0, 'available_power_sources': 0, 'current_power_source': 0, 'current_power_source_level': 0}, 'addr': 0, 'status': 0}`

## Notes
- ZDO discovery read paths now include:
  - Mgmt_Bind
  - Active Endpoint
  - Node Descriptor
  - Simple Descriptor
  - Power Descriptor
- Main task `ZDO commands (device discovery, descriptor requests)` remains open for composed discovery workflows and additional helpers.
