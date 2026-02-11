import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStack:
    def __init__(self):
        self.calls = []
        self.state = False
        self.level = 254
        self.temp_raw = -32768
        self.humidity_raw = 0xFFFF
        self.pressure_raw = -32768
        self.power_w = 0
        self.voltage_v = 0
        self.current_ma = 0
        self.color_temp = 250
        self.color_x = 0
        self.color_y = 0
        self.lock_state = 0xFF
        self.thermostat_local_temp = -32768
        self.thermostat_heat_setpoint = 2000
        self.thermostat_system_mode = 1
        self.occupancy = 0
        self.window_lift_percentage = 0xFF
        self.window_tilt_percentage = 0xFF
        self.ias_zone_type = 0x0015
        self.ias_zone_status = 0
        self.attr_callback = None

    def create_on_off_light(self, endpoint):
        self.calls.append(("create_on_off_light", endpoint))

    def create_on_off_switch(self, endpoint):
        self.calls.append(("create_on_off_switch", endpoint))

    def create_dimmable_switch(self, endpoint):
        self.calls.append(("create_dimmable_switch", endpoint))

    def create_dimmable_light(self, endpoint):
        self.calls.append(("create_dimmable_light", endpoint))

    def create_color_light(self, endpoint):
        self.calls.append(("create_color_light", endpoint))

    def create_temperature_sensor(self, endpoint):
        self.calls.append(("create_temperature_sensor", endpoint))

    def create_humidity_sensor(self, endpoint):
        self.calls.append(("create_humidity_sensor", endpoint))

    def create_pressure_sensor(self, endpoint):
        self.calls.append(("create_pressure_sensor", endpoint))

    def create_climate_sensor(self, endpoint):
        self.calls.append(("create_climate_sensor", endpoint))

    def create_power_outlet(self, endpoint, with_metering=False):
        self.calls.append(("create_power_outlet", endpoint, with_metering))

    def create_door_lock(self, endpoint):
        self.calls.append(("create_door_lock", endpoint))

    def create_door_lock_controller(self, endpoint):
        self.calls.append(("create_door_lock_controller", endpoint))

    def create_thermostat(self, endpoint):
        self.calls.append(("create_thermostat", endpoint))

    def create_occupancy_sensor(self, endpoint):
        self.calls.append(("create_occupancy_sensor", endpoint))

    def create_window_covering(self, endpoint):
        self.calls.append(("create_window_covering", endpoint))

    def create_ias_zone(self, endpoint, zone_type=0x0015):
        self.calls.append(("create_ias_zone", endpoint, zone_type))
        self.ias_zone_type = int(zone_type)

    def create_contact_sensor(self, endpoint):
        self.calls.append(("create_contact_sensor", endpoint))
        self.ias_zone_type = 0x0015

    def create_motion_sensor(self, endpoint):
        self.calls.append(("create_motion_sensor", endpoint))
        self.ias_zone_type = 0x000D

    def register_device(self):
        self.calls.append(("register_device",))

    def set_attribute(self, endpoint_id, cluster_id, attr_id, value, cluster_role, check):
        self.calls.append(("set_attribute", endpoint_id, cluster_id, attr_id, value, cluster_role, check))
        attr_type = 0x10
        event_value = value
        if cluster_id == 0x0008 and attr_id == 0x0000:
            self.level = int(value)
            event_value = self.level
            attr_type = 0x20
        elif cluster_id == 0x0402 and attr_id == 0x0000:
            self.temp_raw = int(value)
            event_value = self.temp_raw
            attr_type = 0x29
        elif cluster_id == 0x0405 and attr_id == 0x0000:
            self.humidity_raw = int(value)
            event_value = self.humidity_raw
            attr_type = 0x21
        elif cluster_id == 0x0403 and attr_id == 0x0000:
            self.pressure_raw = int(value)
            event_value = self.pressure_raw
            attr_type = 0x29
        elif cluster_id == 0x0B04 and attr_id == 0x050B:
            self.power_w = int(value)
            event_value = self.power_w
            attr_type = 0x29
        elif cluster_id == 0x0B04 and attr_id == 0x0505:
            self.voltage_v = int(value)
            event_value = self.voltage_v
            attr_type = 0x21
        elif cluster_id == 0x0B04 and attr_id == 0x0508:
            self.current_ma = int(value)
            event_value = self.current_ma
            attr_type = 0x21
        elif cluster_id == 0x0300 and attr_id == 0x0007:
            self.color_temp = int(value)
            event_value = self.color_temp
            attr_type = 0x21
        elif cluster_id == 0x0300 and attr_id == 0x0003:
            self.color_x = int(value)
            event_value = self.color_x
            attr_type = 0x21
        elif cluster_id == 0x0300 and attr_id == 0x0004:
            self.color_y = int(value)
            event_value = self.color_y
            attr_type = 0x21
        elif cluster_id == 0x0101 and attr_id == 0x0000:
            self.lock_state = int(value)
            event_value = self.lock_state
            attr_type = 0x20
        elif cluster_id == 0x0201 and attr_id == 0x0000:
            self.thermostat_local_temp = int(value)
            event_value = self.thermostat_local_temp
            attr_type = 0x29
        elif cluster_id == 0x0201 and attr_id == 0x0012:
            self.thermostat_heat_setpoint = int(value)
            event_value = self.thermostat_heat_setpoint
            attr_type = 0x29
        elif cluster_id == 0x0201 and attr_id == 0x001C:
            self.thermostat_system_mode = int(value)
            event_value = self.thermostat_system_mode
            attr_type = 0x30
        elif cluster_id == 0x0406 and attr_id == 0x0000:
            self.occupancy = int(value)
            event_value = self.occupancy
            attr_type = 0x18
        elif cluster_id == 0x0102 and attr_id == 0x0008:
            self.window_lift_percentage = int(value) & 0xFF
            event_value = self.window_lift_percentage
            attr_type = 0x20
        elif cluster_id == 0x0102 and attr_id == 0x0009:
            self.window_tilt_percentage = int(value) & 0xFF
            event_value = self.window_tilt_percentage
            attr_type = 0x20
        elif cluster_id == 0x0500 and attr_id == 0x0002:
            self.ias_zone_status = int(value)
            event_value = self.ias_zone_status
            attr_type = 0x19
        else:
            self.state = bool(value)
            event_value = self.state
        if self.attr_callback is not None:
            self.attr_callback(endpoint_id, cluster_id, attr_id, event_value, attr_type, 0)

    def get_attribute(self, endpoint_id, cluster_id, attr_id, cluster_role):
        self.calls.append(("get_attribute", endpoint_id, cluster_id, attr_id, cluster_role))
        if cluster_id == 0x0008 and attr_id == 0x0000:
            return self.level
        if cluster_id == 0x0402 and attr_id == 0x0000:
            return self.temp_raw
        if cluster_id == 0x0405 and attr_id == 0x0000:
            return self.humidity_raw
        if cluster_id == 0x0403 and attr_id == 0x0000:
            return self.pressure_raw
        if cluster_id == 0x0B04 and attr_id == 0x050B:
            return self.power_w
        if cluster_id == 0x0B04 and attr_id == 0x0505:
            return self.voltage_v
        if cluster_id == 0x0B04 and attr_id == 0x0508:
            return self.current_ma
        if cluster_id == 0x0300 and attr_id == 0x0007:
            return self.color_temp
        if cluster_id == 0x0300 and attr_id == 0x0003:
            return self.color_x
        if cluster_id == 0x0300 and attr_id == 0x0004:
            return self.color_y
        if cluster_id == 0x0101 and attr_id == 0x0000:
            return self.lock_state
        if cluster_id == 0x0201 and attr_id == 0x0000:
            return self.thermostat_local_temp
        if cluster_id == 0x0201 and attr_id == 0x0012:
            return self.thermostat_heat_setpoint
        if cluster_id == 0x0201 and attr_id == 0x001C:
            return self.thermostat_system_mode
        if cluster_id == 0x0406 and attr_id == 0x0000:
            return self.occupancy
        if cluster_id == 0x0102 and attr_id == 0x0008:
            return self.window_lift_percentage
        if cluster_id == 0x0102 and attr_id == 0x0009:
            return self.window_tilt_percentage
        if cluster_id == 0x0500 and attr_id == 0x0001:
            return self.ias_zone_type
        if cluster_id == 0x0500 and attr_id == 0x0002:
            return self.ias_zone_status
        return self.state

    def on_attribute(self, callback):
        self.calls.append(("on_attribute", callback))
        self.attr_callback = callback

    def send_on_off_cmd(self, dst_short_addr, dst_endpoint=1, src_endpoint=1, cmd_id=0x02):
        self.calls.append(("send_on_off_cmd", src_endpoint, dst_short_addr, dst_endpoint, cmd_id))
        return None

    def send_level_cmd(self, dst_short_addr, level, dst_endpoint=1, src_endpoint=1, transition_ds=0, with_onoff=True):
        self.calls.append(("send_level_cmd", src_endpoint, dst_short_addr, dst_endpoint, level, transition_ds, with_onoff))
        return None

    def send_lock_cmd(self, dst_short_addr, lock=True, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_lock_cmd", src_endpoint, dst_short_addr, dst_endpoint, lock))
        return None

    def send_group_add_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_group_add_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))
        return None

    def send_group_remove_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_group_remove_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))
        return None

    def send_group_remove_all_cmd(self, dst_short_addr, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_group_remove_all_cmd", src_endpoint, dst_short_addr, dst_endpoint))
        return None

    def configure_reporting(
        self,
        src_endpoint,
        dst_short_addr,
        dst_endpoint,
        cluster_id,
        attr_id,
        attr_type,
        min_interval,
        max_interval,
        reportable_change,
    ):
        self.calls.append(
            (
                "configure_reporting",
                src_endpoint,
                dst_short_addr,
                dst_endpoint,
                cluster_id,
                attr_id,
                attr_type,
                min_interval,
                max_interval,
                reportable_change,
            )
        )
        return None


def test_light_provision_invokes_core_and_identity():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        light = devices.Light(endpoint_id=7, stack=fake, manufacturer="acme", model="acme_light_01")
        out = light.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is light
    assert fake.calls[0] == ("create_on_off_light", 7)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["endpoint_id"] == 7
    assert calls[0]["manufacturer"] == "acme"
    assert calls[0]["model"] == "acme_light_01"


def test_light_state_and_toggle():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    light = devices.Light(endpoint_id=3, stack=fake)

    assert light.set_state(True) is True
    assert light.get_state() is True
    assert light.toggle() is False
    assert light.state is False

    set_calls = [c for c in fake.calls if c[0] == "set_attribute"]
    assert len(set_calls) >= 2
    assert set_calls[0][4] is True
    assert set_calls[1][4] is False


def test_light_on_change_receives_filtered_updates():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    light = devices.Light(endpoint_id=5, stack=fake)
    events = []

    light.on_change(lambda state: events.append(state))
    assert any(c[0] == "on_attribute" for c in fake.calls)

    fake.attr_callback(5, 0x0006, 0x0000, True, 0x10, 0)
    fake.attr_callback(5, 0x0008, 0x0000, False, 0x10, 0)  # wrong cluster
    fake.attr_callback(5, 0x0006, 0x0000, False, 0x10, 0)
    fake.attr_callback(5, 0x0006, 0x0000, True, 0x10, 1)  # non-zero status
    fake.attr_callback(6, 0x0006, 0x0000, True, 0x10, 0)  # wrong endpoint

    assert events == [True, False]


def test_dimmable_light_provision_uses_dimmable_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        light = devices.DimmableLight(endpoint_id=9, stack=fake, model="uzb_DimmableLight")
        out = light.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is light
    assert fake.calls[0] == ("create_dimmable_light", 9)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_DimmableLight"


def test_dimmable_light_brightness_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    light = devices.DimmableLight(endpoint_id=2, stack=fake)
    values = []

    light.on_brightness_change(lambda level: values.append(level))
    assert light.set_brightness(180) == 180
    assert light.get_brightness() == 180
    assert light.set_brightness(999) == 254
    assert light.brightness == 254
    light.brightness = -4
    assert light.get_brightness() == 0
    assert any(c[0] == "on_attribute" for c in fake.calls)
    assert values == [180, 254, 0]


def test_color_light_provision_uses_color_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        light = devices.ColorLight(endpoint_id=11, stack=fake, model="uzb_ColorLight")
        out = light.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is light
    assert fake.calls[0] == ("create_color_light", 11)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_ColorLight"


def test_color_light_temp_xy_and_callbacks():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    light = devices.ColorLight(endpoint_id=4, stack=fake)
    temps = []
    xys = []

    light.on_color_temperature_change(lambda mireds: temps.append(mireds))
    light.on_xy_change(lambda xy: xys.append(xy))

    assert light.set_color_temperature(140) == 153
    assert light.get_color_temperature() == 153
    assert light.set_color_temperature(999) == 500
    assert light.color_temperature == 500
    light.color_temperature = 200
    assert light.get_color_temperature() == 200

    assert light.set_xy(-1, 70000) == (0, 65535)
    assert light.get_xy() == (0, 65535)
    assert light.set_xy(12345, 22222) == (12345, 22222)
    assert light.get_xy() == (12345, 22222)

    assert any(c[0] == "on_attribute" for c in fake.calls)
    assert temps == [153, 500, 200]
    assert xys == [(0, 0), (0, 65535), (12345, 65535), (12345, 22222)]


def test_switch_provision_uses_switch_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        switch = devices.Switch(endpoint_id=6, stack=fake, model="uzb_Switch")
        out = switch.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is switch
    assert fake.calls[0] == ("create_on_off_switch", 6)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_Switch"


def test_switch_send_on_off_toggle():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    switch = devices.Switch(endpoint_id=7, stack=fake)

    switch.send_on(0x1234, 2)
    switch.send_off(0x1234, 2)
    switch.toggle(0x1234, 2)

    sends = [c for c in fake.calls if c[0] == "send_on_off_cmd"]
    assert sends == [
        ("send_on_off_cmd", 7, 0x1234, 2, 0x01),
        ("send_on_off_cmd", 7, 0x1234, 2, 0x00),
        ("send_on_off_cmd", 7, 0x1234, 2, 0x02),
    ]


def test_switch_group_helpers():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    switch = devices.Switch(endpoint_id=7, stack=fake)

    assert switch.add_to_group(0x1234, 0x3344, dst_endpoint=2) == 0x3344
    assert switch.remove_from_group(0x1234, 0x3344, dst_endpoint=2) == 0x3344
    assert switch.clear_groups(0x1234, dst_endpoint=2) is True

    calls = [c for c in fake.calls if c[0].startswith("send_group_")]
    assert calls == [
        ("send_group_add_cmd", 7, 0x1234, 2, 0x3344),
        ("send_group_remove_cmd", 7, 0x1234, 2, 0x3344),
        ("send_group_remove_all_cmd", 7, 0x1234, 2),
    ]


def test_dimmable_switch_provision_uses_dimmable_switch_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        switch = devices.DimmableSwitch(endpoint_id=8, stack=fake, model="uzb_DimmableSwitch")
        out = switch.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is switch
    assert fake.calls[0] == ("create_dimmable_switch", 8)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_DimmableSwitch"


def test_dimmable_switch_send_level():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    switch = devices.DimmableSwitch(endpoint_id=9, stack=fake)

    switch.send_level(0x1234, 200, dst_endpoint=3, transition_ds=15, with_onoff=False)
    switch.send_level(0x1234, 999, dst_endpoint=3, transition_ds=0, with_onoff=True)
    switch.set_brightness(0x1234, -5, dst_endpoint=3, transition_ds=1)

    levels = [c for c in fake.calls if c[0] == "send_level_cmd"]
    assert levels == [
        ("send_level_cmd", 9, 0x1234, 3, 200, 15, False),
        ("send_level_cmd", 9, 0x1234, 3, 254, 0, True),
        ("send_level_cmd", 9, 0x1234, 3, 0, 1, True),
    ]


def test_temperature_sensor_provision_uses_temperature_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.TemperatureSensor(endpoint_id=10, stack=fake, model="uzb_TemperatureSensor")
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_temperature_sensor", 10)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_TemperatureSensor"


def test_temperature_sensor_read_write_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    sensor = devices.TemperatureSensor(endpoint_id=11, stack=fake)
    readings = []

    sensor.on_temperature_change(lambda c: readings.append(c))
    assert sensor.set_temperature_raw(2156) == 2156
    assert sensor.get_temperature_raw() == 2156
    assert sensor.get_temperature_c() == 21.56
    assert sensor.set_temperature_c(-300.0) == -30000
    assert sensor.get_temperature_c() == -300.0
    assert sensor.set_temperature_raw(-50000) == -32767
    assert sensor.get_temperature_raw() == -32767
    assert sensor.temperature_c == -327.67
    assert any(c[0] == "on_attribute" for c in fake.calls)
    assert readings[0] == 21.56
    assert readings[-1] == -327.67


def test_humidity_sensor_provision_uses_humidity_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.HumiditySensor(endpoint_id=12, stack=fake, model="uzb_HumiditySensor")
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_humidity_sensor", 12)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_HumiditySensor"


def test_humidity_sensor_read_write_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    sensor = devices.HumiditySensor(endpoint_id=13, stack=fake)
    readings = []

    sensor.on_humidity_change(lambda p: readings.append(p))
    assert sensor.set_humidity_raw(4567) == 4567
    assert sensor.get_humidity_raw() == 4567
    assert sensor.get_humidity_percent() == 45.67
    assert sensor.set_humidity_percent(101.3) == 10000
    assert sensor.get_humidity_percent() == 100.0
    assert sensor.set_humidity_raw(-50) == 0
    assert sensor.get_humidity_raw() == 0
    assert sensor.humidity_percent == 0.0
    assert any(c[0] == "on_attribute" for c in fake.calls)
    assert readings[0] == 45.67
    assert readings[-1] == 0.0


def test_pressure_sensor_provision_uses_pressure_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.PressureSensor(endpoint_id=14, stack=fake, model="uzb_PressureSensor")
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_pressure_sensor", 14)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_PressureSensor"


def test_pressure_sensor_read_write_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    sensor = devices.PressureSensor(endpoint_id=15, stack=fake)
    readings = []

    sensor.on_pressure_change(lambda p: readings.append(p))
    assert sensor.set_pressure_raw(1013) == 1013
    assert sensor.get_pressure_raw() == 1013
    assert sensor.get_pressure_hpa() == 1013.0
    assert sensor.set_pressure_hpa(998.7) == 999
    assert sensor.get_pressure_hpa() == 999.0
    assert sensor.set_pressure_raw(-50000) == -32767
    assert sensor.get_pressure_raw() == -32767
    assert sensor.pressure_hpa == -32767.0
    assert any(c[0] == "on_attribute" for c in fake.calls)
    assert readings[0] == 1013.0
    assert readings[-1] == -32767.0


def test_climate_sensor_provision_uses_climate_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.ClimateSensor(endpoint_id=16, stack=fake, model="uzb_ClimateSensor")
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_climate_sensor", 16)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_ClimateSensor"


def test_climate_sensor_read_write_and_callbacks():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    sensor = devices.ClimateSensor(endpoint_id=17, stack=fake)
    t_values = []
    h_values = []
    p_values = []

    sensor.on_temperature_change(lambda c: t_values.append(c))
    sensor.on_humidity_change(lambda p: h_values.append(p))
    sensor.on_pressure_change(lambda p: p_values.append(p))

    assert sensor.set_temperature_c(22.34) == 2234
    assert sensor.get_temperature_c() == 22.34
    assert sensor.set_humidity_percent(49.25) == 4925
    assert sensor.get_humidity_percent() == 49.25
    assert sensor.set_pressure_hpa(1001.4) == 1001
    assert sensor.get_pressure_hpa() == 1001.0
    assert sensor.temperature_c == 22.34
    assert sensor.humidity_percent == 49.25
    assert sensor.pressure_hpa == 1001.0
    assert any(c[0] == "on_attribute" for c in fake.calls)
    assert t_values[-1] == 22.34
    assert h_values[-1] == 49.25
    assert p_values[-1] == 1001.0


def test_power_outlet_provision_uses_power_outlet_creator():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        outlet = devices.PowerOutlet(endpoint_id=18, stack=fake, model="uzb_PowerOutlet", with_metering=True)
        out = outlet.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is outlet
    assert fake.calls[0] == ("create_power_outlet", 18, True)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_PowerOutlet"


def test_power_outlet_measurements_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    outlet = devices.PowerOutlet(endpoint_id=19, stack=fake, with_metering=True)
    values = []

    outlet.on_measurement_change(lambda payload: values.append(payload))
    assert outlet.set_power(45.2) == 45
    assert outlet.get_power() == 45
    assert outlet.set_voltage(230.1) == 230
    assert outlet.get_voltage() == 230
    assert outlet.set_current(0.196) == 0.196
    assert round(outlet.get_current(), 3) == 0.196
    assert outlet.power_w == 45
    assert outlet.voltage_v == 230
    assert round(outlet.current_a, 3) == 0.196
    assert values[-1]["power_w"] == 45
    assert values[-1]["voltage_v"] == 230
    assert round(values[-1]["current_a"], 3) == 0.196


def test_door_lock_provision_and_state_callbacks():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    events = []
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        lock = devices.DoorLock(endpoint_id=20, stack=fake, model="uzb_DoorLock")
        out = lock.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is lock
    assert fake.calls[0] == ("create_door_lock", 20)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_DoorLock"

    lock.on_lock_change(lambda state: events.append(state))
    assert lock.lock() is True
    assert lock.unlock() is False
    assert lock.get_lock_state() == 2
    assert lock.locked is False
    assert events == [True, False]


def test_door_lock_controller_provision_and_send_commands():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        controller = devices.DoorLockController(endpoint_id=21, stack=fake, model="uzb_DoorLockController")
        out = controller.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is controller
    assert fake.calls[0] == ("create_door_lock_controller", 21)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_DoorLockController"

    controller.send_lock(0x1234, 2)
    controller.send_unlock(0x1234, 2)
    sends = [c for c in fake.calls if c[0] == "send_lock_cmd"]
    assert sends == [
        ("send_lock_cmd", 21, 0x1234, 2, True),
        ("send_lock_cmd", 21, 0x1234, 2, False),
    ]


def test_thermostat_provision_read_write_and_callbacks():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    events = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        thermostat = devices.Thermostat(endpoint_id=22, stack=fake, model="uzb_Thermostat")
        out = thermostat.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is thermostat
    assert fake.calls[0] == ("create_thermostat", 22)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_Thermostat"

    thermostat.on_change(lambda payload: events.append(payload))
    assert thermostat.set_temperature_c(21.5) == 21.5
    assert thermostat.get_temperature_c() == 21.5
    assert thermostat.set_heating_setpoint_c(22.75) == 22.75
    assert thermostat.get_heating_setpoint_c() == 22.75
    assert thermostat.set_system_mode(4) == 4
    assert thermostat.get_system_mode() == 4
    assert events[-1]["system_mode"] == 4
    assert round(events[-1]["heating_setpoint_c"], 2) == 22.75


def test_occupancy_sensor_provision_and_callbacks():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    events = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.OccupancySensor(endpoint_id=23, stack=fake, model="uzb_OccupancySensor")
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_occupancy_sensor", 23)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_OccupancySensor"

    sensor.on_change(lambda occupied: events.append(occupied))
    assert sensor.set_occupied(True) is True
    assert sensor.get_occupied() is True
    assert sensor.set_occupied(False) is False
    assert sensor.occupied is False
    assert events == [True, False]


def test_window_covering_provision_position_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    events = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        cover = devices.WindowCovering(endpoint_id=27, stack=fake, model="uzb_WindowCovering")
        out = cover.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is cover
    assert fake.calls[0] == ("create_window_covering", 27)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_WindowCovering"

    cover.on_change(lambda payload: events.append(payload))
    assert cover.set_lift_percentage(35) == 35
    assert cover.get_lift_percentage() == 35
    assert cover.set_tilt_percentage(200) == 100
    assert cover.get_tilt_percentage() == 100
    cover.position = -10
    assert cover.position == 0
    assert events[-1]["lift_percentage"] == 0
    assert events[-1]["tilt_percentage"] == 100


def test_ias_zone_provision_and_status():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    events = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.IASZone(endpoint_id=24, stack=fake, model="uzb_IASZone", zone_type=0x0028)
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_ias_zone", 24, 0x0028)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_IASZone"

    sensor.on_change(lambda alarm: events.append(alarm))
    assert sensor.set_zone_status(0x0001) == 0x0001
    assert sensor.get_zone_status() == 0x0001
    assert sensor.alarm is True
    assert sensor.get_zone_type() == 0x0028
    assert sensor.set_alarm(False) is False
    assert sensor.alarm is False
    assert events == [True, False]


def test_contact_sensor_provision_state_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    events = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.ContactSensor(endpoint_id=25, stack=fake, model="uzb_ContactSensor")
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_contact_sensor", 25)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_ContactSensor"

    sensor.on_change(lambda contact: events.append(contact))
    assert sensor.set_contact(True) is True
    assert sensor.get_contact() is True
    assert sensor.set_contact(False) is False
    assert sensor.contact is False
    assert events == [True, False]


def test_motion_sensor_provision_state_and_callback():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()
    calls = []
    events = []
    old_set_identity = devices.set_identity
    try:
        def _fake_set_identity(**kwargs):
            calls.append(kwargs)
            return kwargs

        devices.set_identity = _fake_set_identity
        sensor = devices.MotionSensor(endpoint_id=26, stack=fake, model="uzb_MotionSensor")
        out = sensor.provision(register=True)
    finally:
        devices.set_identity = old_set_identity

    assert out is sensor
    assert fake.calls[0] == ("create_motion_sensor", 26)
    assert fake.calls[1] == ("register_device",)
    assert calls and calls[0]["model"] == "uzb_MotionSensor"

    sensor.on_change(lambda motion: events.append(motion))
    assert sensor.set_motion(True) is True
    assert sensor.get_motion() is True
    assert sensor.set_motion(False) is False
    assert sensor.motion is False
    assert events == [True, False]


def test_default_reporting_helpers_for_ha_wrappers():
    devices = importlib.import_module("uzigbee.devices")
    fake = _FakeStack()

    lock = devices.DoorLock(endpoint_id=31, stack=fake)
    thermostat = devices.Thermostat(endpoint_id=32, stack=fake)
    occupancy = devices.OccupancySensor(endpoint_id=33, stack=fake)
    contact = devices.ContactSensor(endpoint_id=34, stack=fake)
    motion = devices.MotionSensor(endpoint_id=35, stack=fake)

    lock.configure_default_reporting(dst_short_addr=0x1234, dst_endpoint=2)
    thermostat.configure_default_reporting(dst_short_addr=0x1234, dst_endpoint=2)
    occupancy.configure_default_reporting(dst_short_addr=0x1234, dst_endpoint=2)
    contact.configure_default_reporting(dst_short_addr=0x1234, dst_endpoint=2)
    motion.configure_default_reporting(dst_short_addr=0x1234, dst_endpoint=2)

    reporting_calls = [c for c in fake.calls if c[0] == "configure_reporting"]
    assert len(reporting_calls) == 7
    assert reporting_calls[0] == ("configure_reporting", 31, 0x1234, 2, 0x0101, 0x0000, 0x30, 0, 3600, 1)
    assert reporting_calls[1] == ("configure_reporting", 32, 0x1234, 2, 0x0201, 0x0000, 0x29, 10, 300, 50)
    assert reporting_calls[2] == ("configure_reporting", 32, 0x1234, 2, 0x0201, 0x0012, 0x29, 5, 600, 50)
    assert reporting_calls[3] == ("configure_reporting", 32, 0x1234, 2, 0x0201, 0x001C, 0x30, 1, 3600, 1)
    assert reporting_calls[4] == ("configure_reporting", 33, 0x1234, 2, 0x0406, 0x0000, 0x18, 1, 300, 1)
    assert reporting_calls[5] == ("configure_reporting", 34, 0x1234, 2, 0x0500, 0x0002, 0x19, 1, 300, 1)
    assert reporting_calls[6] == ("configure_reporting", 35, 0x1234, 2, 0x0500, 0x0002, 0x19, 1, 300, 1)
