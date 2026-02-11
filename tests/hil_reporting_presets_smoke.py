"""HIL smoke for python-level reporting presets."""

import uzigbee
from uzigbee import reporting


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)
try:
    z.create_thermostat(1)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    z.register_device()
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise
try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

dst = z.get_short_addr()
applied = reporting.configure_thermostat(z, dst_short_addr=dst, src_endpoint=1, dst_endpoint=1)

print("uzigbee.hil.reporting_preset.dst", hex(dst))
print("uzigbee.hil.reporting_preset.count", len(applied))
assert len(applied) == len(reporting.PRESET_THERMOSTAT)
print("uzigbee.hil.reporting_preset.result PASS")
