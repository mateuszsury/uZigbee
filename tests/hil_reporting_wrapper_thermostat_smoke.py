"""HIL smoke for Thermostat.configure_default_reporting helper."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)
thermostat = uzigbee.Thermostat(endpoint_id=1, stack=z, model="uzb_thermostat_reporting")

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

dst = z.get_short_addr()
applied = thermostat.configure_default_reporting(dst_short_addr=dst, dst_endpoint=1)

print("uzigbee.hil.reporting_wrapper.thermostat.dst", hex(dst))
print("uzigbee.hil.reporting_wrapper.thermostat.count", len(applied))
assert len(applied) == 3
print("uzigbee.hil.reporting_wrapper.thermostat.result PASS")
