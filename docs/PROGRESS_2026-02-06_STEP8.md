# Progress 2026-02-06 Step 8

Scope:
- Implement the next minimal Faza 1 milestone from `plan.md`:
  - typed callback bridge for `attribute change -> Python`.
- Complete build/flash/HIL validation on device `COM5`.

Implemented:
- `c_module/uzb_core.h`
  - Added typed event model:
    - `uzb_event_type_t`
    - `uzb_attr_set_event_t`
    - `uzb_event_t`
  - Replaced queue pop API with generic:
    - `uzb_core_pop_event(...)`.
- `c_module/uzb_core.c`
  - Extended static queue to carry both app signals and attribute events.
  - Added reusable scalar decode helper for ZCL attribute payloads.
  - Added Zigbee core action handler registration on successful device registration:
    - `esp_zb_core_action_handler_register(...)`.
  - Added handling for `ESP_ZB_CORE_SET_ATTR_VALUE_CB_ID`:
    - enqueue typed attribute event (no Python allocation in Zigbee task).
  - Extended local `set_attribute(...)` path to emit typed attribute events after successful write.
- `c_module/mod_uzigbee.c`
  - Added GC-rooted attribute callback pointer.
  - Added new APIs:
    - `_uzigbee.on_attribute(callback|None)`
    - `_uzigbee.set_attribute_callback(callback|None)`
  - Extended scheduler dispatch to route:
    - app signal events -> signal callback
    - attribute events -> attribute callback
  - Attribute callback args:
    - `(endpoint, cluster_id, attr_id, value, attr_type, status)`.
- `python/uzigbee/core.py`
  - Added:
    - `ZigbeeStack.on_attribute(callback=None)`
    - `ZigbeeStack.set_attribute_callback(callback=None)`.
- `tests/test_core_api.py`
  - Extended fake backend and assertions for new attribute callback wrapper APIs.
- `tests/hil_attr_callback_smoke.py`
  - New HIL smoke script for attribute callback path.
- Build system robustness fix:
  - `third_party/micropython-esp32/py/mkrules.cmake`
  - `third_party/micropython-esp32/py/mkrules.mk`
  - Forced recursive `mpy-cross` build to use `BUILD=build` and blank `FROZEN_MANIFEST` to avoid inherited variant build flags breaking `mpy-cross`.

Host validation:
- `python -m pytest tests/test_core_api.py -q` -> `2 passed`.

Build/flash validation:
- WSL build (`ESP32_GENERIC_C6`, `build-ESP32_GENERIC_C6-uzigbee-step8a`) successful.
- Image/partition check:
  - `micropython.bin`: `0x216d00`
  - app partition: `0x3eb000`
  - free: `0x1d4300` (~47%)
- Flash to `COM5`: PASS.

Device validation (`COM5`):
- API presence:
  - `ZigbeeStack.on_attribute`: `True`
  - `ZigbeeStack.set_attribute_callback`: `True`
- HIL tests:
  - `python -m mpremote connect COM5 soft-reset run tests/hil_attr_smoke.py` -> PASS
  - `python -m mpremote connect COM5 soft-reset run tests/hil_attr_callback_smoke.py` -> PASS
    - observed callback values: `True`, `False`
  - `python -m mpremote connect COM5 soft-reset run tests/hil_signal_smoke.py` -> PASS
  - `python -m mpremote connect COM5 soft-reset run tests/hil_endpoint_smoke.py` -> PASS
  - `python -m mpremote connect COM5 soft-reset run tests/hil_onoff_light_smoke.py` -> PASS

Notes:
- `mpremote` on `COM5` must be strictly single-process and sequential.
- Immediately after flashing, first raw REPL entry may fail once; a retry resolves it.
