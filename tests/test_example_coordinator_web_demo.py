import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

MODULE_PATH = ROOT / "examples" / "coordinator_web_demo.py"
SPEC = importlib.util.spec_from_file_location("coordinator_web_demo", MODULE_PATH)
coordinator_web_demo = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(coordinator_web_demo)


def test_parse_u16_ok():
    assert coordinator_web_demo.parse_u16("0x1234") == 0x1234
    assert coordinator_web_demo.parse_u16("4660") == 0x1234
    assert coordinator_web_demo.parse_u16("", default=7) == 7


def test_parse_u16_invalid():
    with pytest.raises(ValueError):
        coordinator_web_demo.parse_u16("70000")
    with pytest.raises(ValueError):
        coordinator_web_demo.parse_u16("-1")


def test_parse_u8_ok():
    assert coordinator_web_demo.parse_u8("1") == 1
    assert coordinator_web_demo.parse_u8("240") == 240
    assert coordinator_web_demo.parse_u8("", default=5) == 5


def test_parse_u8_invalid():
    with pytest.raises(ValueError):
        coordinator_web_demo.parse_u8("0")
    with pytest.raises(ValueError):
        coordinator_web_demo.parse_u8("241")


def test_query_and_escape_helpers():
    q = coordinator_web_demo.parse_query_string("addr=0x1234&ep=1&note=hello+world")
    assert q["addr"] == "0x1234"
    assert q["ep"] == "1"
    assert q["note"] == "hello world"
    assert coordinator_web_demo.html_escape('<x&"y>') == "&lt;x&amp;&quot;y&gt;"


def test_auto_target_from_join_signal(monkeypatch):
    class _Stack:
        def get_last_joined_short_addr(self):
            return 0x3456

    monkeypatch.setattr(coordinator_web_demo.time, "ticks_ms", lambda: 1000, raising=False)
    demo = coordinator_web_demo.CoordinatorWebDemo()
    demo.stack = _Stack()
    demo.target_short_addr = 0x0000
    demo._signal_cb(coordinator_web_demo.uzigbee.SIGNAL_DEVICE_ANNCE, 0)
    assert demo.target_short_addr == 0x3456


def test_auto_target_disables_when_firmware_lacks_api(monkeypatch):
    class _NoApiStack:
        def get_last_joined_short_addr(self):
            raise Exception("get_last_joined_short_addr not available in firmware")

    monkeypatch.setattr(coordinator_web_demo.time, "ticks_ms", lambda: 1000, raising=False)
    demo = coordinator_web_demo.CoordinatorWebDemo()
    demo.stack = _NoApiStack()
    demo._signal_cb(coordinator_web_demo.uzigbee.SIGNAL_DEVICE_ANNCE, 0)
    assert demo._auto_target_supported is False


def test_start_zigbee_logs_ota_capability(monkeypatch):
    class _Stack:
        def __init__(self):
            self.calls = []

        def init(self, role):
            self.calls.append(("init", role))

        def on_signal(self, cb):
            self.calls.append(("on_signal", cb is not None))

        def start(self, form_network=False):
            self.calls.append(("start", bool(form_network)))

        def get_ieee_addr(self):
            return b"\x01\x02\x03\x04\x05\x06\x07\x08"

        def get_short_addr(self):
            return 0x0000

        def ota_client_control_supported(self):
            self.calls.append(("ota_client_control_supported",))
            return False

    class _Switch:
        def __init__(self):
            self.calls = []

        def provision(self, register=True):
            self.calls.append(("provision", bool(register)))

    monkeypatch.setattr(coordinator_web_demo.time, "ticks_ms", lambda: 1000, raising=False)
    demo = coordinator_web_demo.CoordinatorWebDemo()
    demo.stack = _Stack()
    demo.switch = _Switch()
    demo.start_zigbee()
    assert demo._ota_control_supported is False
    assert ("ota_client_control_supported",) in demo.stack.calls
    assert any("ota control supported=False" in line for line in demo.logs)
