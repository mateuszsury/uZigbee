# Progress 2026-02-06 Step 6

Scope:
- Implement the next minimal Faza 1 item: On/Off cluster endpoint path.

Implemented:
- `c_module/uzb_core.h`
  - Added `uzb_core_create_on_off_light_endpoint(uint8_t endpoint)`.
- `c_module/uzb_core.c`
  - Added endpoint kind tracking:
    - generic endpoint path
    - HA On/Off light endpoint path
  - Implemented `uzb_core_create_on_off_light_endpoint()`.
  - Extended `uzb_core_register_device()` to register either:
    - generic basic+identify endpoint (existing path), or
    - `esp_zb_on_off_light_ep_create()` endpoint using `ESP_ZB_DEFAULT_ON_OFF_LIGHT_CONFIG()`.
  - Kept Zigbee lock requirement for all registration operations.
- `c_module/mod_uzigbee.c`
  - Added `_uzigbee.create_on_off_light(endpoint=1)`.
- `python/uzigbee/core.py`
  - Added `ZigbeeStack.create_on_off_light(endpoint_id=1)`.
  - Fallback to `create_endpoint(...DEVICE_ID_ON_OFF_LIGHT...)` when older firmware lacks new symbol.
- `tests/test_core_api.py`
  - Extended fake backend and wrapper assertion for `create_on_off_light`.
- `tests/hil_onoff_light_smoke.py`
  - Added HIL smoke script for On/Off light endpoint path.

Host validation:
- `python -m pytest tests/test_core_api.py -q` -> `2 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step6a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x211640`
  - app partition: `0x240000`
  - free: `0x2e9c0` (~8%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `_uzigbee.create_on_off_light`: `True`
  - `ZigbeeStack.create_on_off_light`: `True`
- On/Off endpoint smoke:
  - `python -m mpremote connect COM5 run tests/hil_onoff_light_smoke.py`
  - PASS (`dropped_queue_full=0`, `dropped_schedule_fail=0`, `dispatched>0`)
- Regression smoke:
  - `tests/hil_endpoint_smoke.py`: PASS
  - `tests/hil_signal_smoke.py`: PASS

Notes:
- `COM5` must remain single-process for `mpremote`; parallel calls lock the port.
- With this step firmware free app margin decreased to ~8%; keep tracking growth each step.
