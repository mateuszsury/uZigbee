"""HIL smoke for high-level uzigbee.Thermostat wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

thermostat = uzigbee.Thermostat(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_thermostat_01",
    sw_build_id="step23",
)

try:
    thermostat.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

thermostat.set_temperature_c(21.5)
thermostat.set_heating_setpoint_c(22.25)
thermostat.set_system_mode(4)

temp = thermostat.get_temperature_c()
setpoint = thermostat.get_heating_setpoint_c()
mode = thermostat.get_system_mode()
stats = z.event_stats()

print("uzigbee.hil.thermostat.temp_c", temp)
print("uzigbee.hil.thermostat.setpoint_c", setpoint)
print("uzigbee.hil.thermostat.mode", mode)
print("uzigbee.hil.thermostat.stats", stats)
assert temp is None or isinstance(temp, float)
assert isinstance(setpoint, float)
assert isinstance(mode, int)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.thermostat.result PASS")
