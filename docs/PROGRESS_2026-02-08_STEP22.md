# Progress 2026-02-08 - Step 22

Scope:
- verify on real ESP32-C6 that ZigBee stack works through MicroPython bridge, including IEEE/short address reads.

Environment:
- target port: `COM3` (ESP32-C6).
- firmware: `build-ESP32_GENERIC_C6-uzigbee-step21b` (already flashed).
- note: first `mpremote` call after hard reset can fail entering raw REPL; immediate retry works.

Device validation executed:
1. Chip identity / MAC (host side):
   - `python -m esptool --port COM3 chip-id`
   - MAC reported: `40:4c:ca:ff:fe:4e:4c:64`.
2. ZigBee stack start via MicroPython bridge (`uzigbee`):
   - init coordinator
   - create endpoint + register device
   - `start(form_network=True)`
   - read `ieee`, `short_addr`, event stats, collected signals.
3. Direct bridge calls (`_uzigbee`) for address reads:
   - `_uzigbee.get_ieee_addr()`
   - `_uzigbee.get_short_addr()`.

Results:
- `uzigbee` path:
  - `ieee_hex = 644c4efeffca4c40`
  - `short_addr = 0x0`
  - signals captured via callback: `[(23, -1), (1, 0), (54, 0), (11, 0)]`
  - event queue stats healthy: no drops (`dropped_queue_full=0`, `dropped_schedule_fail=0`).
- `_uzigbee` path:
  - `ieee_hex = 644c4efeffca4c40`
  - `short_addr = 0x0`.

Interpretation:
- ZigBee stack is running through our MicroPython bridge and forms as coordinator.
- Address reads work correctly from both high-level and low-level bridge APIs.
- IEEE from ZigBee API is byte-reversed versus `esptool` MAC print order (expected representation difference), values are consistent for the same hardware identity.

Plan updates:
- In `plan.md`, marked as done:
  - `Uruchomiæ koordynator formuj¹cy sieæ z poziomu REPL`.
