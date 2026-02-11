# Progress - 2026-02-09 - Step 47

## Scope
- Add explicit OTA control capability probe so callers can gate OTA control-plane calls safely.
- Keep current OTA crash guard behavior unchanged (`ESP_ERR_NOT_SUPPORTED` / `262`).

## Code Changes
- `c_module/uzb_core.h`
  - Added declaration: `bool uzb_core_ota_client_control_supported(void);`
- `c_module/uzb_core.c`
  - Added implementation:
    - `uzb_core_ota_client_control_supported()` currently returns `false` on ESP32-C6 firmware path.
- `c_module/mod_uzigbee.c`
  - Added `_uzigbee.ota_client_control_supported() -> bool`.
- `python/uzigbee/core.py`
  - Added `ZigbeeStack.ota_client_control_supported()` with backward-compatible fallback (`False` when symbol is missing in old firmware).
- `python/uzigbee/ota.py`
  - Added helper: `is_control_supported(stack) -> bool`.
- `tests/test_core_api.py`
  - Extended fake C module and assertions for capability probe.
- `tests/test_ota_api.py`
  - Added helper-level assertion for `is_control_supported`.

## Validation
- Host tests:
  - `python -m pytest tests/test_core_api.py tests/test_ota_api.py tests/test_import.py -q`
  - Result: `24 passed`.
- Firmware build (WSL, isolated env):
  - `build-ESP32_GENERIC_C6-uzigbee-step47a`
  - `micropython.bin`: `0x2da7e0`
  - free app space: `0x110820` (~27%)
- Flash:
  - `COM3` with `@flash_args` from `build-ESP32_GENERIC_C6-uzigbee-step47a`
  - `esptool` confirms device is ESP32-C6, flash size 4MB.
- Runtime probe on device:
  - `cap_api True False False`
  - meaning: symbol exists, stack probe is `False`, helper probe is `False`.
- HIL regression on `COM3`:
  - `tests/hil_ota_client_smoke.py` PASS (expected `errno=262` for OTA control calls)
  - `tests/hil_zigbee_bridge_addr_smoke.py` PASS
  - `tests/hil_custom_cluster_smoke.py` PASS
  - `tests/hil_security_smoke.py` PASS

## Notes
- This step improves API clarity for application logic and examples: callers can now check capability first instead of handling OTA-control errors as feature detection.
- Full OTA workflow (server/client transfer and upgrade lifecycle) remains open in roadmap.
