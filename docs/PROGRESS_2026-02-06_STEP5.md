# Progress 2026-02-06 Step 5

Scope:
- Implement the next minimal Faza 1 milestone from `plan.md`:
  - endpoint creation
  - device registration

Implemented:
- `c_module/uzb_core.h`
  - Added:
    - `uzb_core_create_endpoint(endpoint, device_id, profile_id)`
    - `uzb_core_register_device()`
- `c_module/uzb_core.c`
  - Added endpoint state (`s_endpoint_defined`, `s_device_registered`, `s_endpoint_cfg`).
  - Implemented endpoint config validation.
  - Implemented registration flow:
    - `esp_zb_ep_list_create()`
    - `esp_zb_zcl_cluster_list_create()`
    - `esp_zb_basic_cluster_create(NULL)`
    - `esp_zb_identify_cluster_create(NULL)`
    - `esp_zb_ep_list_add_ep(...)`
    - `esp_zb_device_register(...)`
  - All Zigbee SDK calls in registration path are guarded by `esp_zb_lock_acquire/release`.
- `c_module/mod_uzigbee.c`
  - Added:
    - `_uzigbee.create_endpoint(endpoint, device_id, profile_id=0x0104)`
    - `_uzigbee.register_device()`
- `python/uzigbee/core.py`
  - Added:
    - `ZigbeeStack.create_endpoint(...)`
    - `ZigbeeStack.register_device()`
  - Added constants:
    - `PROFILE_ID_ZHA = 0x0104`
    - `DEVICE_ID_ON_OFF_LIGHT = 0x0100`
- `python/uzigbee/__init__.py`
  - Re-exported `PROFILE_ID_ZHA` and `DEVICE_ID_ON_OFF_LIGHT`.
- `tests/test_core_api.py`
  - Extended fake backend and wrapper assertions for endpoint create/register.
- `tests/hil_endpoint_smoke.py`
  - Added HIL smoke for endpoint path.
  - Script tolerates `ESP_ERR_INVALID_STATE` when already configured/running (repeatable runs).

Host validation:
- `python -m pytest tests/test_core_api.py -q` -> `2 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step5a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x20ab60`
  - app partition: `0x240000`
  - free: `0x354a0` (~9%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `_uzigbee.create_endpoint`: `True`
  - `_uzigbee.register_device`: `True`
  - `ZigbeeStack.create_endpoint`: `True`
  - `ZigbeeStack.register_device`: `True`
- Endpoint/register/start smoke (inline `mpremote` exec):
  - callback events captured: `3`
  - stats: `enqueued=3`, `dispatched=3`, `dropped_queue_full=0`, `dropped_schedule_fail=0`
  - result: PASS
- Script smoke (`mpremote run tests/hil_endpoint_smoke.py`):
  - result: PASS

Notes:
- Immediate `mpremote` call after flashing can sporadically fail to enter raw REPL.
  - Sequential retry (`soft-reset` or `resume`) resolves this.
- Firmware image growth is visible after endpoint registration support; free app margin is now ~9%.
