# Examples (Draft)

Planned examples:
- Simple on/off light
- Temperature sensor
- Coordinator startup
- Router bootstrap
- EndDevice bootstrap

Available demo app:
- `examples/coordinator_web_demo.py`
- `examples/coordinator_web_portal_highlevel.py` (high-level `uzigbee.Coordinator` only)
- `examples/router_sensor_switch_sim_highlevel.py` (high-level `uzigbee.Router` only)
- `examples/coordinator_web_portal_color_highlevel.py` (high-level coordinator web UI for color light control)
- `examples/router_neopixel_color_light_highlevel.py` (high-level router color-light endpoint mirrored to NeoPixel on `GPIO8`)

High-level API scaffold (Phase 4.5.1):
- `uzigbee.Coordinator` + `uzigbee.network` device registry.
- Target usage pattern:
  - `coordinator = uzigbee.Coordinator().start(form_network=True)`
  - `coordinator.permit_join(60)`
  - `device = coordinator.get_device(0x1234)`
  - `device.on()`
  - `temp_c = device.read.temperature()`
  - `light = coordinator.select_device(feature="on_off")`
  - `thermostat = coordinator.select_device(features=("thermostat", "cover"))`
  - `known = coordinator.get_device_by_ieee("10:11:12:13:14:15:16:17")`
  - `online_lights = coordinator.find_devices(feature="on_off", online=True)`
  - `status = coordinator.device_status(0x1234)`
  - duplicate feature selector pattern:
    - `device.switch(1).on()`
    - `device.switch(2).off()`
    - `temp_ep2 = device.temperature_sensor(2).read.temperature()`

Node bootstrap scaffold (Phase 4.6.1):
- Router:
  - `router = uzigbee.Router().add_light().add_switch(dimmable=True).start(join_parent=True)`
  - retry join explicitly (same high-level API): `router.join_parent()`
- EndDevice:
  - `ed = uzigbee.EndDevice(sleepy=True).add_contact_sensor().start(join_parent=True)`
  - retry join explicitly (same high-level API): `ed.join_parent()`

Node declarative builder scaffold (Phase 4.6.2):
- Router:
  - `router = uzigbee.Router().add("light", color=True).add("motion").add_all(("temperature", {"capability": "switch", "dimmable": True, "endpoint_id": 9})).start(join_parent=True)`
- EndDevice:
  - `ed = uzigbee.EndDevice(sleepy=True).add_all(("contact", {"capability": "ias_zone", "zone_type": uzigbee.IAS_ZONE_TYPE_CONTACT_SWITCH})).start(join_parent=True)`

Node sensor update scaffold (Phase 4.6.3):
- Local updates:
  - `router.update("temperature", 21.7, endpoint_id=4)`
  - `router.update("motion", True, endpoint_id=5)`
  - `router.update("climate", {"temperature": 22.0, "humidity": 45.0}, endpoint_id=11)`
- Local cache reads:
  - `router.sensor_state("temperature", endpoint_id=4)`
  - `router.sensor_states()`

Node actuator scaffold (Phase 4.6.4):
- Actor lookup:
  - `light = router.actor("main_light")`
- Idempotent local mirror:
  - `light.on()`
  - `light.on()`  # second call keeps state with `changed=False`
- Other actuator classes:
  - `router.actor("front_lock").lock()`
  - `router.actor("blind").cover(60)`
  - `router.actor("hvac").thermostat_mode("heat")`
- Mirror reads:
  - `router.actuator_state("main_light", field="on_off")`
  - `router.actuator_states()`

Node reporting policy scaffold (Phase 4.6.5):
- Configure defaults per capability:
  - `router.configure_reporting_policy("thermostat", endpoint_id=9, dst_short_addr=0x0000)`
- Override one attribute interval:
  - `router.configure_reporting_policy("contact", endpoint_id=10, overrides=({"cluster_id": uzigbee.CLUSTER_ID_IAS_ZONE, "attr_id": uzigbee.ATTR_IAS_ZONE_STATUS, "attr_type": uzigbee.zcl.DATA_TYPE_16BITMAP, "min_interval": 2, "max_interval": 120, "reportable_change": 1},))`
- Apply:
  - `router.apply_reporting_policy(endpoint_id=9)`
  - `router.reporting_policies()`

Node binding policy scaffold (Phase 4.6.6):
- Configure bind defaults:
  - `router.configure_binding_policy("thermostat", endpoint_id=12, dst_ieee_addr="11:22:33:44:55:66:77:88", req_dst_short_addr=0x0000)`
- Apply:
  - `router.apply_binding_policy(endpoint_id=12)`
- IAS automation:
  - `router.configure_binding_policy("ias_zone", endpoint_id=14, dst_ieee_addr="88:99:aa:bb:cc:dd:ee:ff", ias_enroll=True)`
  - `router.apply_binding_policy(endpoint_id=14)`

Sleepy EndDevice scaffold (Phase 4.6.7):
- Profile:
  - `ed = uzigbee.EndDevice(sleepy=True, poll_interval_ms=1500, keep_alive_ms=4000, wake_window_ms=500, low_power_reporting=True)`
  - `ed.mark_wake()`
  - `if ed.should_poll(): ed.mark_poll()`
  - `if ed.should_keepalive(): ed.mark_keepalive()`
- Low-power reporting:
  - `ed.configure_reporting_policy("contact", endpoint_id=15)`  # auto-tuned min/max intervals

Node persistence scaffold (Phase 4.6.8):
- Configure write throttle:
  - `router.configure_persistence(min_interval_ms=30000)`
- Save:
  - `router.save_node_state("uzigbee_node_state.json", force=False)`
- Load:
  - `router.load_node_state("uzigbee_node_state.json", merge=False)`

Advanced extension scaffold (Phase 4.6.9):
- Register custom capability:
  - `router.register_capability("air_quality_sensor", "create_air_quality_sensor", aliases=("aqi",))`
  - `router.add("aqi", endpoint_id=21)`
- Register policy hook:
  - `router.register_policy_hook("logger", lambda event, payload: print(event, payload))`

Host matrix run (Phase 4.6.10):
- `python tools/run_node_host_matrix.py`

HIL matrix run (Phase 4.6.11):
- `python tools/hil_runner.py --ports COM3 --tests tests/hil_node_router_smoke.py tests/hil_node_enddevice_sleepy_smoke.py tests/hil_node_binding_reporting_smoke.py tests/hil_node_longrun_smoke.py --retries 3 --timeout 300`

Node cookbook (Phase 4.6.12):
- Router quickstart:
  - `router = uzigbee.Router().add_light(name="kitchen_light", dimmable=True).add_temperature_sensor(name="kitchen_temp").start(join_parent=True)`
  - `router.update("temperature", 22.1, endpoint_id=2)`
  - `router.actor("kitchen_light").on()`
  - `router.sensor_state("temperature", endpoint_id=2)`
- EndDevice quickstart:
  - `ed = uzigbee.EndDevice(sleepy=True, poll_interval_ms=2000, keep_alive_ms=8000, wake_window_ms=700, checkin_interval_ms=60000, low_power_reporting=True).add_contact_sensor(name="door_contact").add_motion_sensor(name="hall_motion").start(join_parent=True)`
  - `ed.mark_wake(); ed.should_poll(); ed.should_keepalive()`
  - `ed.configure_reporting_policy("contact", endpoint_id=1)`  # low-power tuned
- Advanced policy flow:
  - `router.configure_reporting_policy("thermostat", endpoint_id=9, dst_short_addr=0x0000, auto_apply=True)`
  - `router.configure_binding_policy("thermostat", endpoint_id=9, dst_ieee_addr="11:22:33:44:55:66:77:88", auto_apply=True)`
  - `router.apply_binding_policy(endpoint_id=9, dst_ieee_addr="22:33:44:55:66:77:88:99")`  # override destination
  - `router.register_policy_hook("audit", lambda event, payload: print(event, payload))`
  - `router.save_node_state("uzigbee_node_state.json")`

Gateway bridge scaffold (Phase 4 / Step 74):
- Runtime bridge object:
  - `gateway = uzigbee.Gateway().start(form_network=True)`
  - `gateway.permit_join(60, auto_discover=True)`
- Device control command:
  - `gateway.process_command({"op": "control", "short_addr": "0x1234", "action": "on"})`
  - `gateway.process_command({"op": "control", "short_addr": "0x1234", "action": "level", "value": 128})`
- Device read command:
  - `gateway.process_command({"op": "read", "short_addr": "0x1234", "metric": "temperature", "use_cache": True})`
- JSON frame flow (for HTTP/TCP/WebSocket handlers):
  - `resp_json = gateway.process_frame('{"op":"list_devices"}')`
- Event queue:
  - `gateway.on_event(lambda event, payload: print(event, payload))`
  - `gateway.poll_event()`
  - `gateway.drain_events(16)`

OTA manager scaffold (Phase 4 / Step 75):
- Capability check:
  - `caps = uzigbee.ota.capabilities(stack)`  # client/server control availability
- Stateful manager:
  - `ota_mgr = uzigbee.OtaManager(stack)`
  - `ota_mgr.start_client(strict=False)`  # safe no-op on unsupported firmware
  - `ota_mgr.set_query_interval(endpoint_id=1, interval_min=5)`
  - `ota_mgr.query_image(server_ep=1, server_addr=0x00)`
  - `ota_mgr.stop_query()`
  - `ota_mgr.stop_client(strict=False)`
- OTA server (when firmware exposes server API):
  - `ota_mgr.start_server("firmware.zigbee.ota", file_version=0x00010002, hw_version=1, strict=False)`
  - `ota_mgr.stop_server(strict=False)`

Green Power scaffold (Phase 4 / Step 76):
- Manager setup:
  - `gp = uzigbee.GreenPowerManager(stack, proxy_enabled=True, sink_enabled=True, commissioning_allowed=False)`
  - `gp.on_event(lambda event, payload: print(event, payload))`
- Hook into stack signals:
  - `gp.install_signal_handler()`
- Runtime control:
  - `gp.set_proxy(True, strict=False)`
  - `gp.set_sink(True, strict=False)`
  - `gp.set_commissioning(True, duration_s=60, strict=False)`
- Observe events and status:
  - `evt = gp.poll_event()`
  - `all_events = gp.drain_events()`
  - `info = gp.status()`

Touchlink scaffold (Phase 4 / Step 77):
- Manager setup:
  - `tl = uzigbee.TouchlinkManager(stack)`
  - `tl.on_event(lambda event, payload: print(event, payload))`
- Hook into stack signals:
  - `tl.install_signal_handler()`
- Runtime control:
  - `tl.start_initiator(channel=11, strict=False)`
  - `tl.set_target_mode(True, strict=False)`
  - `tl.stop_initiator(strict=False)`
  - `tl.factory_reset(strict=False)`
- Observe events and status:
  - `evt = tl.poll_event()`
  - `all_events = tl.drain_events()`
  - `info = tl.status()`

NCP/RCP scaffold (Phase 4 / Step 78):
- Manager setup:
  - `ncp_mgr = uzigbee.NcpRcpManager(stack, mode=uzigbee.ncp.NCP_MODE_NCP, transport=uzigbee.ncp.TRANSPORT_UART, port="UART0", baudrate=115200, flow_control=False)`
  - `ncp_mgr.on_event(lambda event, payload: print(event, payload))`
- Start / stop mode:
  - `ncp_mgr.start(strict=False)`
  - `ncp_mgr.stop(strict=False)`
- Frame bridge:
  - `ncp_mgr.send_host_frame(b"\\x01\\x02", strict=False)`
  - `ncp_mgr.receive_device_frame(b"\\xaa\\xbb")`
- Signal bridge and status:
  - `ncp_mgr.install_signal_handler()`
  - `evt = ncp_mgr.poll_event()`
  - `info = ncp_mgr.status()`

What this demo does:
- starts `uzigbee` as coordinator,
- exposes a small HTTP UI (example app, not library feature),
- allows enabling `permit_join` from browser,
- allows sending `ON/OFF/TOGGLE/LEVEL` to a target light.
- auto-selects target `short_addr` after join/update/authorized signals
  by reading `ZigbeeStack.get_last_joined_short_addr()`.
- by default connects WiFi in `STA` mode to:
  - SSID: `STAR1`
  - password: `wodasodowa`
- if `STA` connection fails, falls back to AP (`uZigbeeDemo` / `uzigbee1234`).
- startup order in this demo is `WiFi -> Zigbee` (on this device this is required for reliable STA association while coordinator is active).
- logs OTA control capability at startup (`ota control supported=True/False`) using `uzigbee.ota.is_control_supported()`.

Important limitation in current API:
- Auto-target requires at least one fresh join/update/authorized event in current runtime.
- If no such event occurs, target remains default (`0x0000`) until set manually in UI.

Run on device:
1. Start script directly from host:
   - `python -m mpremote connect COM3 run examples/coordinator_web_demo.py`
   - alternate stable launcher (keeps COM open, avoids `mpremote` raw-repl issues):
     - `python tools/run_web_demo_serial.py --port COM3 --reset`
2. Read serial logs:
   - on success in STA mode you will see `wifi sta connected ... ip=...`
   - otherwise demo prints fallback AP info.
3. Open browser:
   - STA mode: `http://<ip_z_logu>/`
   - fallback AP: `http://192.168.4.1/`

Quick smoke without starting web loop:
- `python -m mpremote connect COM3 resume soft-reset run tests/hil_web_demo_startup_smoke.py`
- `python tools/hil_runner.py --ports COM3 --tests tests/hil_web_demo_sta_smoke.py --retries 3 --timeout 220`

High-level dual-device demo (coordinator + router simulator):
1. Start coordinator web portal (high-level only):
   - `python tools/run_web_demo_serial.py --port COM3 --script examples/coordinator_web_portal_highlevel.py --reset`
2. Start router simulator (high-level only):
   - `python tools/run_web_demo_serial.py --port COM6 --script examples/router_sensor_switch_sim_highlevel.py --reset`
3. In portal, use:
   - `permit join`
   - `probe`
   - `on/off/toggle/level`

High-level color demo (coordinator web portal + NeoPixel router):
1. Start coordinator color portal:
   - `python tools/run_web_demo_serial.py --port COM3 --script examples/coordinator_web_portal_color_highlevel.py --reset`
2. Start router NeoPixel color light (pin 8):
   - `python tools/run_web_demo_serial.py --port COM6 --script examples/router_neopixel_color_light_highlevel.py --reset`
3. Commissioning mode used by default:
   - both scripts use high-level `guided` mode with automatic fallback (`auto`) and do not hardcode `channel/pan_id/extended_pan_id`.
   - optional advanced fixed override is available in each script via `FIXED_NETWORK_PROFILE` at the top of the file.
4. Open coordinator portal:
   - `http://<ip_z_logu>/`
   - UI on `/` exposes full controls for router NeoPixel (target selection, on/off/toggle, level, RGB, XY, CT) and live status from `/status`.
5. Use UI routes:
   - `on/off/toggle`
   - `level`
   - `rgb` presets (`red/green/blue/black`)
   - manual `xy` / `ct`
6. Optional automated HIL runner:
   - `python tools/hil_highlevel_color_portal_runner.py --coord-port COM3 --router-port COM6 --timeout-s 260`
7. Troubleshooting:
   - if router log shows repeated `signal steering(0x0a) status=-1`, both boards are not joining the same Zigbee network context; clear Zigbee state (`nvs`, `zb_storage`, `zb_fct`) or flash identical latest uzigbee firmware on both boards, then retry.
   - if coordinator log shows `Device not in a network, failed to open network` during startup, keep script running; the demo retries `permit_join` automatically after network formation.
   - if `ImportError: no module named 'neopixel'` appears, this example auto-falls back to a local `machine.bitstream` NeoPixel driver.
   - if HTTP portal stops answering right after Zigbee starts (timeouts from LAN), rebuild/flash firmware that includes Wi-Fi + 802.15.4 coexist hook (`enable_wifi_i154_coex`) and use high-level `Coordinator.start()` path.
   - if filesystem is unavailable (`OSError: [Errno 19] ENODEV`), portal still serves full embedded HTML from script; optional external `portal_color.html` is used only when VFS is mounted.

High-level endpoint-overlap + long-run matrix (coordinator + dual-switch router):
1. Start host runner (coordinator on `COM6`, router on `COM3` by default):
   - `python tools/hil_highlevel_overlap_longrun_runner.py --coord-port COM6 --router-port COM3 --timeout-s 520`
2. What this validates:
   - auto/guided commissioning without hardcoded `channel/pan_id/extended_pan_id`,
   - duplicate same-type endpoint mapping on coordinator high-level API (`device.switch(1)` and `device.switch(2)`),
   - long-run control stability (120 rounds),
   - router-side receipt of `on_off` updates on both endpoints (`ep=10` and `ep=11`).
3. Device scripts used by runner:
   - `tests/hil_highlevel_coordinator_dual_switch_longrun.py`
   - `tests/hil_highlevel_router_dual_switch_overlap.py`
4. Validation status:
   - latest matrix run passed (`TEST_PASS`) with endpoint-hit coverage on both router endpoints (`{10: 21, 11: 21}`) and long-run control (`120` rounds).
   - when commissioning stalls (`timeout waiting_for_target`), clear runtime Zigbee state on both boards (`nvs`, `zb_storage`, `zb_fct`) and rerun the matrix; this recovers deterministic pairing in current lab setup.
5. Batch stability run (overlap + color portal in cycles):
   - smoke: `python tools/hil_stability_suite_runner.py --coord-port COM6 --router-port COM3 --cycles 3 --overlap-timeout-s 620 --color-timeout-s 320`
   - gate for auto-commissioning reliability: `python tools/hil_stability_suite_runner.py --coord-port COM6 --router-port COM3 --cycles 10 --overlap-timeout-s 620 --color-timeout-s 320`
   - JSON report output: `python tools/hil_stability_suite_runner.py --coord-port COM6 --router-port COM3 --cycles 10 --report-json docs/hil_stability_report.json`
   - runner clears runtime Zigbee state on both boards before each cycle and fails-fast on first non-zero scenario return code.
   - overlap scenario includes synthetic `panid_conflict_detected` injection in coordinator loop to validate self-heal path during active control rounds.
   - strict high-level API mode is enabled by default and fails batch if scenario output contains compatibility fallbacks (`drop unsupported kwarg`); use `--no-strict-api` only for legacy-firmware diagnostics.

Auto commissioning (high-level API, no hardcoded Zigbee channel/PAN):
1. Coordinator auto mode:
   - `coordinator = uzigbee.Coordinator(network_mode="auto").start(form_network=True)`
   - `print(coordinator.network_info())`
2. Router auto mode:
   - `router = uzigbee.Router(commissioning_mode="auto").add_light().start(join_parent=True)`
   - `print(router.network_info())`
3. Optional fixed override (advanced mode):
   - `coordinator = uzigbee.Coordinator(network_mode="fixed", channel=20, pan_id=0x1A62, extended_pan_id="00124b0001c6c6c6").start(form_network=True)`
   - `router = uzigbee.Router(commissioning_mode="fixed", channel=20, pan_id=0x1A62, extended_pan_id="00124b0001c6c6c6").add_light().start(join_parent=True)`
4. Runtime network snapshot fields (available from high-level API):
   - `info["channel"]`, `info["pan_id"]`, `info["extended_pan_id_hex"]`
   - `info["short_addr"]`, `info["formed"]`, `info["joined"]`
5. Advanced auto-channel tuning (still high-level):
   - `coordinator = uzigbee.Coordinator(network_mode="auto", auto_channel_blacklist=(26,), auto_channel_preferred=(15, 20, 25, 11))`
   - `coordinator.start(form_network=True)`
   - `print(coordinator.network_info()["auto_channel"])`
6. Runtime-generated PAN/extPAN are persisted automatically in auto mode:
   - `info = coordinator.network_info()`
   - `print(info["profile"]["pan_id"], info["profile"]["extended_pan_id"])`
7. Router/EndDevice auto-join policy (no hardcoded PAN/channel):
   - `router = uzigbee.Router(commissioning_mode="auto", auto_join_channel_mask=((1 << 11) | (1 << 15) | (1 << 20) | (1 << 25)))`
   - `router.configure_auto_join(join_retry_max=4, join_retry_base_ms=50, join_retry_max_backoff_ms=500)`
   - `router.add_light().start(join_parent=True)`
8. Guided mode (reuse previous profile, keep automatic fallback):
   - `coordinator = uzigbee.Coordinator(network_mode="guided", auto_channel_scan_wifi=True).start(form_network=True)`
   - `print(coordinator.network_info()["auto_channel"])  # guided_restored_profile or guided_* fallback`
9. Guided Router/EndDevice reconnect:
   - `router = uzigbee.Router(commissioning_mode="guided", auto_join_channel_mask=((1 << 11) | (1 << 15) | (1 << 20) | (1 << 25)))`
   - `router.add_light().start(join_parent=True)`
   - `router.join_parent()  # guided retry, then fallback to full auto_join mask when needed`
10. Self-heal policy for conflict/timeout handling:
   - `coordinator = uzigbee.Coordinator(network_mode="auto")`
   - `coordinator.configure_self_heal(enabled=True, retry_max=3, retry_base_ms=100, retry_max_backoff_ms=1000)`
   - `router = uzigbee.Router(commissioning_mode="auto")`
   - `router.configure_self_heal(enabled=True, retry_max=3, retry_base_ms=100, retry_max_backoff_ms=1000)`
   - `# register optional telemetry callback`
   - `coordinator.on_commissioning_event(lambda event: print("coord_event", event))`
   - `router.on_commissioning_event(lambda event: print("router_event", event))`
   - `# inspect runtime stats`
   - `print(coordinator.network_info()["self_heal"])`
   - `print(router.network_info()["self_heal"])`
11. Commissioning telemetry counters for CI/HIL:
   - `coordinator = uzigbee.Coordinator(network_mode="auto")`
   - `coordinator.start(form_network=True)`
   - `print(coordinator.commissioning_stats())`
   - `router = uzigbee.Router(commissioning_mode="auto").add_light().start(join_parent=True)`
   - `print(router.commissioning_stats())`
   - `# optional reset window between test phases`
   - `coordinator.commissioning_stats(reset=True)`
   - `router.commissioning_stats(reset=True)`
