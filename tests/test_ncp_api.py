import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStackNoNcp:
    def __init__(self):
        self.signal_cb = None

    def on_signal(self, callback):
        self.signal_cb = callback
        return None


class _FakeStackWithNcp(_FakeStackNoNcp):
    def __init__(self):
        super().__init__()
        self.calls = []

    def start_ncp_mode(self, port=None, baudrate=115200, flow_control=False):
        self.calls.append(("start_ncp_mode", port, int(baudrate), bool(flow_control)))
        return 0

    def start_rcp_mode(self, port=None, baudrate=115200, flow_control=False):
        self.calls.append(("start_rcp_mode", port, int(baudrate), bool(flow_control)))
        return 0

    def stop_ncp_rcp_mode(self):
        self.calls.append(("stop_ncp_rcp_mode",))
        return 0

    def ncp_send_frame(self, frame):
        self.calls.append(("ncp_send_frame", bytes(frame)))
        return len(frame)

    def rcp_send_frame(self, frame):
        self.calls.append(("rcp_send_frame", bytes(frame)))
        return len(frame)


def test_ncp_capabilities_supported_and_unsupported():
    ncp = importlib.import_module("uzigbee.ncp")
    no_ncp = _FakeStackNoNcp()
    with_ncp = _FakeStackWithNcp()
    assert ncp.capabilities(no_ncp) == {
        "ncp_start_control": False,
        "rcp_start_control": False,
        "stop_control": False,
        "ncp_frame_tx": False,
        "rcp_frame_tx": False,
    }
    assert ncp.capabilities(with_ncp) == {
        "ncp_start_control": True,
        "rcp_start_control": True,
        "stop_control": True,
        "ncp_frame_tx": True,
        "rcp_frame_tx": True,
    }


def test_ncp_mode_start_stop_and_frame_tx():
    ncp = importlib.import_module("uzigbee.ncp")
    stack = _FakeStackWithNcp()
    manager = ncp.NcpRcpManager(stack=stack, mode=ncp.NCP_MODE_NCP, port="UART0", baudrate=230400, flow_control=True)

    started = manager.start(strict=True)
    assert started["ok"] is True
    assert manager.status()["active"] is True

    tx = manager.send_host_frame(b"\x01\x02\x03", strict=True)
    assert tx["ok"] is True
    assert tx["size"] == 3

    stopped = manager.stop(strict=True)
    assert stopped["ok"] is True
    assert manager.status()["active"] is False

    assert ("start_ncp_mode", "UART0", 230400, True) in stack.calls
    assert ("stop_ncp_rcp_mode",) in stack.calls
    assert ("ncp_send_frame", b"\x01\x02\x03") in stack.calls


def test_rcp_mode_start_and_frame_tx():
    ncp = importlib.import_module("uzigbee.ncp")
    stack = _FakeStackWithNcp()
    manager = ncp.NcpRcpManager(stack=stack, mode=ncp.NCP_MODE_RCP)
    started = manager.start(strict=True)
    assert started["ok"] is True
    tx = manager.send_host_frame(b"\xaa", strict=True)
    assert tx["ok"] is True
    assert ("start_rcp_mode", None, 115200, False) in stack.calls
    assert ("rcp_send_frame", b"\xaa") in stack.calls


def test_ncp_unsupported_non_strict_and_strict():
    ncp = importlib.import_module("uzigbee.ncp")
    manager = ncp.NcpRcpManager(stack=_FakeStackNoNcp(), mode=ncp.NCP_MODE_NCP)
    out = manager.start(strict=False)
    assert out["supported"] is False
    with pytest.raises(ncp.ZigbeeError):
        manager.start(strict=True)


def test_ncp_helpers_and_events():
    ncp = importlib.import_module("uzigbee.ncp")
    manager = ncp.NcpRcpManager(stack=_FakeStackNoNcp())

    assert ncp.decode_frame_hex("0102") == b"\x01\x02"
    assert ncp.encode_frame_hex(b"\x0a\x0b") == "0a0b"
    with pytest.raises(ValueError):
        ncp.decode_frame_hex("abc")

    manager.receive_device_frame(b"\x10\x20")
    evt = manager.poll_event()
    assert evt["event"] == "frame_rx"
    assert evt["payload"]["hex"] == "1020"


def test_ncp_install_signal_handler_chain():
    ncp = importlib.import_module("uzigbee.ncp")
    stack = _FakeStackNoNcp()
    seen = []
    manager = ncp.NcpRcpManager(stack=stack)
    manager.install_signal_handler(chain_callback=lambda sid, status: seen.append((int(sid), int(status))))
    stack.signal_cb(0x09, 0)
    assert seen == [(0x09, 0)]
    event = manager.poll_event()
    assert event["event"] == "signal"
