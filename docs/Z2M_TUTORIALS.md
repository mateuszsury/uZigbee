# Z2M Tutorials (Use Cases)

These are practical snippets focused on Zigbee2MQTT-oriented workflows.

## 1) Coordinator: Pair and Control Without Endpoint Math

```python
import time
import uzigbee

coordinator = uzigbee.Coordinator().start(form_network=True)
coordinator.permit_join(60)

deadline = time.ticks_add(time.ticks_ms(), 20000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    coordinator.process_pending_discovery()
    light = coordinator.select_device(feature="on_off")
    if light is not None:
        light.on()
        time.sleep_ms(200)
        light.off()
        break
    time.sleep_ms(100)
```

What this gives:
- auto-discovery after join
- endpoint/cluster mapping hidden behind `select_device(...)`
- high-level control via `device.on()` / `device.off()`

## 2) Router: Contact + Motion + Reporting/Binding Automation

```python
import uzigbee

router = (
    uzigbee.Router()
    .add_contact_sensor(name="door")
    .add_motion_sensor(name="hall")
    .start(join_parent=True)
)

router.configure_reporting_policy("contact_sensor", endpoint_id=1, auto_apply=True, dst_short_addr=0x0000)
router.configure_reporting_policy("motion_sensor", endpoint_id=2, auto_apply=True, dst_short_addr=0x0000)

router.configure_binding_policy(
    "contact_sensor",
    endpoint_id=1,
    dst_ieee_addr="11:22:33:44:55:66:77:88",
    req_dst_short_addr=0x0000,
    auto_apply=True,
)
```

What this gives:
- chainable endpoint declaration
- default reporting presets per capability
- one-call binding policy with auto-apply

## 3) Sleepy EndDevice: Contact/Motion With Low Power Profile

```python
import time
import uzigbee

ed = (
    uzigbee.EndDevice(
        sleepy=True,
        poll_interval_ms=2000,
        keep_alive_ms=8000,
        wake_window_ms=700,
        checkin_interval_ms=60000,
        low_power_reporting=True,
    )
    .add_contact_sensor(name="door")
    .add_motion_sensor(name="hall")
    .start(join_parent=True)
)

while True:
    ed.mark_wake()
    if ed.should_poll():
        ed.mark_poll()
    if ed.should_keepalive():
        ed.mark_keepalive()
    time.sleep_ms(500)
```

What this gives:
- sleepy runtime profile for battery devices
- deterministic poll/keepalive timing helpers
- low-power reporting tuning through built-in policy path

## 4) Zigbee2MQTT Validation Path

Run quick validation:
- `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_z2m_validate_smoke.py tests/hil_z2m_setters_smoke.py --retries 4 --timeout 180`

Run full interview-oriented matrix:
- `python tools/z2m_interview_suite.py --ports COM3 COM5 --retries 4 --timeout 180 --report-json docs/z2m_interview_report.json`
