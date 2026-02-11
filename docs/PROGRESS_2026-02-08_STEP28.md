# Progress 2026-02-08 Step 28

## Scope
- Completed `plan.md` item from Faza 4:
  - `Attribute reporting configuration`

## What changed
- Added C core API for reporting configuration:
  - `c_module/uzb_core.h`
  - `c_module/uzb_core.c`
  - new function:
    - `uzb_core_configure_reporting(...)`
  - validates endpoint/address/interval/value ranges,
  - runs under Zigbee lock in the Zigbee API critical section,
  - sends `esp_zb_zcl_config_report_cmd_req(...)`.

- Added MicroPython binding:
  - `c_module/mod_uzigbee.c`
  - exported `_uzigbee.configure_reporting(...)`.

- Added Python wrapper API:
  - `python/uzigbee/core.py`
  - new method:
    - `ZigbeeStack.configure_reporting(...)`.

- Added host/unit coverage:
  - `tests/test_core_api.py`
  - verifies wrapper call shape and missing-firmware error path.

- Added HIL smoke:
  - `tests/hil_reporting_config_smoke.py`

- Hardened HIL runner:
  - `tools/hil_runner.py`
  - catches `subprocess.TimeoutExpired` and reports timeout per attempt
    instead of crashing the whole batch runner.

## Bug found and fixed during HIL
- Symptom:
  - ESP32-C6 crash (`Guru Meditation / Load access fault`) when calling
    `configure_reporting` for analog type `S16` with `reportable_change=None`.
- Root cause:
  - SDK path dereferenced `record.reportable_change` for analog attrs.
- Fix:
  - `c_module/uzb_core.c` now assigns a zero-threshold storage pointer for
    analog attr types when `reportable_change` is omitted.

## Validation
- Host tests:
  - `pytest -q tests/test_core_api.py tests/test_import.py tests/test_devices_api.py tests/test_z2m_api.py tests/test_z2m_interview_suite.py`
  - Result: `42 passed`

- Firmware build (WSL, isolated env, unique build dir):
  - `make -C third_party/micropython-esp32/ports/esp32 BOARD=ESP32_GENERIC_C6 BUILD=build-ESP32_GENERIC_C6-uzigbee-step28a USER_C_MODULES=<repo>/c_module/micropython.cmake FROZEN_MANIFEST=<repo>/firmware/manifest.py SDKCONFIG_DEFAULTS=<repo>/firmware/sdkconfig.defaults`
  - Result: PASS
  - size:
    - `micropython.bin = 0x2648d0`
    - free in app partition: `0x186730` (~39%)

- Flash:
  - `python -m esptool --chip esp32c6 --port COM3 ... write-flash ...`
  - Result: PASS

- Device HIL (COM3):
  - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_zigbee_bridge_addr_smoke.py tests/hil_attr_smoke.py tests/hil_reporting_config_smoke.py --retries 3 --timeout 120`
  - Result: `PASS 3 tests`
  - IEEE readback verified:
    - `uzigbee.hil.bridge.ieee_api = 644c4efeffca4c40`
    - `uzigbee.hil.bridge.short_api = 0x0`

## Plan status
- Marked done in `plan.md`:
  - `- [x] Attribute reporting configuration`
