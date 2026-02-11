"""HIL smoke for high-level uzigbee.IASZone wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

zone = uzigbee.IASZone(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_ias_zone_01",
    sw_build_id="step27",
    zone_type=uzigbee.IAS_ZONE_TYPE_CONTACT_SWITCH,
)

try:
    zone.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

zone.set_alarm(True)
alarm_true = zone.get_alarm()
zone.set_alarm(False)
alarm_false = zone.get_alarm()
zone_status = zone.get_zone_status()
zone_type = zone.get_zone_type()
stats = z.event_stats()

print("uzigbee.hil.ias.alarm_true", alarm_true)
print("uzigbee.hil.ias.alarm_false", alarm_false)
print("uzigbee.hil.ias.zone_status", zone_status)
print("uzigbee.hil.ias.zone_type", hex(zone_type))
print("uzigbee.hil.ias.stats", stats)
assert isinstance(alarm_true, bool)
assert isinstance(alarm_false, bool)
assert isinstance(zone_status, int)
assert zone_type == uzigbee.IAS_ZONE_TYPE_CONTACT_SWITCH
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.ias.result PASS")
