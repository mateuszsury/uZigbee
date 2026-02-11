# Progress Step 33 (2026-02-09)

Scope:
- Configure coordinator web demo to use WiFi STA on user network (`STAR1` / `wodasodowa`).
- Validate this path on device (`COM3`) together with active Zigbee coordinator.

Implementation:
- Updated `examples/coordinator_web_demo.py`:
  - added STA defaults:
    - `DEFAULT_STA_SSID = "STAR1"`
    - `DEFAULT_STA_PASSWORD = "wodasodowa"`
  - added WiFi mode handling:
    - `setup_sta()`
    - `setup_wifi()` (`sta` with AP fallback, or `ap`)
  - status page now shows:
    - `wifi_mode`
    - `wifi_ip`
  - changed runtime startup order to:
    - `setup_wifi()` then `start_zigbee()`
  - rationale: on tested ESP32-C6, Zigbee-first prevented reliable STA association.
- Added HIL test:
  - `tests/hil_web_demo_sta_smoke.py`
  - validates:
    - STA connect to `STAR1`,
    - Zigbee coordinator start,
    - IEEE/short readback,
    - HTTP socket bind,
    - no queue/scheduler drops.

Validation:
- Host tests:
  - `pytest -q tests/test_example_coordinator_web_demo.py`
  - Result: `5 passed`
- Device HIL:
  - `python tools/hil_runner.py --ports COM3 --tests tests/hil_web_demo_sta_smoke.py --retries 3 --timeout 220`
  - Result: PASS
  - observed:
    - `uzigbee.hil.webdemo.sta.ip 192.168.0.26`
    - `uzigbee.hil.webdemo.sta.short_addr 0x0`
    - `uzigbee.hil.webdemo.sta.result PASS`

Docs updated:
- `docs/EXAMPLES.md`
- `docs/BUILD.md`

Plan status:
- `plan.md` updated with execution log entry for Step 33.
