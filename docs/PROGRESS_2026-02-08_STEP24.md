# Progress 2026-02-08 - Step 24

Scope:
- close two remaining checklist items in `Faza 0` from `plan.md`:
  - RAM usage measurement after Zigbee stack startup
  - documented problems and constraints from real device runs
- keep delivery end-to-end: code + build + flash + HIL.

Implemented:
- C module (`_uzigbee`):
  - `c_module/mod_uzigbee.c`
  - added `_uzigbee.get_heap_stats() -> tuple[int, int, int, int]`
  - tuple order:
    - `free_8bit`
    - `min_free_8bit`
    - `largest_free_8bit`
    - `free_internal`
  - implementation uses:
    - `heap_caps_get_free_size(MALLOC_CAP_8BIT)`
    - `heap_caps_get_minimum_free_size(MALLOC_CAP_8BIT)`
    - `heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)`
    - `heap_caps_get_free_size(MALLOC_CAP_INTERNAL)`

- Python core API:
  - `python/uzigbee/core.py`
  - added `ZigbeeStack.heap_stats() -> dict`
  - dict keys:
    - `free_8bit`
    - `min_free_8bit`
    - `largest_free_8bit`
    - `free_internal`

- Tests:
  - `tests/test_core_api.py`
    - fake backend supports `get_heap_stats`
    - wrapper-call assertions extended for `heap_stats()`
  - new HIL:
    - `tests/hil_ram_startup_smoke.py`
    - captures `gc.mem_free()/mem_alloc()` and `_uzigbee` heap metrics over stages:
      - before init
      - after init
      - after register
      - after start (+3s)
    - validates Zigbee runtime health and IEEE/short address readback.

- Docs:
  - `docs/API.md`
    - documented `_uzigbee.get_heap_stats()` and `ZigbeeStack.heap_stats()`
  - `docs/MEMORY.md`
    - added measured RAM table + deltas + validated issues/limitations
  - `docs/BUILD.md`
    - added `tests/hil_ram_startup_smoke.py` to smoke sequence.

Build and flash:
- WSL build:
  - `BOARD=ESP32_GENERIC_C6`
  - `BUILD=build-ESP32_GENERIC_C6-uzigbee-step24a`
  - result: PASS
  - `micropython.bin = 0x250da0`
  - free app partition: `0x19a260` (~41%)
- Flash (Windows):
  - target: `COM3`
  - result: PASS

HIL on device (`COM3`):
- `tests/hil_ram_startup_smoke.py`: PASS
- `tests/hil_zigbee_bridge_addr_smoke.py`: PASS

Measured RAM baseline (`tests/hil_ram_startup_smoke.py`):
- before init:
  - `gc_free=303472`, `gc_alloc=18576`, `free_8bit=290792`
- after start (+3s):
  - `gc_free=282688`, `gc_alloc=18880`, `free_8bit=260500`
- delta (before init -> after start):
  - `gc_free=-20784`
  - `free_8bit=-30292`
- bridge validation:
  - `ieee=644c4efeffca4c40`
  - `short=0x0`
  - event queue drops: zero.

Operational findings documented:
- `mpremote soft-reset` can fail raw-REPL entry after hard reset.
- stable sequence in current setup: `resume run` on `COM3`.
- clean startup RAM measurement must run after hardware reset, not after a reused soft-reset session.

Plan updates:
- `plan.md` updated:
  - marked done:
    - `ZmierzyÄ‡ zuĹĽycie RAM po starcie stosu ZigBee`
    - `UdokumentowaÄ‡ znalezione problemy i ograniczenia`
