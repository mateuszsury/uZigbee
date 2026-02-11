# Progress Report: 2026-02-09 Step 42

## Scope
- Added composed descriptor discovery helper in Python API:
  - `uzigbee.core.ZigbeeStack.discover_node_descriptors(...)`
- Goal: close open `ZDO commands` gap with one orchestrated call that runs:
  - Active Endpoint request
  - Node Descriptor request
  - Simple Descriptor requests per endpoint
  - Power Descriptor request

## Implementation
- Python core (`python/uzigbee/core.py`):
  - Added portable timing helpers for MicroPython/CPython:
    - `_ticks_ms`, `_ticks_add`, `_ticks_diff`, `_sleep_ms`
  - Added generic polling helper:
    - `ZigbeeStack._poll_snapshot(...)`
  - Added composed workflow:
    - `ZigbeeStack.discover_node_descriptors(dst_short_addr, endpoint_ids=None, include_power_desc=True, include_green_power=False, timeout_ms=5000, poll_ms=200, strict=True)`
  - Behavior:
    - auto fetch of active endpoints when `endpoint_ids` is not provided
    - optional skip of Green Power endpoint `242` (default skip)
    - strict mode raises `ZigbeeError` on timeout
    - non-strict mode collects errors in `result["errors"]`
- Tests:
  - `tests/test_core_api.py`:
    - `test_discover_node_descriptors_flow`
    - `test_discover_node_descriptors_timeout_strict`
    - `test_discover_node_descriptors_non_strict_collects_errors`
  - New HIL test:
    - `tests/hil_discover_node_descriptors_smoke.py`

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py`
  - Result: `53 passed`
- WSL build:
  - Build dir: `build-ESP32_GENERIC_C6-uzigbee-step42a`
  - App size: `0x28e2f0`
  - Free in app partition (`0x3eb000`): `0x15cd10` (~35%)
- Flash:
  - Target: ESP32-C6 on `COM3`
  - Status: success
- HIL batch:
  - `tests/hil_discover_node_descriptors_smoke.py` -> PASS
  - `tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - `tests/hil_active_endpoints_read_smoke.py` -> PASS
  - `tests/hil_node_desc_read_smoke.py` -> PASS
  - `tests/hil_simple_desc_read_smoke.py` -> PASS
  - `tests/hil_power_desc_read_smoke.py` -> PASS
  - `tests/hil_binding_table_read_smoke.py` -> PASS

## Runtime Snapshot (Step 42)
- `uzigbee.hil.discover.result {'endpoint_ids': [1], 'active_endpoints': {'count': 2, 'endpoints': [1, 242], 'status': 0}, 'node_descriptor': {...}, 'short_addr': 0, 'power_descriptor': {...}, 'errors': [], 'simple_descriptors': [{'endpoint': 1, 'snapshot': {...}}]}`

## Notes
- This step marks the `ZDO commands (device discovery, descriptor requests)` checkbox as complete in `plan.md`.
- Remaining advanced items in Phase 4 are now mostly outside descriptor discovery (scene/security/OTA/gateway/etc.).
