"""Helpers for manufacturer-specific (custom) clusters."""

from . import core


def _normalize_custom_cluster_id(cluster_id):
    cluster_id = int(cluster_id)
    if cluster_id < core.CUSTOM_CLUSTER_ID_MIN or cluster_id > 0xFFFF:
        raise ValueError("custom cluster_id must be in range 0xFC00..0xFFFF")
    return cluster_id


def _normalize_payload(payload):
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload.encode("utf-8")
    return bytes(payload)


def add_custom_cluster(
    stack,
    cluster_id,
    attrs=(),
    cluster_role=core.CLUSTER_ROLE_SERVER,
):
    """Register custom cluster and optional attributes before device registration."""
    cluster_id = _normalize_custom_cluster_id(cluster_id)
    stack.add_custom_cluster(cluster_id, cluster_role=int(cluster_role))
    for item in attrs:
        if len(item) == 3:
            attr_id, attr_type, initial_value = item
            attr_access = core.ATTR_ACCESS_READ_WRITE
        elif len(item) == 4:
            attr_id, attr_type, attr_access, initial_value = item
        else:
            raise ValueError("attr item must be (attr_id, attr_type, initial_value) or (attr_id, attr_type, attr_access, initial_value)")
        stack.add_custom_attr(
            cluster_id=cluster_id,
            attr_id=int(attr_id),
            attr_type=int(attr_type),
            attr_access=int(attr_access),
            initial_value=int(initial_value),
        )
    return cluster_id


def send_custom_cmd(
    stack,
    dst_short_addr,
    cluster_id,
    custom_cmd_id,
    payload=None,
    dst_endpoint=1,
    src_endpoint=1,
    profile_id=0x0104,
    direction=core.CMD_DIRECTION_TO_SERVER,
    disable_default_resp=False,
    manuf_specific=False,
    manuf_code=0,
    data_type=0x41,
):
    """Send a custom cluster command."""
    cluster_id = _normalize_custom_cluster_id(cluster_id)
    payload = _normalize_payload(payload)
    stack.send_custom_cmd(
        dst_short_addr=int(dst_short_addr),
        cluster_id=cluster_id,
        custom_cmd_id=int(custom_cmd_id),
        payload=payload,
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
        profile_id=int(profile_id),
        direction=int(direction),
        disable_default_resp=bool(disable_default_resp),
        manuf_specific=bool(manuf_specific),
        manuf_code=int(manuf_code),
        data_type=int(data_type),
    )
    return (int(dst_short_addr), cluster_id, int(custom_cmd_id), payload)
