# Memory

ESP32-C6 has 512 KB SRAM and no PSRAM. Frozen modules are required to keep RAM available.

## Measurement baseline (2026-02-08, step24)

Environment:
- board: ESP32-C6 (`COM3`)
- firmware build: `build-ESP32_GENERIC_C6-uzigbee-step24a`
- stack role: coordinator
- measurement script: `tests/hil_ram_startup_smoke.py`
- startup mode: clean boot + `resume run` (no soft-reset reuse)

Captured metrics:

| Stage | `gc.mem_free()` | `gc.mem_alloc()` | `free_8bit` | `free_internal` | `largest_free_8bit` |
|---|---:|---:|---:|---:|---:|
| before init | 303472 | 18576 | 290792 | 290792 | 258048 |
| after init | 287008 | 18656 | 266344 | 266344 | 241664 |
| after register | 286912 | 18752 | 265248 | 265248 | 241664 |
| after start (+3s) | 282688 | 18880 | 260500 | 260500 | 237568 |

Deltas (before init -> after start):
- `gc.mem_free`: `-20784`
- `free_8bit`: `-30292`

Notes:
- `free_8bit` and `free_internal` are read from `_uzigbee.get_heap_stats()` (ESP-IDF heap caps).
- `gc.*` values are MicroPython heap only, so both views are tracked.

## Known issues and limitations (validated)

1. Soft-reset raw REPL instability in `mpremote`:
- after hard reset/flash, `soft-reset run` can fail to enter raw REPL.
- stable path on this setup: `python -m mpremote connect COM3 resume run <script.py>`.

2. Zigbee stack state persists across MicroPython soft reset:
- when the stack is already started, `start()` can return `ESP_ERR_INVALID_STATE`.
- for deterministic startup RAM measurement, run after hardware reset.

3. Flash size ceiling on current hardware:
- `esptool` reports `4MB` flash on tested ESP32-C6.
- current maximum app partition in this layout is `0x3EB000` (with `zb_storage` + `zb_fct` preserved).

4. Platform memory constraints remain hard:
- no PSRAM on ESP32-C6.
- coordinator mode + rich Python app + Zigbee routing still requires strict RAM budgeting.

## Runtime cache guardrail (2026-02-11, step118)

- high-level device cache is now bounded per device by `state_cache_max` (default `64`, range `8..512`).
- applies to both:
  - default state cache (`state` / `state_meta`)
  - endpoint-aware cache (`state_by_endpoint` / `state_meta_by_endpoint`)
- pruning policy: oldest `updated_ms` entries are dropped first when the cap is exceeded.

Recommended tuning:
- many devices with sparse telemetry: lower to `24..48`.
- few devices with dense telemetry (multiple endpoints): keep `64` or raise intentionally.
