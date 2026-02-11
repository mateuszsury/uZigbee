import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _GroupStack:
    def __init__(self):
        self.calls = []

    def send_group_add_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_group_add_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))
        return None

    def send_group_remove_cmd(self, dst_short_addr, group_id, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_group_remove_cmd", src_endpoint, dst_short_addr, dst_endpoint, group_id))
        return None

    def send_group_remove_all_cmd(self, dst_short_addr, dst_endpoint=1, src_endpoint=1):
        self.calls.append(("send_group_remove_all_cmd", src_endpoint, dst_short_addr, dst_endpoint))
        return None


def test_groups_helper_commands():
    groups = importlib.import_module("uzigbee.groups")
    stack = _GroupStack()

    gid_add = groups.add_group(stack, dst_short_addr=0x1234, group_id=0x20001, src_endpoint=2, dst_endpoint=3)
    gid_remove = groups.remove_group(stack, dst_short_addr=0x1234, group_id=-1, src_endpoint=2, dst_endpoint=3)
    ok = groups.remove_all_groups(stack, dst_short_addr=0x1234, src_endpoint=2, dst_endpoint=3)

    assert gid_add == 0x0001
    assert gid_remove == 0xFFFF
    assert ok is True
    assert stack.calls == [
        ("send_group_add_cmd", 2, 0x1234, 3, 0x0001),
        ("send_group_remove_cmd", 2, 0x1234, 3, 0xFFFF),
        ("send_group_remove_all_cmd", 2, 0x1234, 3),
    ]


def test_switch_group_helpers_use_endpoint_as_source():
    devices = importlib.import_module("uzigbee.devices")
    stack = _GroupStack()
    switch = devices.Switch(endpoint_id=7, stack=stack)

    assert switch.add_to_group(0x2233, 0x1111, dst_endpoint=4) == 0x1111
    assert switch.remove_from_group(0x2233, 0x1111, dst_endpoint=4) == 0x1111
    assert switch.clear_groups(0x2233, dst_endpoint=4) is True

    assert stack.calls == [
        ("send_group_add_cmd", 7, 0x2233, 4, 0x1111),
        ("send_group_remove_cmd", 7, 0x2233, 4, 0x1111),
        ("send_group_remove_all_cmd", 7, 0x2233, 4),
    ]
