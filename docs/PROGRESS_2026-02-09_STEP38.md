# Progress Report: 2026-02-09 Step 38

## Scope
- Extended ZDO discovery support with Active Endpoint request path:
  - `_uzigbee.request_active_endpoints(dst_short_addr)`
  - `_uzigbee.get_active_endpoints_snapshot()`
  - `uzigbee.core.ZigbeeStack.request_active_endpoints(...)`
  - `uzigbee.core.ZigbeeStack.get_active_endpoints_snapshot()`

## Implementation
- C core (`c_module/uzb_core.c`, `c_module/uzb_core.h`):
  - Added bounded Active Endpoint snapshot (`UZB_ACTIVE_EP_MAX_ENDPOINTS = 16`).
  - Added callback for `esp_zb_zdo_active_ep_req(...)` that stores response to static snapshot.
  - Added API:
    - `uzb_core_request_active_endpoints(...)`
    - `uzb_core_get_active_endpoints_snapshot(...)`
  - Added lock-protected reset of snapshot on startup and before each request.
- MicroPython C bridge (`c_module/mod_uzigbee.c`):
  - Added:
    - `request_active_endpoints(...)`
    - `get_active_endpoints_snapshot()`
- Python API (`python/uzigbee/core.py`):
  - Added:
    - `request_active_endpoints(dst_short_addr)`
    - `get_active_endpoints_snapshot() -> {"status", "count", "endpoints"}`

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py`
  - Result: `47 passed`
- WSL build (isolated ESP-IDF 5.3.2 env):
  - Build dir: `build-ESP32_GENERIC_C6-uzigbee-step38a`
  - App size: `0x285ac0`
  - Free in app partition (`0x3eb000`): `0x165540` (~36%)
- Flash:
  - Target: ESP32-C6 on `COM3`
  - Status: success
- HIL:
  - `tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - `tests/hil_bind_cmd_smoke.py` -> PASS
  - `tests/hil_binding_table_read_smoke.py` -> PASS
  - `tests/hil_active_endpoints_read_smoke.py` -> PASS

## Runtime Snapshot (Step 38)
- `uzigbee.hil.bridge.ieee_api 644c4efeffca4c40`
- `uzigbee.hil.active_ep.snapshot {'count': 2, 'endpoints': [1, 242], 'status': 0}`

## Notes
- ZDO discovery now has read paths for:
  - Mgmt_Bind response
  - Active Endpoint response
- Full `ZDO commands (device discovery, descriptor requests)` remains open in `plan.md` (node/simple descriptor paths still pending).
