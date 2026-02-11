"""HIL smoke for high-level uzigbee.ContactSensor wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

sensor = uzigbee.ContactSensor(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_contact_sensor_01",
    sw_build_id="step25",
)

try:
    sensor.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

sensor.set_contact(True)
contact_closed = sensor.get_contact()
sensor.set_contact(False)
contact_open = sensor.get_contact()
zone_status = sensor.get_zone_status()
zone_type = sensor.get_zone_type()
stats = z.event_stats()

print("uzigbee.hil.contact.closed", contact_closed)
print("uzigbee.hil.contact.open", contact_open)
print("uzigbee.hil.contact.zone_status", zone_status)
print("uzigbee.hil.contact.zone_type", hex(zone_type))
print("uzigbee.hil.contact.stats", stats)
assert isinstance(contact_closed, bool)
assert isinstance(contact_open, bool)
assert isinstance(zone_status, int)
assert zone_type == uzigbee.IAS_ZONE_TYPE_CONTACT_SWITCH
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.contact.result PASS")
