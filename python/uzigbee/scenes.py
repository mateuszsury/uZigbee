"""Scene management helpers for Zigbee Scenes cluster."""


def add_scene(stack, dst_short_addr, group_id, scene_id, src_endpoint=1, dst_endpoint=1, transition_ds=0):
    """Send Scenes Add Scene command and return normalized `(group_id, scene_id)`."""
    normalized_group = int(group_id) & 0xFFFF
    normalized_scene = int(scene_id) & 0xFF
    stack.send_scene_add_cmd(
        dst_short_addr=int(dst_short_addr),
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
        group_id=normalized_group,
        scene_id=normalized_scene,
        transition_ds=int(transition_ds) & 0xFFFF,
    )
    return normalized_group, normalized_scene


def remove_scene(stack, dst_short_addr, group_id, scene_id, src_endpoint=1, dst_endpoint=1):
    """Send Scenes Remove Scene command and return normalized `(group_id, scene_id)`."""
    normalized_group = int(group_id) & 0xFFFF
    normalized_scene = int(scene_id) & 0xFF
    stack.send_scene_remove_cmd(
        dst_short_addr=int(dst_short_addr),
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
        group_id=normalized_group,
        scene_id=normalized_scene,
    )
    return normalized_group, normalized_scene


def remove_all_scenes(stack, dst_short_addr, group_id, src_endpoint=1, dst_endpoint=1):
    """Send Scenes Remove All Scenes command and return normalized `group_id`."""
    normalized_group = int(group_id) & 0xFFFF
    stack.send_scene_remove_all_cmd(
        dst_short_addr=int(dst_short_addr),
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
        group_id=normalized_group,
    )
    return normalized_group


def recall_scene(stack, dst_short_addr, group_id, scene_id, src_endpoint=1, dst_endpoint=1):
    """Send Scenes Recall Scene command and return normalized `(group_id, scene_id)`."""
    normalized_group = int(group_id) & 0xFFFF
    normalized_scene = int(scene_id) & 0xFF
    stack.send_scene_recall_cmd(
        dst_short_addr=int(dst_short_addr),
        dst_endpoint=int(dst_endpoint),
        src_endpoint=int(src_endpoint),
        group_id=normalized_group,
        scene_id=normalized_scene,
    )
    return normalized_group, normalized_scene
