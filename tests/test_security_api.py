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

    def set_install_code_policy(self, enabled=False):
        self.calls.append(("set_install_code_policy", bool(enabled)))

    def set_network_security_enabled(self, enabled=True):
        self.calls.append(("set_network_security_enabled", bool(enabled)))

    def set_network_key(self, key):
        self.calls.append(("set_network_key", bytes(key)))

    def switch_network_key(self, key, key_seq_num):
        self.calls.append(("switch_network_key", bytes(key), int(key_seq_num)))

    def broadcast_network_key(self, key, key_seq_num):
        self.calls.append(("broadcast_network_key", bytes(key), int(key_seq_num)))

    def broadcast_network_key_switch(self, key_seq_num):
        self.calls.append(("broadcast_network_key_switch", int(key_seq_num)))

    def add_install_code(self, ieee_addr, ic_str):
        self.calls.append(("add_install_code", bytes(ieee_addr), str(ic_str)))

    def set_local_install_code(self, ic_str):
        self.calls.append(("set_local_install_code", str(ic_str)))

    def remove_install_code(self, ieee_addr):
        self.calls.append(("remove_install_code", bytes(ieee_addr)))

    def remove_all_install_codes(self):
        self.calls.append(("remove_all_install_codes",))


def test_normalize_network_key_accepts_hex_and_bytes():
    security = importlib.import_module("uzigbee.security")
    key_hex = "00112233445566778899AABBCCDDEEFF"
    key_bytes = b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff"

    assert security.normalize_network_key(key_hex) == key_bytes
    assert security.normalize_network_key("00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd:ee:ff") == key_bytes
    assert security.normalize_network_key(key_bytes) == key_bytes


def test_normalize_network_key_rejects_invalid_length():
    security = importlib.import_module("uzigbee.security")
    with pytest.raises(ValueError, match="network key must be 16 bytes"):
        security.normalize_network_key(b"\x01\x02")


def test_configure_security_sets_selected_fields():
    security = importlib.import_module("uzigbee.security")
    stack = _FakeStack()

    result = security.configure_security(
        stack,
        install_code_policy=True,
        network_security_enabled=True,
        network_key="00112233445566778899aabbccddeeff",
    )

    assert result["install_code_policy"] is True
    assert result["network_security_enabled"] is True
    assert result["network_key"] == b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff"
    assert stack.calls == [
        ("set_install_code_policy", True),
        ("set_network_security_enabled", True),
        ("set_network_key", b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff"),
    ]


def test_network_key_rotation_helpers():
    security = importlib.import_module("uzigbee.security")
    stack = _FakeStack()
    key = "0102030405060708090a0b0c0d0e0f10"

    assert security.set_network_key(stack, key) == bytes.fromhex(key)
    assert security.switch_network_key(stack, key, 7) == (bytes.fromhex(key), 7)
    assert security.broadcast_network_key(stack, key, 8, activate=True) == (bytes.fromhex(key), 8)

    assert stack.calls == [
        ("set_network_key", bytes.fromhex(key)),
        ("switch_network_key", bytes.fromhex(key), 7),
        ("broadcast_network_key", bytes.fromhex(key), 8),
        ("broadcast_network_key_switch", 8),
    ]


def test_install_code_helpers():
    security = importlib.import_module("uzigbee.security")
    stack = _FakeStack()
    ieee = b"\x11\x22\x33\x44\x55\x66\x77\x88"
    ic_str = "83FED3407A939723A5C639B26916D5054195"

    assert security.add_install_code(stack, ieee, ic_str) == ieee
    assert security.set_local_install_code(stack, ic_str) is True
    assert security.remove_install_code(stack, ieee) == ieee
    assert security.remove_all_install_codes(stack) is True
    assert stack.calls == [
        ("add_install_code", ieee, ic_str),
        ("set_local_install_code", ic_str),
        ("remove_install_code", ieee),
        ("remove_all_install_codes",),
    ]
