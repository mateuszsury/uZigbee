# Progress - 2026-02-09 - Step 45

## Scope
- Closed Phase 4 item: `Custom clusters (manufacturer-specific)`.
- Added end-to-end path:
  - C core (`uzb_core_*`) already prepared in previous step.
  - MicroPython C bridge (`_uzigbee`) wiring.
  - Python `uzigbee.core` wrappers.
  - Python helper module `uzigbee.custom`.
  - Host tests + HIL test on device (`COM3`).

## Code Changes
- `c_module/mod_uzigbee.c`
  - Added wrappers:
    - `clear_custom_clusters()`
    - `add_custom_cluster(...)`
    - `add_custom_attr(...)`
    - `send_custom_cmd(...)`
  - Added optional payload parser for bytes-like `payload`.
  - Exported constants:
    - `CUSTOM_CLUSTER_ID_MIN`
    - `ATTR_ACCESS_READ_ONLY`
    - `ATTR_ACCESS_WRITE_ONLY`
    - `ATTR_ACCESS_READ_WRITE`
    - `ATTR_ACCESS_REPORTING`
    - `ATTR_ACCESS_SCENE`
    - `CMD_DIRECTION_TO_SERVER`
    - `CMD_DIRECTION_TO_CLIENT`
- `python/uzigbee/core.py`
  - Added constants mirroring `_uzigbee` values/fallbacks.
  - Added `ZigbeeStack` methods:
    - `clear_custom_clusters`
    - `add_custom_cluster`
    - `add_custom_attr`
    - `send_custom_cmd`
- `python/uzigbee/custom.py`
  - Added helper API:
    - `add_custom_cluster(stack, cluster_id, attrs=(), cluster_role=...)`
    - `send_custom_cmd(stack, dst_short_addr, cluster_id, custom_cmd_id, payload=None, ...)`
- `python/uzigbee/__init__.py`
  - Exported new constants.
  - Exported module `custom`.
- Tests:
  - `tests/test_core_api.py` custom wrapper coverage.
  - `tests/test_custom_api.py` helper module coverage.
  - `tests/test_import.py` import/constant checks.
  - `tests/hil_custom_cluster_smoke.py` new device smoke.
- Docs:
  - `docs/API.md` updated with Step 45 API surface.
  - `docs/BUILD.md` updated with HIL command and new size line.
  - `plan.md` marked custom clusters as done and added Step 45 log line.

## Validation
- Host unit tests:
  - `python -m pytest tests/test_import.py tests/test_core_api.py tests/test_custom_api.py -q`
  - Result: `25 passed`.
- Build (WSL, isolated ESP-IDF env):
  - `build-ESP32_GENERIC_C6-uzigbee-step45a`
  - `micropython.bin` size: `0x2d2770`
  - Free app space: `0x118890` (~28%).
- Flash:
  - Flashed successfully to `COM3` with esptool.
- HIL regression batch:
  - `tests/hil_zigbee_bridge_addr_smoke.py` PASS
  - `tests/hil_custom_cluster_smoke.py` PASS
  - `tests/hil_security_smoke.py` PASS
  - `tests/hil_scenes_cmd_smoke.py` PASS
- Runtime API probe:
  - `mpremote` check confirmed `add_custom_cluster`, `send_custom_cmd`, and `uzigbee.custom` are present.

## Notes
- Custom cluster send path was validated in HIL against local short address `0x0000` and returned success in this run.
- RAM/flash budget remains within current maximized app partition, with ~28% app headroom after Step 45.
