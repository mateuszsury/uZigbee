"""Group management helpers for Zigbee Groups cluster."""


def add_group(stack, dst_short_addr, group_id, src_endpoint=1, dst_endpoint=1):
    """Send Groups Add Group command and return normalized group id."""
    normalized_group = int(group_id) & 0xFFFF
    stack.send_group_add_cmd(
        dst_short_addr=int(dst_short_addr),
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
        group_id=normalized_group,
    )
    return normalized_group


def remove_group(stack, dst_short_addr, group_id, src_endpoint=1, dst_endpoint=1):
    """Send Groups Remove Group command and return normalized group id."""
    normalized_group = int(group_id) & 0xFFFF
    stack.send_group_remove_cmd(
        dst_short_addr=int(dst_short_addr),
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
        group_id=normalized_group,
    )
    return normalized_group


def remove_all_groups(stack, dst_short_addr, src_endpoint=1, dst_endpoint=1):
    """Send Groups Remove All Groups command."""
    stack.send_group_remove_all_cmd(
        dst_short_addr=int(dst_short_addr),
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
    )
    return True
