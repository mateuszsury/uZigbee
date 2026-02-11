"""Router sensor/switch simulator for dual-device coordinator tests."""

try:
    import ubinascii as binascii
except ImportError:
    import binascii

import gc
import time

import uzigbee


stack = uzigbee.ZigbeeStack()

light = uzigbee.DimmableLight(
    endpoint_id=1,
    stack=stack,
    manufacturer="uzigbee",
    model="uzb_router_light_sim",
    sw_build_id="dualtest",
)
temp = uzigbee.TemperatureSensor(
    endpoint_id=2,
    stack=stack,
    manufacturer="uzigbee",
    model="uzb_router_temp_sim",
    sw_build_id="dualtest",
)
contact = uzigbee.ContactSensor(
    endpoint_id=3,
    stack=stack,
    manufacturer="uzigbee",
    model="uzb_router_contact_sim",
    sw_build_id="dualtest",
)
motion = uzigbee.MotionSensor(
    endpoint_id=4,
    stack=stack,
    manufacturer="uzigbee",
    model="uzb_router_motion_sim",
    sw_build_id="dualtest",
)
switch_ep = uzigbee.DimmableSwitch(
    endpoint_id=5,
    stack=stack,
    manufacturer="uzigbee",
    model="uzb_router_switch_sim",
    sw_build_id="dualtest",
)


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
    if int(status) != 0:
        return
    print(
        "attr src=%s ep=%d cluster=0x%04x attr=0x%04x value=%s"
        % (
            "None" if source_short is None else ("0x%04x" % (int(source_short) & 0xFFFF)),
            int(endpoint),
            int(cluster_id) & 0xFFFF,
            int(attr_id) & 0xFFFF,
            value,
        )
    )


stack.init(uzigbee.ROLE_ROUTER)
stack.on_signal(_signal_cb)
stack.on_attribute(_attr_cb)

light.provision(register=False)
temp.provision(register=False)
contact.provision(register=False)
motion.provision(register=False)
switch_ep.provision(register=True)

stack.start(form_network=False)
print(
    "router simulator started ieee=%s"
    % binascii.hexlify(stack.get_ieee_addr()).decode()
)

# Keep process alive without additional stack API calls to avoid lock-race
# failures on some firmware revisions during long runtime.
counter = 0
while True:
    print("tick=%d alive" % counter)
    counter += 1
    gc.collect()
    time.sleep(5)

