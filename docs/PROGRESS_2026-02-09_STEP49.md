# Progress - 2026-02-09 - Step 49 (Phase 4.5.1)

## Scope
- Start Phase 4.5 implementation: high-level coordinator/network API scaffold.
- Keep full compatibility with existing `ZigbeeStack` low-level API.

## Code Changes
- Added `python/uzigbee/network.py`:
  - `Coordinator`
  - `DeviceRegistry`
  - `DiscoveredDevice`
  - `DeviceReadProxy`
  - `DeviceControlProxy`
- Added automation behavior:
  - auto-discovery trigger on join-related signals (`device_announce`, `device_update`, `device_authorized`),
  - descriptor-based endpoint/feature inference,
  - bounded registry storage,
  - read-through state cache + command-level optimistic updates.
- Updated exports:
  - `python/uzigbee/__init__.py` now exports:
    - module `network`
    - `Coordinator`, `DeviceRegistry`, `DiscoveredDevice`

## Tests
- New host tests:
  - `tests/test_network_api.py`
    - discovery mapping,
    - device read/control path,
    - attribute cache update,
    - auto-discovery on join signal.
- Updated host import checks:
  - `tests/test_import.py` includes `network` + exported types.
- New HIL smoke:
  - `tests/hil_network_coordinator_smoke.py`

## Validation
- Host:
  - `python -m pytest tests/test_network_api.py tests/test_import.py tests/test_core_api.py tests/test_ota_api.py tests/test_example_coordinator_web_demo.py -q`
  - Result: `38 passed`.
- Firmware build (WSL):
  - `build-ESP32_GENERIC_C6-uzigbee-step49a`
  - `micropython.bin`: `0x2dc100`
  - free app space: `0x10ef00` (~27%)
- Flash:
  - ESP32-C6 on `COM3` flashed successfully using `@flash_args`.
- HIL:
  - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_network_coordinator_smoke.py tests/hil_zigbee_bridge_addr_smoke.py tests/hil_ota_capability_fallback_smoke.py --retries 3 --timeout 360`
  - Result: PASS (`3/3`).

## Notes
- In minimal smoke context, `permit_join` may return `OSError(-1)`; this is accepted in the test and documented.
- For full multi-device cache precision, next steps in Phase 4.5 require C-bridge payload extension with source short address in attribute callbacks.
