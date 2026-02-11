"""Zigbee2MQTT interview helpers."""

from .core import (
    ZigbeeStack,
    BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF,
    BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    BASIC_POWER_SOURCE_UNKNOWN,
)

_PENDING = {}


def _identity_defaults():
    return {
        "manufacturer_name": "uzigbee",
        "model_identifier": "uzb_device",
        "date_code": None,
        "sw_build_id": None,
        "power_source": BASIC_POWER_SOURCE_MAINS_SINGLE_PHASE,
    }


def _identity_for_endpoint(endpoint_id):
    data = _identity_defaults()
    cached = _PENDING.get(int(endpoint_id))
    if cached:
        data.update(cached)
    return data


def _read_identity_if_available(stack, endpoint_id):
    try:
        attrs = stack.get_basic_identity(endpoint_id)
    except Exception:
        return {}
    if not isinstance(attrs, dict):
        return {}
    return attrs


def set_identity(stack=None, endpoint_id=1, manufacturer=None, model=None, date_code=None, sw_build_id=None, power_source=None):
    """Set Basic interview identity fields on endpoint and cache desired values."""
    if stack is None:
        stack = ZigbeeStack()

    data = _identity_for_endpoint(endpoint_id)
    live = _read_identity_if_available(stack, endpoint_id)
    for key in ("manufacturer_name", "model_identifier", "date_code", "sw_build_id", "power_source"):
        value = live.get(key)
        if value is not None:
            data[key] = value

    if manufacturer is not None:
        data["manufacturer_name"] = manufacturer
    if model is not None:
        data["model_identifier"] = model
    if date_code is not None:
        data["date_code"] = date_code
    if sw_build_id is not None:
        data["sw_build_id"] = sw_build_id
    if power_source is not None:
        data["power_source"] = power_source

    stack.set_basic_identity(
        endpoint_id=endpoint_id,
        manufacturer=data["manufacturer_name"],
        model=data["model_identifier"],
        date_code=data["date_code"],
        sw_build_id=data["sw_build_id"],
        power_source=data["power_source"],
    )
    _PENDING[int(endpoint_id)] = dict(data)
    return dict(data)


def set_model_id(model, stack=None, endpoint_id=1):
    """Set Z2M model identifier while preserving other Basic identity fields."""
    return set_identity(stack=stack, endpoint_id=endpoint_id, model=model)


def set_manufacturer(name, stack=None, endpoint_id=1):
    """Set Z2M manufacturer name while preserving other Basic identity fields."""
    return set_identity(stack=stack, endpoint_id=endpoint_id, manufacturer=name)


def get_interview_attrs(stack=None, endpoint_id=1):
    """Return Basic-cluster attributes commonly read during Z2M interview."""
    if stack is None:
        stack = ZigbeeStack()
    return stack.get_basic_identity(endpoint_id)


def validate(stack=None, endpoint_id=1):
    """Validate the minimum Basic-cluster identity required for interview mapping."""
    attrs = get_interview_attrs(stack=stack, endpoint_id=endpoint_id)
    errors = []
    warnings = []

    manufacturer = attrs.get("manufacturer_name")
    model = attrs.get("model_identifier")
    power_source = attrs.get("power_source")

    if not manufacturer:
        errors.append("missing manufacturer_name")
    if not model:
        errors.append("missing model_identifier")
    if power_source is None:
        errors.append("missing power_source")
    elif not (BASIC_POWER_SOURCE_UNKNOWN <= int(power_source) <= BASIC_POWER_SOURCE_EMERGENCY_MAINS_TRANSF):
        errors.append("power_source out of range")

    if not attrs.get("sw_build_id"):
        warnings.append("sw_build_id missing")
    if not attrs.get("date_code"):
        warnings.append("date_code missing")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "attrs": attrs,
    }
