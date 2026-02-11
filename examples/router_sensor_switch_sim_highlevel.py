"""Router sensor/switch simulator using only high-level uzigbee API."""

import gc
import time

import uzigbee


def _signal_cb(signal_id, status):
    try:
        name = uzigbee.signal_name(signal_id)
    except Exception:
        name = "unknown"
    print("signal %s(0x%02x) status=%d" % (name, int(signal_id), int(status)))


router = uzigbee.Router(auto_register=True)
router.add_light(endpoint_id=1, name="light_main", dimmable=True)
router.add_temperature_sensor(endpoint_id=2, name="temp_main")
router.add_contact_sensor(endpoint_id=3, name="contact_main")
router.add_motion_sensor(endpoint_id=4, name="motion_main")
router.add_switch(endpoint_id=5, name="switch_main", dimmable=True)
router.on_signal(_signal_cb)
router.start(join_parent=True)

print("router high-level started")
print("router status=%s" % router.status())

# Local high-level state cache updates for visibility in logs.
router.update("temperature", 21.5, endpoint_id=2)
router.update("contact", False, endpoint_id=3)
router.update("motion", False, endpoint_id=4)
print("initial local sensor cache=%s" % (router.sensor_states(),))

counter = 0
while True:
    phase = int(counter // 4)
    temp = 21.5 + float((phase % 6) * 0.2)
    contact = bool(phase % 2)
    motion = not contact
    router.update("temperature", temp, endpoint_id=2)
    router.update("contact", contact, endpoint_id=3)
    router.update("motion", motion, endpoint_id=4)
    print(
        "tick=%d alive temp=%.1f contact=%s motion=%s"
        % (int(counter), float(temp), bool(contact), bool(motion))
    )
    counter += 1
    gc.collect()
    time.sleep(5)
