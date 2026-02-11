"""HIL smoke for high-level uzigbee.PowerOutlet wrapper on ESP32-C6."""

import uzigbee


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
z.init(uzigbee.ROLE_COORDINATOR)

plug = uzigbee.PowerOutlet(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_power_outlet_01",
    sw_build_id="step21",
    with_metering=True,
)

try:
    plug.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=False)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

plug.set_state(True)
plug.set_power(45.2)
plug.set_voltage(230.1)
plug.set_current(0.196)
state = plug.get_state()
power = plug.get_power()
voltage = plug.get_voltage()
current = plug.get_current()

stats = z.event_stats()
print("uzigbee.hil.outlet.state", state)
print("uzigbee.hil.outlet.power", power)
print("uzigbee.hil.outlet.voltage", voltage)
print("uzigbee.hil.outlet.current", current)
print("uzigbee.hil.outlet.stats", stats)
assert isinstance(state, bool)
assert isinstance(power, int)
assert isinstance(voltage, int)
assert isinstance(current, float)
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.outlet.result PASS")
