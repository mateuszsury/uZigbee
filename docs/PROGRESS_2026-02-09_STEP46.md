# Progress - 2026-02-09 - Step 46

## Scope
- Implemented OTA client control-plane baseline in small, testable scope:
  - set OTA query interval,
  - trigger client image query,
  - stop client query.
- Kept firmware stability as first priority on ESP32-C6.

## Code Changes
- `c_module/uzb_core.h`
  - Added:
    - `uzb_core_ota_client_query_interval_set`
    - `uzb_core_ota_client_query_image_req`
    - `uzb_core_ota_client_query_image_stop`
- `c_module/uzb_core.c`
  - Added OTA client control entry points and final safety guard behavior.
  - OTA control functions currently return `ESP_ERR_NOT_SUPPORTED` (`262`) to avoid vendor stack assert (`zcl_general_commands.c:612`) observed on real hardware.
- `c_module/mod_uzigbee.c`
  - Added `_uzigbee` functions:
    - `ota_client_query_interval_set(...)`
    - `ota_client_query_image_req(...)`
    - `ota_client_query_image_stop()`
  - `server_addr` validation widened to 16-bit (`0x0000..0xFFFF`).
- `python/uzigbee/core.py`
  - Added `ZigbeeStack` methods:
    - `ota_client_query_interval_set(...)`
    - `ota_client_query_image_req(...)`
    - `ota_client_query_image_stop()`
  - Added constant:
    - `CLUSTER_ID_OTA_UPGRADE = 0x0019`
- `python/uzigbee/ota.py`
  - Added helpers:
    - `set_query_interval`
    - `query_image`
    - `stop_query`
- `python/uzigbee/__init__.py`
  - Exported `CLUSTER_ID_OTA_UPGRADE` and module `ota`.

## Tests
- Host:
  - `tests/test_core_api.py` extended for OTA wrappers.
  - `tests/test_ota_api.py` added.
  - `tests/test_import.py` extended (`uzigbee.ota`, `CLUSTER_ID_OTA_UPGRADE`).
- HIL:
  - `tests/hil_ota_client_smoke.py` added and validated with expected `errno=262` behavior.

## Validation
- Host tests passed:
  - `python -m pytest tests/test_core_api.py tests/test_ota_api.py tests/test_import.py -q`
- Final firmware build:
  - `build-ESP32_GENERIC_C6-uzigbee-step46g`
  - `micropython.bin` size: `0x2da6e0`
  - free app space: `0x110920` (~27%)
- HIL on `COM3` passed:
  - `tests/hil_zigbee_bridge_addr_smoke.py`
  - `tests/hil_custom_cluster_smoke.py`
  - `tests/hil_ota_client_smoke.py`
  - `tests/hil_security_smoke.py`

## Notes
- Hardware flash size confirmed by `esptool`: `4MB`.
- Full OTA roadmap item (server + real image transfer/upgrade lifecycle) remains open in `plan.md`.
