"""HIL: router high-level node with on/off output bound to GPIO8 LED."""

import gc
import time

import uzigbee

try:
    import machine
except Exception as exc:
    print("TEST_FAIL machine module unavailable: %s" % exc)
    raise


LED_PIN = 8


def _signal_cb(signal_id, status):
    try:
        name = uzigbee.signal_name(signal_id)
    except Exception:
        name = "unknown"
    print("signal %s(0x%02x) status=%d" % (name, int(signal_id), int(status)))


def _attr_cb(*event):
    if len(event) == 5:
        endpoint, cluster_id, attr_id, value, status = event
        source_short = None
    elif len(event) == 6:
        endpoint, cluster_id, attr_id, value, _atype, status = event
        source_short = None
    elif len(event) >= 7:
        source_short, endpoint, cluster_id, attr_id, value, _atype, status = event[:7]
    else:
        return
    print(
        "attr src=%s ep=%d cluster=0x%04x attr=0x%04x value=%s status=%d"
        % (
            "none" if source_short is None else ("0x%04x" % (int(source_short) & 0xFFFF)),
            int(endpoint),
            int(cluster_id) & 0xFFFF,
            int(attr_id) & 0xFFFF,
            value,
            int(status),
        )
    )


led = machine.Pin(LED_PIN, machine.Pin.OUT)
led.value(0)

router = uzigbee.Router(auto_register=True)
router.add_power_outlet(endpoint_id=1, name="led_switch", with_metering=False)
router.on_signal(_signal_cb)
router.on_attribute(_attr_cb)
router.bind_onoff_output(actor="led_switch", pin=LED_PIN, active_high=True, initial=False)
router.start(join_parent=True)

status = router.status()
print(
    "router_ready short=%s ieee=%s endpoints=%s"
    % (status.get("short_addr"), status.get("ieee_hex"), status.get("endpoint_ids"))
)

counter = 0
while True:
    row = router.actuator_state("led_switch", field="on_off", default=None)
    led_hw = int(led.value())
    print("tick=%d led_hw=%d switch_state=%s" % (int(counter), int(led_hw), row))
    counter += 1
    gc.collect()
    time.sleep(1)
