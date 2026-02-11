import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStack:
    def __init__(self):
        self.calls = []

    def add_custom_cluster(self, cluster_id, cluster_role):
        self.calls.append(("add_custom_cluster", int(cluster_id), int(cluster_role)))

    def add_custom_attr(self, cluster_id, attr_id, attr_type, attr_access, initial_value):
        self.calls.append(
            ("add_custom_attr", int(cluster_id), int(attr_id), int(attr_type), int(attr_access), int(initial_value))
        )

    def send_custom_cmd(
        self,
        dst_short_addr,
        cluster_id,
        custom_cmd_id,
        payload=None,
        dst_endpoint=1,
        src_endpoint=1,
        profile_id=0x0104,
        direction=0,
        disable_default_resp=False,
        manuf_specific=False,
        manuf_code=0,
        data_type=0x41,
    ):
        self.calls.append(
            (
                "send_custom_cmd",
                int(dst_short_addr),
                int(cluster_id),
                int(custom_cmd_id),
                payload,
                int(dst_endpoint),
                int(src_endpoint),
                int(profile_id),
                int(direction),
                bool(disable_default_resp),
                bool(manuf_specific),
                int(manuf_code),
                int(data_type),
            )
        )


def test_add_custom_cluster_with_attrs():
    custom = importlib.import_module("uzigbee.custom")
    stack = _FakeStack()

    out = custom.add_custom_cluster(
        stack,
        0xFC00,
        attrs=[
            (0x0000, 0x21, 7),
            (0x0001, 0x10, 0x03, 1),
        ],
    )

    assert out == 0xFC00
    assert stack.calls == [
        ("add_custom_cluster", 0xFC00, 1),
        ("add_custom_attr", 0xFC00, 0x0000, 0x21, 0x03, 7),
        ("add_custom_attr", 0xFC00, 0x0001, 0x10, 0x03, 1),
    ]


def test_add_custom_cluster_attr_tuple_validation():
    custom = importlib.import_module("uzigbee.custom")
    stack = _FakeStack()

    with pytest.raises(ValueError, match="attr item must be"):
        custom.add_custom_cluster(stack, 0xFC00, attrs=[(0x0000, 0x21)])


def test_send_custom_cmd_normalizes_payload():
    custom = importlib.import_module("uzigbee.custom")
    stack = _FakeStack()
    out = custom.send_custom_cmd(stack, 0x1234, 0xFC00, 1, payload="ab")

    assert out == (0x1234, 0xFC00, 1, b"ab")
    assert stack.calls == [
        ("send_custom_cmd", 0x1234, 0xFC00, 1, b"ab", 1, 1, 0x0104, 0, False, False, 0, 0x41)
    ]


def test_custom_cluster_id_validation():
    custom = importlib.import_module("uzigbee.custom")
    stack = _FakeStack()
    with pytest.raises(ValueError, match="custom cluster_id must be in range"):
        custom.add_custom_cluster(stack, 0xFBFF)
