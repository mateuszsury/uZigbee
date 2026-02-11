# Progress Step 34 (2026-02-09)

Scope:
- Stabilize coordinator web demo connectivity on `COM3` for long-running STA sessions.

Implementation:
- Updated `examples/coordinator_web_demo.py`:
  - added STA watchdog + periodic heartbeat logs,
  - added STA reconnect trigger (interval-based),
  - attempted AP+STA startup path with explicit AP/STA state refresh,
  - added client socket timeout handling in HTTP server (`_serve_one`) to avoid permanent blocking on stalled client sockets.
- Added launcher utility:
  - `tools/run_web_demo_serial.py`
  - runs demo over serial paste mode and keeps COM open (avoids `mpremote` raw-repl instability during long sessions).

Validation:
- Device runtime (`COM3`):
  - launcher process active:
    - `python tools/run_web_demo_serial.py --port COM3 --reset`
  - observed STA:
    - `wifi sta connected ssid=STAR1 ip=192.168.0.26`
  - observed web server:
    - `http server listening on 0.0.0.0:80`
  - HTTP stability check from host:
    - 30 consecutive GET requests to `http://192.168.0.26/`
    - result: `30 OK / 0 fail`
- Host tests:
  - `pytest -q tests/test_example_coordinator_web_demo.py tests/test_core_api.py tests/test_devices_api.py tests/test_import.py`
  - result: `41 passed`

Notes:
- Logs still show occasional ESP WiFi warning `CCMP replay detected`; despite this, HTTP stayed stable in the validated run.

Plan status:
- `plan.md` updated with execution log entry for Step 34.
