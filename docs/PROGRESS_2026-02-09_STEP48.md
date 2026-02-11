# Progress - 2026-02-09 - Step 48

## Scope
- Add no-throw OTA fallback helpers that use capability probe first.
- Wire capability visibility into runtime example startup logs.

## Code Changes
- `python/uzigbee/ota.py`
  - Added:
    - `set_query_interval_if_supported(stack, endpoint_id=1, interval_min=5) -> bool`
    - `query_image_if_supported(stack, server_ep=1, server_addr=0x00) -> bool`
    - `stop_query_if_supported(stack) -> bool`
  - Behavior:
    - returns `False` and skips OTA control call when capability is unavailable,
    - returns `True` and executes OTA control call when capability is available.
- `examples/coordinator_web_demo.py`
  - Added startup capability log:
    - `ota control supported=<bool>`
  - Stores startup result in `self._ota_control_supported`.

## Test Changes
- `tests/test_ota_api.py`
  - Added host tests for fallback helpers in both unsupported and supported paths.
- `tests/test_example_coordinator_web_demo.py`
  - Added host test that verifies web demo startup logs OTA capability.
- `tests/hil_ota_capability_fallback_smoke.py`
  - New HIL smoke validating fallback helpers on device.

## Validation
- Host tests:
  - `python -m pytest tests/test_ota_api.py tests/test_example_coordinator_web_demo.py tests/test_core_api.py tests/test_import.py -q`
  - Result: `34 passed`.
- Firmware build (WSL, isolated env):
  - `build-ESP32_GENERIC_C6-uzigbee-step48a`
  - `micropython.bin`: `0x2da8d0`
  - free app space: `0x110730` (~27%)
- Flash:
  - `COM3` using `@flash_args` from `build-ESP32_GENERIC_C6-uzigbee-step48a`.
- HIL on `COM3`:
  - `tests/hil_ota_capability_fallback_smoke.py` PASS
  - `tests/hil_ota_client_smoke.py` PASS
  - `tests/hil_zigbee_bridge_addr_smoke.py` PASS

## Device Behavior Confirmed
- OTA capability probe remains `False` on current ESP32-C6 firmware.
- Fallback helpers return `False` and avoid `OSError(262)` in normal control flow.
- Direct OTA control calls are still guarded and return `ESP_ERR_NOT_SUPPORTED` (`262`), preserving stability.
