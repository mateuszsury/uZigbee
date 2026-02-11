"""HIL: router with duplicated on/off capabilities on endpoints 1 and 2."""

import gc
import time

import uzigbee

try:
    import machine
except Exception as exc:
    print("TEST_FAIL machine module unavailable: %s" % exc)
    raise


LED_PIN = 8
EP_LED = 10
EP_AUX = 11
AUTO_JOIN_CHANNEL_MASK = (1 << 11) | (1 << 15) | (1 << 20) | (1 << 25)


def _signal_cb(signal_id, status):
    try:
        name = uzigbee.signal_name(signal_id)
    except Exception:
        name = "unknown"
    print("signal %s(0x%02x) status=%d" % (name, int(signal_id), int(status)))


_counts = {EP_LED: 0, EP_AUX: 0}
_aux_out = {"value": False}


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
    endpoint = int(endpoint)
    cluster_id = int(cluster_id) & 0xFFFF
    attr_id = int(attr_id) & 0xFFFF
    status = int(status)
    print(
        "attr src=%s ep=%d cluster=0x%04x attr=0x%04x value=%s status=%d"
        % (
            "none" if source_short is None else ("0x%04x" % (int(source_short) & 0xFFFF)),
            endpoint,
            cluster_id,
            attr_id,
            value,
            status,
        )
    )
    if status == 0 and cluster_id == 0x0006 and attr_id == 0x0000 and endpoint in _counts:
        _counts[endpoint] = int(_counts[endpoint]) + 1


def _aux_writer(value):
    _aux_out["value"] = bool(value)
    print("aux_writer value=%d" % (1 if bool(value) else 0))


def _new_router():
    kwargs = {
        "auto_register": True,
        "commissioning_mode": "guided",
        "auto_join_channel_mask": AUTO_JOIN_CHANNEL_MASK,
        "join_retry_max": 8,
        "join_retry_base_ms": 700,
        "join_retry_max_backoff_ms": 12000,
        "self_heal_enabled": True,
        "self_heal_retry_max": 3,
        "self_heal_retry_base_ms": 200,
        "self_heal_retry_max_backoff_ms": 2000,
    }
    while True:
        try:
            return uzigbee.Router(**kwargs)
        except TypeError as exc:
            msg = str(exc)
            if "unexpected keyword argument" not in msg:
                raise
            parts = msg.split("'")
            if len(parts) < 2:
                raise
            key = parts[1]
            if key not in kwargs:
                raise
            kwargs.pop(key, None)
            print("router compat: drop unsupported kwarg %s" % key)


led = machine.Pin(LED_PIN, machine.Pin.OUT)
led.value(0)

router = _new_router()
router.add_power_outlet(endpoint_id=EP_LED, name="switch_led", with_metering=False)
router.add_power_outlet(endpoint_id=EP_AUX, name="switch_aux", with_metering=False)
router.on_signal(_signal_cb)
router.on_attribute(_attr_cb)
if hasattr(router, "on_commissioning_event"):
    router.on_commissioning_event(lambda event: print("commissioning_event %s" % event))
router.bind_onoff_output(actor="switch_led", pin=LED_PIN, active_high=True, initial=False)
router.bind_onoff_output(actor="switch_aux", writer=_aux_writer, initial=False)
router.start(join_parent=False)
try:
    if hasattr(router.stack, "start_network_steering"):
        router.stack.start_network_steering()
    else:
        router.join_parent()
except OSError as exc:
    if (not exc.args) or (int(exc.args[0]) not in (-1, 259)):
        raise
    print("join_parent_busy code=%d (ignored)" % int(exc.args[0]))

status = router.status()
print(
    "TEST_READY short=%s ieee=%s endpoints=%s"
    % (status.get("short_addr"), status.get("ieee_hex"), status.get("endpoint_ids"))
)
try:
    print("network_info=%s" % router.network_info())
except Exception:
    pass

counter = 0
next_retry_ms = time.ticks_add(time.ticks_ms(), 5000)
while True:
    led_state = router.actuator_state("switch_led", field="on_off", default=None)
    aux_state = router.actuator_state("switch_aux", field="on_off", default=None)
    print(
        "tick=%d led_hw=%d led=%s aux=%s onoff_counts ep%d=%d ep%d=%d aux_writer=%d"
        % (
            int(counter),
            int(led.value()),
            led_state,
            aux_state,
            int(EP_LED),
            int(_counts[EP_LED]),
            int(EP_AUX),
            int(_counts[EP_AUX]),
            1 if bool(_aux_out["value"]) else 0,
        )
    )
    now_ms = time.ticks_ms()
    if time.ticks_diff(now_ms, int(next_retry_ms)) >= 0:
        try:
            if hasattr(router.stack, "start_network_steering"):
                router.stack.start_network_steering()
            else:
                router.join_parent()
            print("steering_retry ok")
        except OSError as exc:
            if (not exc.args) or (int(exc.args[0]) not in (-1, 259)):
                raise
            print("steering_retry busy code=%d" % int(exc.args[0]))
        next_retry_ms = time.ticks_add(now_ms, 5000)
    counter += 1
    gc.collect()
    time.sleep(1)
