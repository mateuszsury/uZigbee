# Progress Report: 2026-02-09 Step 39

## Scope
- Added ZDO Node Descriptor read path:
  - `_uzigbee.request_node_descriptor(dst_short_addr)`
  - `_uzigbee.get_node_descriptor_snapshot()`
  - `uzigbee.core.ZigbeeStack.request_node_descriptor(...)`
  - `uzigbee.core.ZigbeeStack.get_node_descriptor_snapshot()`

## Implementation
- C core (`c_module/uzb_core.c`, `c_module/uzb_core.h`):
  - Added lock-protected static snapshot for node descriptor response.
  - Added callback wiring for `esp_zb_zdo_node_desc_req(...)`.
  - Added API:
    - `uzb_core_request_node_descriptor(...)`
    - `uzb_core_get_node_descriptor_snapshot(...)`
- MicroPython C bridge (`c_module/mod_uzigbee.c`):
  - Added wrapper functions:
    - `request_node_descriptor(...)`
    - `get_node_descriptor_snapshot()`
- Python API (`python/uzigbee/core.py`):
  - Added methods:
    - `request_node_descriptor(dst_short_addr)`
    - `get_node_descriptor_snapshot()` returning `{"status", "addr", "node_desc"}`

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py`
  - Result: `48 passed`
- WSL build:
  - Build dir: `build-ESP32_GENERIC_C6-uzigbee-step39a`
  - App size: `0x287d50`
  - Free in app partition (`0x3eb000`): `0x1632b0` (~35%)
- Flash:
  - Target: ESP32-C6 on `COM3`
  - Status: success
- HIL:
  - `tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - `tests/hil_active_endpoints_read_smoke.py` -> PASS
  - `tests/hil_node_desc_read_smoke.py` -> PASS
  - `tests/hil_binding_table_read_smoke.py` -> PASS

## Runtime Snapshot (Step 39)
- `uzigbee.hil.node_desc.short_addr 0x0`
- `uzigbee.hil.node_desc.snapshot {'node_desc': {'manufacturer_code': 4660, 'max_outgoing_transfer_size': 1613, 'desc_capability_field': 0, 'node_desc_flags': 16384, 'server_mask': 11329, 'mac_capability_flags': 15, 'max_buf_size': 108, 'max_incoming_transfer_size': 1613}, 'addr': 0, 'status': 0}`

## Notes
- ZDO discovery read paths now include:
  - Mgmt_Bind
  - Active Endpoint
  - Node Descriptor
- Global task `ZDO commands (device discovery, descriptor requests)` remains open; Simple Descriptor and related discovery helpers are the next logical step.
