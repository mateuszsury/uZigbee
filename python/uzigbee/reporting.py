"""Attribute reporting presets and helpers."""

from .core import (
    ATTR_DOOR_LOCK_LOCK_STATE,
    ATTR_IAS_ZONE_STATUS,
    ATTR_OCCUPANCY_SENSING_OCCUPANCY,
    ATTR_THERMOSTAT_LOCAL_TEMPERATURE,
    ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT,
    ATTR_THERMOSTAT_SYSTEM_MODE,
    CLUSTER_ID_DOOR_LOCK,
    CLUSTER_ID_IAS_ZONE,
    CLUSTER_ID_OCCUPANCY_SENSING,
    CLUSTER_ID_THERMOSTAT,
    ZigbeeStack,
)
from .zcl import (
    DATA_TYPE_16BITMAP,
    DATA_TYPE_8BITMAP,
    DATA_TYPE_8BIT_ENUM,
    DATA_TYPE_S16,
)


# (cluster_id, attr_id, attr_type, min_interval, max_interval, reportable_change)
PRESET_DOOR_LOCK = (
    (CLUSTER_ID_DOOR_LOCK, ATTR_DOOR_LOCK_LOCK_STATE, DATA_TYPE_8BIT_ENUM, 0, 3600, 1),
)

PRESET_THERMOSTAT = (
    (CLUSTER_ID_THERMOSTAT, ATTR_THERMOSTAT_LOCAL_TEMPERATURE, DATA_TYPE_S16, 10, 300, 50),
    (CLUSTER_ID_THERMOSTAT, ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT, DATA_TYPE_S16, 5, 600, 50),
    (CLUSTER_ID_THERMOSTAT, ATTR_THERMOSTAT_SYSTEM_MODE, DATA_TYPE_8BIT_ENUM, 1, 3600, 1),
)

PRESET_OCCUPANCY = (
    (CLUSTER_ID_OCCUPANCY_SENSING, ATTR_OCCUPANCY_SENSING_OCCUPANCY, DATA_TYPE_8BITMAP, 1, 300, 1),
)

PRESET_CONTACT_SENSOR = (
    (CLUSTER_ID_IAS_ZONE, ATTR_IAS_ZONE_STATUS, DATA_TYPE_16BITMAP, 1, 300, 1),
)

PRESET_MOTION_SENSOR = PRESET_CONTACT_SENSOR


def apply_reporting_preset(stack, dst_short_addr, preset, src_endpoint=1, dst_endpoint=1):
    """Apply a reporting preset and return applied entries."""
    if stack is None:
        stack = ZigbeeStack()

    applied = []
    for entry in preset:
        cluster_id, attr_id, attr_type, min_interval, max_interval, reportable_change = entry
        stack.configure_reporting(
            src_endpoint=src_endpoint,
            dst_short_addr=dst_short_addr,
            dst_endpoint=dst_endpoint,
            cluster_id=cluster_id,
            attr_id=attr_id,
            attr_type=attr_type,
            min_interval=min_interval,
            max_interval=max_interval,
            reportable_change=reportable_change,
        )
        applied.append(entry)
    return tuple(applied)


def configure_door_lock(stack, dst_short_addr, src_endpoint=1, dst_endpoint=1):
    return apply_reporting_preset(
        stack=stack,
        dst_short_addr=dst_short_addr,
        preset=PRESET_DOOR_LOCK,
        src_endpoint=src_endpoint,
        dst_endpoint=dst_endpoint,
    )


def configure_thermostat(stack, dst_short_addr, src_endpoint=1, dst_endpoint=1):
    return apply_reporting_preset(
        stack=stack,
        dst_short_addr=dst_short_addr,
        preset=PRESET_THERMOSTAT,
        src_endpoint=src_endpoint,
        dst_endpoint=dst_endpoint,
    )


def configure_occupancy(stack, dst_short_addr, src_endpoint=1, dst_endpoint=1):
    return apply_reporting_preset(
        stack=stack,
        dst_short_addr=dst_short_addr,
        preset=PRESET_OCCUPANCY,
        src_endpoint=src_endpoint,
        dst_endpoint=dst_endpoint,
    )


def configure_contact_sensor(stack, dst_short_addr, src_endpoint=1, dst_endpoint=1):
    return apply_reporting_preset(
        stack=stack,
        dst_short_addr=dst_short_addr,
        preset=PRESET_CONTACT_SENSOR,
        src_endpoint=src_endpoint,
        dst_endpoint=dst_endpoint,
    )


def configure_motion_sensor(stack, dst_short_addr, src_endpoint=1, dst_endpoint=1):
    return apply_reporting_preset(
        stack=stack,
        dst_short_addr=dst_short_addr,
        preset=PRESET_MOTION_SENSOR,
        src_endpoint=src_endpoint,
        dst_endpoint=dst_endpoint,
    )
