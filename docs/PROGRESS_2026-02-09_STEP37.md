# Progress Report: 2026-02-09 Step 37

## Scope
- Completed ZDO management read path for binding table:
  - `_uzigbee.request_binding_table(dst_short_addr, start_index=0)`
  - `_uzigbee.get_binding_table_snapshot()`
  - `uzigbee.core.ZigbeeStack.request_binding_table(...)`
  - `uzigbee.core.ZigbeeStack.get_binding_table_snapshot()`

## Implementation
- C core:
  - Added bounded snapshot storage (`UZB_BIND_TABLE_MAX_RECORDS = 8`) in `c_module/uzb_core.c`.
  - Added callback copy path from Mgmt_Bind response list into static snapshot.
  - Added API:
    - `uzb_core_request_binding_table(...)`
    - `uzb_core_get_binding_table_snapshot(...)`
  - Snapshot access is lock-protected.
- MicroPython C module:
  - Added wrappers in `c_module/mod_uzigbee.c`:
    - `request_binding_table(...)`
    - `get_binding_table_snapshot()`
- Python API:
  - Added wrappers in `python/uzigbee/core.py` with parsed dict output.

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py`
  - Result: `46 passed`
- Device flash:
  - Target: `ESP32-C6` on `COM3`
  - Image: `third_party/micropython-esp32/ports/esp32/build-ESP32_GENERIC_C6-uzigbee-step37a/micropython.bin`
  - App size: `0x283ad0`
  - Free in app partition (`0x3eb000`): `0x167530` (~36%)
- HIL tests on `COM3`:
  - `tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - `tests/hil_bind_cmd_smoke.py` -> PASS
  - `tests/hil_binding_table_read_smoke.py` -> PASS

## Runtime Snapshot (Step 37)
- IEEE readback working:
  - `uzigbee.hil.bridge.ieee_api 644c4efeffca4c40`
- Short address readback working:
  - `uzigbee.hil.bridge.short_api 0x0`
- Binding table readback working:
  - `uzigbee.hil.bind_table.snapshot {'count': 0, 'records': [], 'status': 0, 'index': 0, 'total': 0}`

## Notes
- This step adds a concrete ZDO command path but does not complete full ZDO discovery coverage yet.
- Faza 4 item `ZDO commands (device discovery, descriptor requests)` remains open in `plan.md`.
