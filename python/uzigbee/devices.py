"""High-level Zigbee device wrappers."""

from .core import (
    ATTR_COLOR_CONTROL_COLOR_TEMPERATURE,
    ATTR_COLOR_CONTROL_CURRENT_X,
    ATTR_COLOR_CONTROL_CURRENT_Y,
    ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER,
    ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT,
    ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE,
    ATTR_LEVEL_CONTROL_CURRENT_LEVEL,
    ATTR_DOOR_LOCK_LOCK_STATE,
    ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE,
    ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE,
    ATTR_THERMOSTAT_LOCAL_TEMPERATURE,
    ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
    ATTR_THERMOSTAT_SYSTEM_MODE,
    ATTR_IAS_ZONE_STATUS,
    ATTR_IAS_ZONE_TYPE,
    ATTR_PRESSURE_MEASUREMENT_VALUE,
    ATTR_REL_HUMIDITY_MEASUREMENT_VALUE,
    ATTR_OCCUPANCY_SENSING_OCCUPANCY,
    ATTR_ON_OFF_ON_OFF,
    ATTR_TEMP_MEASUREMENT_VALUE,
    BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    CLUSTER_ID_COLOR_CONTROL,
    CLUSTER_ID_DOOR_LOCK,
    CLUSTER_ID_WINDOW_COVERING,
    CLUSTER_ID_THERMOSTAT,
    CLUSTER_ID_IAS_ZONE,
    CLUSTER_ID_ELECTRICAL_MEASUREMENT,
    CLUSTER_ID_LEVEL_CONTROL,
    CLUSTER_ID_ON_OFF,
    CLUSTER_ID_OCCUPANCY_SENSING,
    CLUSTER_ID_PRESSURE_MEASUREMENT,
    CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
    CLUSTER_ID_TEMP_MEASUREMENT,
    CLUSTER_ROLE_SERVER,
    CMD_ON_OFF_OFF,
    CMD_ON_OFF_ON,
    CMD_ON_OFF_TOGGLE,
    CMD_DOOR_LOCK_LOCK_DOOR,
    CMD_DOOR_LOCK_UNLOCK_DOOR,
    IAS_ZONE_TYPE_CONTACT_SWITCH,
    IAS_ZONE_TYPE_MOTION,
    IAS_ZONE_STATUS_ALARM1,
    ZigbeeStack,
)
from . import groups as groups_helper
from . import scenes as scenes_helper
from . import reporting as reporting_presets
from .z2m import set_identity, validate


_LIGHT_DISPATCHERS = {}
_LIGHT_REGISTRY = {}


class Light:
    """Minimal high-level On/Off light wrapper."""

    Z2M_MODEL_ID = "uzb_Light"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_state_cache",
        "_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._state_cache = False
        self._change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_on_off_light(self.endpoint_id)

    def provision(self, register=True):
        """Create endpoint, configure Basic identity, optionally register device."""
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def get_state(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_ON_OFF,
            ATTR_ON_OFF_ON_OFF,
            CLUSTER_ROLE_SERVER,
        )
        self._state_cache = bool(value)
        return self._state_cache

    def set_state(self, value, check=False):
        state = bool(value)
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_ON_OFF,
            ATTR_ON_OFF_ON_OFF,
            state,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._state_cache = state
        return state

    @property
    def state(self):
        return self.get_state()

    @state.setter
    def state(self, value):
        self.set_state(value)

    def toggle(self, check=False):
        return self.set_state(not self.get_state(), check=check)

    def on_change(self, callback=None):
        """Register callback(state: bool) for local On/Off attribute updates."""
        self._change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_ON_OFF:
            return
        if int(attr_id) != ATTR_ON_OFF_ON_OFF:
            return
        self._state_cache = bool(value)
        if self._change_cb is not None:
            self._change_cb(self._state_cache)


class DimmableLight(Light):
    """High-level dimmable light wrapper (On/Off + Level Control)."""

    Z2M_MODEL_ID = "uzb_DimmableLight"

    __slots__ = ("_brightness_cache", "_brightness_cb")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._brightness_cache = 254
        self._brightness_cb = None

    def _create_endpoint(self):
        self._stack.create_dimmable_light(self.endpoint_id)

    def get_brightness(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_LEVEL_CONTROL,
            ATTR_LEVEL_CONTROL_CURRENT_LEVEL,
            CLUSTER_ROLE_SERVER,
        )
        self._brightness_cache = int(value)
        return self._brightness_cache

    def set_brightness(self, value, check=False):
        level = int(value)
        if level < 0:
            level = 0
        if level > 254:
            level = 254
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_LEVEL_CONTROL,
            ATTR_LEVEL_CONTROL_CURRENT_LEVEL,
            level,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._brightness_cache = level
        return level

    @property
    def brightness(self):
        return self.get_brightness()

    @brightness.setter
    def brightness(self, value):
        self.set_brightness(value)

    def on_brightness_change(self, callback=None):
        self._brightness_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        super()._handle_attr_event(endpoint, cluster_id, attr_id, value, status)
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_LEVEL_CONTROL:
            return
        if int(attr_id) != ATTR_LEVEL_CONTROL_CURRENT_LEVEL:
            return
        self._brightness_cache = int(value)
        if self._brightness_cb is not None:
            self._brightness_cb(self._brightness_cache)


class ColorLight(DimmableLight):
    """High-level color dimmable light wrapper."""

    Z2M_MODEL_ID = "uzb_ColorLight"

    __slots__ = ("_color_temp_cache", "_xy_cache", "_color_temp_cb", "_xy_cb")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._color_temp_cache = 250
        self._xy_cache = (0, 0)
        self._color_temp_cb = None
        self._xy_cb = None

    def _create_endpoint(self):
        self._stack.create_color_light(self.endpoint_id)

    def get_color_temperature(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_COLOR_CONTROL,
            ATTR_COLOR_CONTROL_COLOR_TEMPERATURE,
            CLUSTER_ROLE_SERVER,
        )
        self._color_temp_cache = int(value)
        return self._color_temp_cache

    def set_color_temperature(self, value, check=False):
        mireds = int(value)
        if mireds < 153:
            mireds = 153
        if mireds > 500:
            mireds = 500
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_COLOR_CONTROL,
            ATTR_COLOR_CONTROL_COLOR_TEMPERATURE,
            mireds,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._color_temp_cache = mireds
        return mireds

    @property
    def color_temperature(self):
        return self.get_color_temperature()

    @color_temperature.setter
    def color_temperature(self, value):
        self.set_color_temperature(value)

    def get_xy(self):
        x = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_COLOR_CONTROL,
            ATTR_COLOR_CONTROL_CURRENT_X,
            CLUSTER_ROLE_SERVER,
        )
        y = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_COLOR_CONTROL,
            ATTR_COLOR_CONTROL_CURRENT_Y,
            CLUSTER_ROLE_SERVER,
        )
        self._xy_cache = (int(x), int(y))
        return self._xy_cache

    def set_xy(self, x, y, check=False):
        current_x = int(x)
        current_y = int(y)
        if current_x < 0:
            current_x = 0
        if current_x > 0xFFFF:
            current_x = 0xFFFF
        if current_y < 0:
            current_y = 0
        if current_y > 0xFFFF:
            current_y = 0xFFFF
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_COLOR_CONTROL,
            ATTR_COLOR_CONTROL_CURRENT_X,
            current_x,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_COLOR_CONTROL,
            ATTR_COLOR_CONTROL_CURRENT_Y,
            current_y,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._xy_cache = (current_x, current_y)
        return self._xy_cache

    def on_color_temperature_change(self, callback=None):
        self._color_temp_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def on_xy_change(self, callback=None):
        self._xy_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        super()._handle_attr_event(endpoint, cluster_id, attr_id, value, status)
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_COLOR_CONTROL:
            return
        attr = int(attr_id)
        if attr == ATTR_COLOR_CONTROL_COLOR_TEMPERATURE:
            self._color_temp_cache = int(value)
            if self._color_temp_cb is not None:
                self._color_temp_cb(self._color_temp_cache)
            return
        if attr == ATTR_COLOR_CONTROL_CURRENT_X:
            self._xy_cache = (int(value), self._xy_cache[1])
        elif attr == ATTR_COLOR_CONTROL_CURRENT_Y:
            self._xy_cache = (self._xy_cache[0], int(value))
        else:
            return
        if self._xy_cb is not None:
            self._xy_cb(self._xy_cache)


class Switch:
    """High-level on/off switch wrapper for outgoing On/Off commands."""

    Z2M_MODEL_ID = "uzb_Switch"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_on_off_switch(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def send_on(self, dst_short_addr, dst_endpoint=1):
        return self._stack.send_on_off_cmd(
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            src_endpoint=self.endpoint_id,
            cmd_id=CMD_ON_OFF_ON,
        )

    def send_off(self, dst_short_addr, dst_endpoint=1):
        return self._stack.send_on_off_cmd(
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            src_endpoint=self.endpoint_id,
            cmd_id=CMD_ON_OFF_OFF,
        )

    def toggle(self, dst_short_addr, dst_endpoint=1):
        return self._stack.send_on_off_cmd(
            dst_short_addr=int(dst_short_addr),
            dst_endpoint=int(dst_endpoint),
            src_endpoint=self.endpoint_id,
            cmd_id=CMD_ON_OFF_TOGGLE,
        )

    def add_to_group(self, dst_short_addr, group_id, dst_endpoint=1):
        return groups_helper.add_group(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            group_id=int(group_id),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def remove_from_group(self, dst_short_addr, group_id, dst_endpoint=1):
        return groups_helper.remove_group(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            group_id=int(group_id),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def clear_groups(self, dst_short_addr, dst_endpoint=1):
        return groups_helper.remove_all_groups(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def add_scene(self, dst_short_addr, group_id, scene_id, dst_endpoint=1, transition_ds=0):
        return scenes_helper.add_scene(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            group_id=int(group_id),
            scene_id=int(scene_id),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
            transition_ds=int(transition_ds),
        )

    def remove_scene(self, dst_short_addr, group_id, scene_id, dst_endpoint=1):
        return scenes_helper.remove_scene(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            group_id=int(group_id),
            scene_id=int(scene_id),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def clear_scenes(self, dst_short_addr, group_id, dst_endpoint=1):
        return scenes_helper.remove_all_scenes(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            group_id=int(group_id),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def recall_scene(self, dst_short_addr, group_id, scene_id, dst_endpoint=1):
        return scenes_helper.recall_scene(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            group_id=int(group_id),
            scene_id=int(scene_id),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )


class DimmableSwitch(Switch):
    """High-level dimmable switch wrapper (On/Off + Level commands)."""

    Z2M_MODEL_ID = "uzb_DimmableSwitch"

    def _create_endpoint(self):
        self._stack.create_dimmable_switch(self.endpoint_id)

    def send_level(self, dst_short_addr, level, dst_endpoint=1, transition_ds=0, with_onoff=True):
        current_level = int(level)
        if current_level < 0:
            current_level = 0
        if current_level > 254:
            current_level = 254
        return self._stack.send_level_cmd(
            dst_short_addr=int(dst_short_addr),
            level=current_level,
            dst_endpoint=int(dst_endpoint),
            src_endpoint=self.endpoint_id,
            transition_ds=int(transition_ds),
            with_onoff=bool(with_onoff),
        )

    def set_brightness(self, dst_short_addr, level, dst_endpoint=1, transition_ds=0):
        return self.send_level(
            dst_short_addr=dst_short_addr,
            level=level,
            dst_endpoint=dst_endpoint,
            transition_ds=transition_ds,
            with_onoff=True,
        )


class PowerOutlet(Light):
    """High-level mains power outlet wrapper (On/Off + optional measurements)."""

    Z2M_MODEL_ID = "uzb_PowerOutlet"

    __slots__ = ("with_metering", "_power_cache", "_voltage_cache", "_current_cache", "_measurement_cb")

    def __init__(self, *args, with_metering=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.with_metering = bool(with_metering)
        self._power_cache = 0
        self._voltage_cache = 0
        self._current_cache = 0
        self._measurement_cb = None

    def _create_endpoint(self):
        self._stack.create_power_outlet(self.endpoint_id, with_metering=self.with_metering)

    def get_power(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER,
            CLUSTER_ROLE_SERVER,
        )
        self._power_cache = int(value)
        return self._power_cache

    def get_voltage(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE,
            CLUSTER_ROLE_SERVER,
        )
        self._voltage_cache = int(value)
        return self._voltage_cache

    def get_current(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT,
            CLUSTER_ROLE_SERVER,
        )
        self._current_cache = int(value)
        return self._current_cache / 1000.0

    @property
    def power_w(self):
        return self.get_power()

    @property
    def voltage_v(self):
        return self.get_voltage()

    @property
    def current_a(self):
        return self.get_current()

    def set_power(self, watts, check=False):
        value = int(round(float(watts)))
        if value < -32767:
            value = -32767
        if value > 32767:
            value = 32767
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER,
            value,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._power_cache = value
        return value

    def set_voltage(self, volts, check=False):
        value = int(round(float(volts)))
        if value < 0:
            value = 0
        if value > 0xFFFF:
            value = 0xFFFF
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE,
            value,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._voltage_cache = value
        return value

    def set_current(self, amps, check=False):
        value_ma = int(round(float(amps) * 1000.0))
        if value_ma < 0:
            value_ma = 0
        if value_ma > 0xFFFF:
            value_ma = 0xFFFF
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_ELECTRICAL_MEASUREMENT,
            ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT,
            value_ma,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._current_cache = value_ma
        return self._current_cache / 1000.0

    def on_measurement_change(self, callback=None):
        self._measurement_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        super()._handle_attr_event(endpoint, cluster_id, attr_id, value, status)
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_ELECTRICAL_MEASUREMENT:
            return

        attr = int(attr_id)
        if attr == ATTR_ELECTRICAL_MEASUREMENT_ACTIVE_POWER:
            self._power_cache = int(value)
        elif attr == ATTR_ELECTRICAL_MEASUREMENT_RMSVOLTAGE:
            self._voltage_cache = int(value)
        elif attr == ATTR_ELECTRICAL_MEASUREMENT_RMSCURRENT:
            self._current_cache = int(value)
        else:
            return

        if self._measurement_cb is not None:
            self._measurement_cb(
                {
                    "power_w": self._power_cache,
                    "voltage_v": self._voltage_cache,
                    "current_a": self._current_cache / 1000.0,
                }
            )


class TemperatureSensor:
    """High-level temperature sensor wrapper (local measured-value updates)."""

    Z2M_MODEL_ID = "uzb_TemperatureSensor"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_temp_raw_cache",
        "_temp_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._temp_raw_cache = -32768
        self._temp_change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_temperature_sensor(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def get_temperature_raw(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_TEMP_MEASUREMENT,
            ATTR_TEMP_MEASUREMENT_VALUE,
            CLUSTER_ROLE_SERVER,
        )
        self._temp_raw_cache = int(value)
        return self._temp_raw_cache

    def get_temperature_c(self):
        raw = self.get_temperature_raw()
        if raw == -32768:
            return None
        return raw / 100.0

    @property
    def temperature_c(self):
        return self.get_temperature_c()

    def set_temperature_raw(self, value, check=False):
        current = int(value)
        if current < -32767:
            current = -32767
        if current > 32767:
            current = 32767
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_TEMP_MEASUREMENT,
            ATTR_TEMP_MEASUREMENT_VALUE,
            current,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._temp_raw_cache = current
        return current

    def set_temperature_c(self, value, check=False):
        raw = int(round(float(value) * 100.0))
        return self.set_temperature_raw(raw, check=check)

    def on_temperature_change(self, callback=None):
        self._temp_change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_TEMP_MEASUREMENT:
            return
        if int(attr_id) != ATTR_TEMP_MEASUREMENT_VALUE:
            return
        self._temp_raw_cache = int(value)
        if self._temp_change_cb is not None:
            if self._temp_raw_cache == -32768:
                self._temp_change_cb(None)
            else:
                self._temp_change_cb(self._temp_raw_cache / 100.0)


class HumiditySensor:
    """High-level humidity sensor wrapper (local measured-value updates)."""

    Z2M_MODEL_ID = "uzb_HumiditySensor"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_humidity_raw_cache",
        "_humidity_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._humidity_raw_cache = 0xFFFF
        self._humidity_change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_humidity_sensor(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def get_humidity_raw(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
            ATTR_REL_HUMIDITY_MEASUREMENT_VALUE,
            CLUSTER_ROLE_SERVER,
        )
        self._humidity_raw_cache = int(value)
        return self._humidity_raw_cache

    def get_humidity_percent(self):
        raw = self.get_humidity_raw()
        if raw == 0xFFFF:
            return None
        return raw / 100.0

    @property
    def humidity_percent(self):
        return self.get_humidity_percent()

    def set_humidity_raw(self, value, check=False):
        current = int(value)
        if current < 0:
            current = 0
        if current > 10000:
            current = 10000
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
            ATTR_REL_HUMIDITY_MEASUREMENT_VALUE,
            current,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._humidity_raw_cache = current
        return current

    def set_humidity_percent(self, value, check=False):
        raw = int(round(float(value) * 100.0))
        return self.set_humidity_raw(raw, check=check)

    def on_humidity_change(self, callback=None):
        self._humidity_change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_REL_HUMIDITY_MEASUREMENT:
            return
        if int(attr_id) != ATTR_REL_HUMIDITY_MEASUREMENT_VALUE:
            return
        self._humidity_raw_cache = int(value)
        if self._humidity_change_cb is not None:
            if self._humidity_raw_cache == 0xFFFF:
                self._humidity_change_cb(None)
            else:
                self._humidity_change_cb(self._humidity_raw_cache / 100.0)


class PressureSensor:
    """High-level pressure sensor wrapper (local measured-value updates)."""

    Z2M_MODEL_ID = "uzb_PressureSensor"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_pressure_raw_cache",
        "_pressure_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._pressure_raw_cache = -32768
        self._pressure_change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_pressure_sensor(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def get_pressure_raw(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_PRESSURE_MEASUREMENT,
            ATTR_PRESSURE_MEASUREMENT_VALUE,
            CLUSTER_ROLE_SERVER,
        )
        self._pressure_raw_cache = int(value)
        return self._pressure_raw_cache

    def get_pressure_hpa(self):
        raw = self.get_pressure_raw()
        if raw == -32768:
            return None
        return float(raw)

    @property
    def pressure_hpa(self):
        return self.get_pressure_hpa()

    def set_pressure_raw(self, value, check=False):
        current = int(value)
        if current < -32767:
            current = -32767
        if current > 32767:
            current = 32767
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_PRESSURE_MEASUREMENT,
            ATTR_PRESSURE_MEASUREMENT_VALUE,
            current,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._pressure_raw_cache = current
        return current

    def set_pressure_hpa(self, value, check=False):
        raw = int(round(float(value)))
        return self.set_pressure_raw(raw, check=check)

    def on_pressure_change(self, callback=None):
        self._pressure_change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_PRESSURE_MEASUREMENT:
            return
        if int(attr_id) != ATTR_PRESSURE_MEASUREMENT_VALUE:
            return
        self._pressure_raw_cache = int(value)
        if self._pressure_change_cb is not None:
            if self._pressure_raw_cache == -32768:
                self._pressure_change_cb(None)
            else:
                self._pressure_change_cb(float(self._pressure_raw_cache))


class ClimateSensor:
    """High-level climate sensor wrapper (Temperature + Humidity + Pressure)."""

    Z2M_MODEL_ID = "uzb_ClimateSensor"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_temp_raw_cache",
        "_humidity_raw_cache",
        "_pressure_raw_cache",
        "_temp_change_cb",
        "_humidity_change_cb",
        "_pressure_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._temp_raw_cache = -32768
        self._humidity_raw_cache = 0xFFFF
        self._pressure_raw_cache = -32768
        self._temp_change_cb = None
        self._humidity_change_cb = None
        self._pressure_change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_climate_sensor(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def get_temperature_raw(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_TEMP_MEASUREMENT,
            ATTR_TEMP_MEASUREMENT_VALUE,
            CLUSTER_ROLE_SERVER,
        )
        self._temp_raw_cache = int(value)
        return self._temp_raw_cache

    def get_temperature_c(self):
        raw = self.get_temperature_raw()
        if raw == -32768:
            return None
        return raw / 100.0

    @property
    def temperature_c(self):
        return self.get_temperature_c()

    def set_temperature_raw(self, value, check=False):
        current = int(value)
        if current < -32767:
            current = -32767
        if current > 32767:
            current = 32767
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_TEMP_MEASUREMENT,
            ATTR_TEMP_MEASUREMENT_VALUE,
            current,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._temp_raw_cache = current
        return current

    def set_temperature_c(self, value, check=False):
        raw = int(round(float(value) * 100.0))
        return self.set_temperature_raw(raw, check=check)

    def get_humidity_raw(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
            ATTR_REL_HUMIDITY_MEASUREMENT_VALUE,
            CLUSTER_ROLE_SERVER,
        )
        self._humidity_raw_cache = int(value)
        return self._humidity_raw_cache

    def get_humidity_percent(self):
        raw = self.get_humidity_raw()
        if raw == 0xFFFF:
            return None
        return raw / 100.0

    @property
    def humidity_percent(self):
        return self.get_humidity_percent()

    def set_humidity_raw(self, value, check=False):
        current = int(value)
        if current < 0:
            current = 0
        if current > 10000:
            current = 10000
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
            ATTR_REL_HUMIDITY_MEASUREMENT_VALUE,
            current,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._humidity_raw_cache = current
        return current

    def set_humidity_percent(self, value, check=False):
        raw = int(round(float(value) * 100.0))
        return self.set_humidity_raw(raw, check=check)

    def get_pressure_raw(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_PRESSURE_MEASUREMENT,
            ATTR_PRESSURE_MEASUREMENT_VALUE,
            CLUSTER_ROLE_SERVER,
        )
        self._pressure_raw_cache = int(value)
        return self._pressure_raw_cache

    def get_pressure_hpa(self):
        raw = self.get_pressure_raw()
        if raw == -32768:
            return None
        return float(raw)

    @property
    def pressure_hpa(self):
        return self.get_pressure_hpa()

    def set_pressure_raw(self, value, check=False):
        current = int(value)
        if current < -32767:
            current = -32767
        if current > 32767:
            current = 32767
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_PRESSURE_MEASUREMENT,
            ATTR_PRESSURE_MEASUREMENT_VALUE,
            current,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._pressure_raw_cache = current
        return current

    def set_pressure_hpa(self, value, check=False):
        raw = int(round(float(value)))
        return self.set_pressure_raw(raw, check=check)

    def on_temperature_change(self, callback=None):
        self._temp_change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def on_humidity_change(self, callback=None):
        self._humidity_change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def on_pressure_change(self, callback=None):
        self._pressure_change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return

        cluster = int(cluster_id)
        attr = int(attr_id)
        if cluster == CLUSTER_ID_TEMP_MEASUREMENT and attr == ATTR_TEMP_MEASUREMENT_VALUE:
            self._temp_raw_cache = int(value)
            if self._temp_change_cb is not None:
                if self._temp_raw_cache == -32768:
                    self._temp_change_cb(None)
                else:
                    self._temp_change_cb(self._temp_raw_cache / 100.0)
            return

        if cluster == CLUSTER_ID_REL_HUMIDITY_MEASUREMENT and attr == ATTR_REL_HUMIDITY_MEASUREMENT_VALUE:
            self._humidity_raw_cache = int(value)
            if self._humidity_change_cb is not None:
                if self._humidity_raw_cache == 0xFFFF:
                    self._humidity_change_cb(None)
                else:
                    self._humidity_change_cb(self._humidity_raw_cache / 100.0)
            return

        if cluster == CLUSTER_ID_PRESSURE_MEASUREMENT and attr == ATTR_PRESSURE_MEASUREMENT_VALUE:
            self._pressure_raw_cache = int(value)
            if self._pressure_change_cb is not None:
                if self._pressure_raw_cache == -32768:
                    self._pressure_change_cb(None)
                else:
                    self._pressure_change_cb(float(self._pressure_raw_cache))


class DoorLock:
    """High-level door lock wrapper."""

    Z2M_MODEL_ID = "uzb_DoorLock"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_lock_state_cache",
        "_lock_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._lock_state_cache = 0xFF
        self._lock_change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_door_lock(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def configure_default_reporting(self, dst_short_addr=0x0000, dst_endpoint=1):
        return reporting_presets.configure_door_lock(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def get_lock_state(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_DOOR_LOCK,
            ATTR_DOOR_LOCK_LOCK_STATE,
            CLUSTER_ROLE_SERVER,
        )
        self._lock_state_cache = int(value)
        return self._lock_state_cache

    def is_locked(self):
        return self.get_lock_state() == 1

    @property
    def locked(self):
        return self.is_locked()

    def set_lock_state(self, value, check=False):
        state = int(value)
        if state < 0:
            state = 0
        if state > 0xFF:
            state = 0xFF
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_DOOR_LOCK,
            ATTR_DOOR_LOCK_LOCK_STATE,
            state,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._lock_state_cache = state
        return state

    def lock(self, check=False):
        self.set_lock_state(1, check=check)
        return True

    def unlock(self, check=False):
        self.set_lock_state(2, check=check)
        return False

    def on_lock_change(self, callback=None):
        self._lock_change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_DOOR_LOCK:
            return
        if int(attr_id) != ATTR_DOOR_LOCK_LOCK_STATE:
            return
        self._lock_state_cache = int(value)
        if self._lock_change_cb is not None:
            self._lock_change_cb(self._lock_state_cache == 1)


class DoorLockController:
    """High-level door lock controller wrapper for lock/unlock commands."""

    Z2M_MODEL_ID = "uzb_DoorLockController"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_door_lock_controller(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def send_lock(self, dst_short_addr, dst_endpoint=1):
        return self._stack.send_lock_cmd(
            dst_short_addr=int(dst_short_addr),
            lock=True,
            dst_endpoint=int(dst_endpoint),
            src_endpoint=self.endpoint_id,
        )

    def send_unlock(self, dst_short_addr, dst_endpoint=1):
        return self._stack.send_lock_cmd(
            dst_short_addr=int(dst_short_addr),
            lock=False,
            dst_endpoint=int(dst_endpoint),
            src_endpoint=self.endpoint_id,
        )


class WindowCovering:
    """High-level window covering wrapper (lift/tilt percentage attributes)."""

    Z2M_MODEL_ID = "uzb_WindowCovering"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_lift_percentage_cache",
        "_tilt_percentage_cache",
        "_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._lift_percentage_cache = 0xFF
        self._tilt_percentage_cache = 0xFF
        self._change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_window_covering(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    @staticmethod
    def _normalize_percentage(value):
        percent = int(value)
        if percent < 0:
            percent = 0
        if percent > 100:
            percent = 100
        return percent

    @staticmethod
    def _decode_percentage(value):
        decoded = int(value) & 0xFF
        if decoded == 0xFF:
            return None
        return decoded

    def _notify(self):
        if self._change_cb is None:
            return
        self._change_cb(
            {
                "lift_percentage": self._decode_percentage(self._lift_percentage_cache),
                "tilt_percentage": self._decode_percentage(self._tilt_percentage_cache),
            }
        )

    def get_lift_percentage(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_WINDOW_COVERING,
            ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE,
            CLUSTER_ROLE_SERVER,
        )
        self._lift_percentage_cache = int(value) & 0xFF
        return self._decode_percentage(self._lift_percentage_cache)

    def set_lift_percentage(self, value, check=False):
        percent = self._normalize_percentage(value)
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_WINDOW_COVERING,
            ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE,
            percent,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._lift_percentage_cache = percent
        return percent

    def get_tilt_percentage(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_WINDOW_COVERING,
            ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE,
            CLUSTER_ROLE_SERVER,
        )
        self._tilt_percentage_cache = int(value) & 0xFF
        return self._decode_percentage(self._tilt_percentage_cache)

    def set_tilt_percentage(self, value, check=False):
        percent = self._normalize_percentage(value)
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_WINDOW_COVERING,
            ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE,
            percent,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._tilt_percentage_cache = percent
        return percent

    @property
    def position(self):
        return self.get_lift_percentage()

    @position.setter
    def position(self, value):
        self.set_lift_percentage(value)

    def on_change(self, callback=None):
        self._change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_WINDOW_COVERING:
            return

        attr = int(attr_id)
        if attr == ATTR_WINDOW_COVERING_CURRENT_POSITION_LIFT_PERCENTAGE:
            self._lift_percentage_cache = int(value) & 0xFF
            self._notify()
            return
        if attr == ATTR_WINDOW_COVERING_CURRENT_POSITION_TILT_PERCENTAGE:
            self._tilt_percentage_cache = int(value) & 0xFF
            self._notify()


class Thermostat:
    """High-level thermostat wrapper."""

    Z2M_MODEL_ID = "uzb_Thermostat"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_local_temp_cache",
        "_heat_setpoint_cache",
        "_system_mode_cache",
        "_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._local_temp_cache = -32768
        self._heat_setpoint_cache = 2000
        self._system_mode_cache = 1
        self._change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_thermostat(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def configure_default_reporting(self, dst_short_addr=0x0000, dst_endpoint=1):
        return reporting_presets.configure_thermostat(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def get_temperature_c(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_LOCAL_TEMPERATURE,
            CLUSTER_ROLE_SERVER,
        )
        self._local_temp_cache = int(value)
        if self._local_temp_cache == -32768:
            return None
        return self._local_temp_cache / 100.0

    def set_temperature_c(self, value, check=False):
        raw = int(round(float(value) * 100.0))
        if raw < -32767:
            raw = -32767
        if raw > 32767:
            raw = 32767
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_LOCAL_TEMPERATURE,
            raw,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._local_temp_cache = raw
        return raw / 100.0

    def get_heating_setpoint_c(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
            CLUSTER_ROLE_SERVER,
        )
        self._heat_setpoint_cache = int(value)
        return self._heat_setpoint_cache / 100.0

    def set_heating_setpoint_c(self, value, check=False):
        raw = int(round(float(value) * 100.0))
        if raw < -27315:
            raw = -27315
        if raw > 32767:
            raw = 32767
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
            raw,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._heat_setpoint_cache = raw
        return self._heat_setpoint_cache / 100.0

    def get_system_mode(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_SYSTEM_MODE,
            CLUSTER_ROLE_SERVER,
        )
        self._system_mode_cache = int(value)
        return self._system_mode_cache

    def set_system_mode(self, value, check=False):
        mode = int(value)
        if mode < 0:
            mode = 0
        if mode > 9:
            mode = 9
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_THERMOSTAT,
            ATTR_THERMOSTAT_SYSTEM_MODE,
            mode,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._system_mode_cache = mode
        return self._system_mode_cache

    def on_change(self, callback=None):
        self._change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _notify(self):
        if self._change_cb is None:
            return
        payload = {
            "temperature_c": None if self._local_temp_cache == -32768 else self._local_temp_cache / 100.0,
            "heating_setpoint_c": self._heat_setpoint_cache / 100.0,
            "system_mode": self._system_mode_cache,
        }
        self._change_cb(payload)

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_THERMOSTAT:
            return

        attr = int(attr_id)
        if attr == ATTR_THERMOSTAT_LOCAL_TEMPERATURE:
            self._local_temp_cache = int(value)
            self._notify()
            return
        if attr == ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT:
            self._heat_setpoint_cache = int(value)
            self._notify()
            return
        if attr == ATTR_THERMOSTAT_SYSTEM_MODE:
            self._system_mode_cache = int(value)
            self._notify()


class OccupancySensor:
    """High-level occupancy sensor wrapper."""

    Z2M_MODEL_ID = "uzb_OccupancySensor"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "_occupied_cache",
        "_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self._occupied_cache = False
        self._change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_occupancy_sensor(self.endpoint_id)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def configure_default_reporting(self, dst_short_addr=0x0000, dst_endpoint=1):
        return reporting_presets.configure_occupancy(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def get_occupied(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_OCCUPANCY_SENSING,
            ATTR_OCCUPANCY_SENSING_OCCUPANCY,
            CLUSTER_ROLE_SERVER,
        )
        self._occupied_cache = (int(value) & 0x01) != 0
        return self._occupied_cache

    @property
    def occupied(self):
        return self.get_occupied()

    def set_occupied(self, occupied, check=False):
        value = 1 if bool(occupied) else 0
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_OCCUPANCY_SENSING,
            ATTR_OCCUPANCY_SENSING_OCCUPANCY,
            value,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._occupied_cache = bool(occupied)
        return self._occupied_cache

    def on_change(self, callback=None):
        self._change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_OCCUPANCY_SENSING:
            return
        if int(attr_id) != ATTR_OCCUPANCY_SENSING_OCCUPANCY:
            return
        self._occupied_cache = (int(value) & 0x01) != 0
        if self._change_cb is not None:
            self._change_cb(self._occupied_cache)


class IASZone:
    """Generic IAS Zone wrapper (zone status + zone type)."""

    Z2M_MODEL_ID = "uzb_IASZone"

    __slots__ = (
        "_stack",
        "endpoint_id",
        "manufacturer",
        "model",
        "date_code",
        "sw_build_id",
        "power_source",
        "zone_type",
        "_zone_status_cache",
        "_change_cb",
    )

    def __init__(
        self,
        endpoint_id=1,
        stack=None,
        manufacturer="uzigbee",
        model=None,
        date_code=None,
        sw_build_id=None,
        power_source=BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
        zone_type=IAS_ZONE_TYPE_CONTACT_SWITCH,
    ):
        self._stack = stack if stack is not None else ZigbeeStack()
        self.endpoint_id = int(endpoint_id)
        self.manufacturer = manufacturer
        self.model = model or self.Z2M_MODEL_ID
        self.date_code = date_code
        self.sw_build_id = sw_build_id
        self.power_source = int(power_source)
        self.zone_type = int(zone_type)
        self._zone_status_cache = 0
        self._change_cb = None

    @property
    def stack(self):
        return self._stack

    def _create_endpoint(self):
        self._stack.create_ias_zone(self.endpoint_id, self.zone_type)

    def provision(self, register=True):
        self._create_endpoint()
        set_identity(
            stack=self._stack,
            endpoint_id=self.endpoint_id,
            manufacturer=self.manufacturer,
            model=self.model,
            date_code=self.date_code,
            sw_build_id=self.sw_build_id,
            power_source=self.power_source,
        )
        if register:
            self._stack.register_device()
        return self

    def validate_interview(self):
        return validate(stack=self._stack, endpoint_id=self.endpoint_id)

    def configure_default_reporting(self, dst_short_addr=0x0000, dst_endpoint=1):
        return reporting_presets.configure_contact_sensor(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )

    def get_zone_status(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_IAS_ZONE,
            ATTR_IAS_ZONE_STATUS,
            CLUSTER_ROLE_SERVER,
        )
        self._zone_status_cache = int(value) & 0xFFFF
        return self._zone_status_cache

    def set_zone_status(self, value, check=False):
        status = int(value)
        if status < 0:
            status = 0
        if status > 0xFFFF:
            status = 0xFFFF
        self._stack.set_attribute(
            self.endpoint_id,
            CLUSTER_ID_IAS_ZONE,
            ATTR_IAS_ZONE_STATUS,
            status,
            CLUSTER_ROLE_SERVER,
            bool(check),
        )
        self._zone_status_cache = status
        return self._zone_status_cache

    def get_zone_type(self):
        value = self._stack.get_attribute(
            self.endpoint_id,
            CLUSTER_ID_IAS_ZONE,
            ATTR_IAS_ZONE_TYPE,
            CLUSTER_ROLE_SERVER,
        )
        return int(value) & 0xFFFF

    def get_alarm(self):
        return (self.get_zone_status() & IAS_ZONE_STATUS_ALARM1) != 0

    @property
    def alarm(self):
        return self.get_alarm()

    def set_alarm(self, active, check=False):
        status = self.get_zone_status()
        if bool(active):
            status |= IAS_ZONE_STATUS_ALARM1
        else:
            status &= (~IAS_ZONE_STATUS_ALARM1) & 0xFFFF
        self.set_zone_status(status, check=check)
        return (self._zone_status_cache & IAS_ZONE_STATUS_ALARM1) != 0

    def on_change(self, callback=None):
        self._change_cb = callback
        key = (id(self._stack), self.endpoint_id)
        _LIGHT_REGISTRY[key] = self
        _ensure_light_dispatcher(self._stack)
        return self

    def _state_from_zone_status(self, zone_status):
        return (int(zone_status) & IAS_ZONE_STATUS_ALARM1) != 0

    def _handle_attr_event(self, endpoint, cluster_id, attr_id, value, status):
        if status != 0:
            return
        if int(endpoint) != self.endpoint_id:
            return
        if int(cluster_id) != CLUSTER_ID_IAS_ZONE:
            return
        if int(attr_id) != ATTR_IAS_ZONE_STATUS:
            return
        self._zone_status_cache = int(value) & 0xFFFF
        if self._change_cb is not None:
            self._change_cb(self._state_from_zone_status(self._zone_status_cache))


class ContactSensor(IASZone):
    """IAS contact sensor wrapper (True = contact closed)."""

    Z2M_MODEL_ID = "uzb_ContactSensor"

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("zone_type", IAS_ZONE_TYPE_CONTACT_SWITCH)
        super().__init__(*args, **kwargs)

    def _create_endpoint(self):
        self._stack.create_contact_sensor(self.endpoint_id)

    def _state_from_zone_status(self, zone_status):
        return (int(zone_status) & IAS_ZONE_STATUS_ALARM1) == 0

    def get_contact(self):
        return not self.get_alarm()

    @property
    def contact(self):
        return self.get_contact()

    def set_contact(self, contact, check=False):
        return not self.set_alarm(not bool(contact), check=check)

    def configure_default_reporting(self, dst_short_addr=0x0000, dst_endpoint=1):
        return reporting_presets.configure_contact_sensor(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )


class MotionSensor(IASZone):
    """IAS motion sensor wrapper (True = motion detected)."""

    Z2M_MODEL_ID = "uzb_MotionSensor"

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("zone_type", IAS_ZONE_TYPE_MOTION)
        super().__init__(*args, **kwargs)

    def _create_endpoint(self):
        self._stack.create_motion_sensor(self.endpoint_id)

    def get_motion(self):
        return self.get_alarm()

    @property
    def motion(self):
        return self.get_motion()

    def set_motion(self, motion, check=False):
        return self.set_alarm(bool(motion), check=check)

    def configure_default_reporting(self, dst_short_addr=0x0000, dst_endpoint=1):
        return reporting_presets.configure_motion_sensor(
            stack=self._stack,
            dst_short_addr=int(dst_short_addr),
            src_endpoint=self.endpoint_id,
            dst_endpoint=int(dst_endpoint),
        )


def _ensure_light_dispatcher(stack):
    sid = id(stack)
    if sid in _LIGHT_DISPATCHERS:
        return

    def _dispatch(endpoint, cluster_id, attr_id, value, _attr_type, status):
        light = _LIGHT_REGISTRY.get((sid, int(endpoint)))
        if light is None:
            return
        light._handle_attr_event(endpoint, cluster_id, attr_id, value, status)

    stack.on_attribute(_dispatch)
    _LIGHT_DISPATCHERS[sid] = _dispatch
