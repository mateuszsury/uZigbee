import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _SceneStack:
    def __init__(self):
        self.calls = []

    def send_scene_add_cmd(self, dst_short_addr, group_id, scene_id, dst_endpoint=1, src_endpoint=1, transition_ds=0):
        self.calls.append(("send_scene_add_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id, transition_ds))
        return None

    def send_scene_remove_cmd(self, dst_short_addr, group_id, scene_id, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_scene_remove_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id))
        return None

    def send_scene_remove_all_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_scene_remove_all_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))
        return None

    def send_scene_recall_cmd(self, dst_short_addr, group_id, scene_id, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_scene_recall_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id, scene_id))
        return None


def test_scenes_helper_commands():
    scenes = importlib.import_module("uzigbee.scenes")
    stack = _SceneStack()

    g1, s1 = scenes.add_scene(stack, dst_short_addr=0x1234, group_id=0x1FFFF, scene_id=0x1FF, src_endpoint=2, dst_endpoint=3, transition_ds=0x1FFFF)
    g2, s2 = scenes.remove_scene(stack, dst_short_addr=0x1234, group_id=-1, scene_id=-1, src_endpoint=2, dst_endpoint=3)
    g3 = scenes.remove_all_scenes(stack, dst_short_addr=0x1234, group_id=-1, src_endpoint=2, dst_endpoint=3)
    g4, s4 = scenes.recall_scene(stack, dst_short_addr=0x1234, group_id=5, scene_id=6, src_endpoint=2, dst_endpoint=3)

    assert (g1, s1) == (0xFFFF, 0xFF)
    assert (g2, s2) == (0xFFFF, 0xFF)
    assert g3 == 0xFFFF
    assert (g4, s4) == (5, 6)
    assert stack.calls == [
        ("send_scene_add_cmd", 2, 0x1234, 3, 0xFFFF, 0xFF, 0xFFFF),
        ("send_scene_remove_cmd", 2, 0x1234, 3, 0xFFFF, 0xFF),
        ("send_scene_remove_all_cmd", 2, 0x1234, 3, 0xFFFF),
        ("send_scene_recall_cmd", 2, 0x1234, 3, 5, 6),
    ]


def test_switch_scene_helpers_use_endpoint_as_source():
    devices = importlib.import_module("uzigbee.devices")
    stack = _SceneStack()
    switch = devices.Switch(endpoint_id=7, stack=stack)

    assert switch.add_scene(0x2233, 0x1111, 0x22, dst_endpoint=4, transition_ds=10) == (0x1111, 0x22)
    assert switch.remove_scene(0x2233, 0x1111, 0x22, dst_endpoint=4) == (0x1111, 0x22)
    assert switch.clear_scenes(0x2233, 0x1111, dst_endpoint=4) == 0x1111
    assert switch.recall_scene(0x2233, 0x1111, 0x22, dst_endpoint=4) == (0x1111, 0x22)

    assert stack.calls == [
        ("send_scene_add_cmd", 7, 0x2233, 4, 0x1111, 0x22, 10),
        ("send_scene_remove_cmd", 7, 0x2233, 4, 0x1111, 0x22),
        ("send_scene_remove_all_cmd", 7, 0x2233, 4, 0x1111),
        ("send_scene_recall_cmd", 7, 0x2233, 4, 0x1111, 0x22),
    ]
