# Progress Step 32 (2026-02-08)

Scope:
- Recover and stabilize HIL on `COM3` after repeated Zigbee startup crashes.
- Remove noisy Basic Cluster duplicate-attribute warning during provisioning.

Root cause:
- Crash addresses decoded with `addr2line` pointed to Zigbee reporting NVRAM path:
  - `zb_nvram_read_zcl_reporting_dataset`
  - `zb_zcl_report_attr`
  - assert in `zcl_general_commands.c:612`
- This was caused by stale/corrupted persisted Zigbee reporting state in flash (`zb_storage`/`zb_fct`).

Implementation:
- Updated `c_module/uzb_core.c`:
  - function `uzb_basic_add_or_update_attr(...)` now prefers `esp_zb_cluster_update_attr(...)` before `esp_zb_basic_cluster_add_attr(...)` when update fallback is enabled.
  - effect: avoids repeated `"add attribute ... already existed"` error logs for Basic attributes like `power_source`.
- Recovery procedure validated:
  - full `erase_flash`
  - reflash firmware images (bootloader + partition table + app)

Validation:
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py tests/test_example_coordinator_web_demo.py`
  - Result: `41 passed`
- Firmware build (WSL):
  - `BUILD=build-ESP32_GENERIC_C6-uzigbee-step32a`
  - `micropython.bin` size: `0x271dd0`
  - app free: `0x179230` (~38%)
- Flash:
  - flashed to `COM3` with `esptool` (after erase)
- HIL (device):
  - `python -m mpremote connect COM3 resume run tests/hil_zigbee_bridge_addr_smoke.py` -> PASS
  - `python -m mpremote connect COM3 resume run tests/hil_web_demo_startup_smoke.py` -> PASS
  - IEEE readback observed:
    - `644c4efeffca4c40`

Plan status:
- `plan.md` updated with execution log entry for Step 32.
