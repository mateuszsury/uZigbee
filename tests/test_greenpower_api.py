import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStackNoGp:
    def __init__(self):
        self.signal_cb = None

    def on_signal(self, callback):
        self.signal_cb = callback
        return None


class _FakeStackWithGp(_FakeStackNoGp):
    def __init__(self):
        super().__init__()
        self.calls = []

    def set_green_power_proxy(self, enabled=False):
        self.calls.append(("set_green_power_proxy", bool(enabled)))
        return 0

    def set_green_power_sink(self, enabled=False):
        self.calls.append(("set_green_power_sink", bool(enabled)))
        return 0

    def set_green_power_commissioning(self, enabled=False, duration_s=60):
        self.calls.append(("set_green_power_commissioning", bool(enabled), int(duration_s)))
        return 0


def test_greenpower_signal_helpers():
    gp = importlib.import_module("uzigbee.greenpower")
    ids = gp.gp_signal_ids()
    assert len(ids) == 3
    for signal_id in ids:
        assert gp.is_gp_signal(signal_id) is True
    assert gp.is_gp_signal(0xFFFF) is False


def test_greenpower_capabilities_supported_and_unsupported():
    gp = importlib.import_module("uzigbee.greenpower")
    no_gp = _FakeStackNoGp()
    with_gp = _FakeStackWithGp()
    assert gp.capabilities(no_gp) == {
        "signals": True,
        "proxy_control": False,
        "sink_control": False,
        "commissioning_control": False,
    }
    assert gp.capabilities(with_gp) == {
        "signals": True,
        "proxy_control": True,
        "sink_control": True,
        "commissioning_control": True,
    }


def test_greenpower_manager_signal_processing_and_events():
    gp = importlib.import_module("uzigbee.greenpower")
    manager = gp.GreenPowerManager(stack=_FakeStackNoGp(), commissioning_allowed=True, event_queue_max=2)
    assert manager.process_signal(gp.SIGNAL_GPP_COMMISSIONING, 0) is True
    assert manager.process_signal(gp.SIGNAL_GPP_MODE_CHANGE, 0) is True
    assert manager.process_signal(gp.SIGNAL_GPP_APPROVE_COMMISSIONING, 0) is True
    # queue bounded to 2
    events = manager.drain_events()
    assert len(events) == 2
    assert events[-1]["payload"]["approved"] is True
    assert manager.status()["signal_count"] == 3


def test_greenpower_install_signal_handler_chain():
    gp = importlib.import_module("uzigbee.greenpower")
    stack = _FakeStackNoGp()
    seen = []
    manager = gp.GreenPowerManager(stack=stack)
    manager.install_signal_handler(chain_callback=lambda sid, status: seen.append((int(sid), int(status))))
    stack.signal_cb(gp.SIGNAL_GPP_MODE_CHANGE, 1)
    assert seen == [(int(gp.SIGNAL_GPP_MODE_CHANGE), 1)]
    event = manager.poll_event()
    assert event["payload"]["signal_name"] == "gpp_mode_change"


def test_greenpower_set_controls_supported():
    gp = importlib.import_module("uzigbee.greenpower")
    stack = _FakeStackWithGp()
    manager = gp.GreenPowerManager(stack=stack)
    proxy = manager.set_proxy(True)
    sink = manager.set_sink(True)
    comm = manager.set_commissioning(True, duration_s=30)
    assert proxy["ok"] is True
    assert sink["ok"] is True
    assert comm["ok"] is True
    assert manager.status()["proxy_enabled"] is True
    assert manager.status()["sink_enabled"] is True
    assert manager.status()["commissioning_allowed"] is True
    assert ("set_green_power_proxy", True) in stack.calls
    assert ("set_green_power_sink", True) in stack.calls
    assert ("set_green_power_commissioning", True, 30) in stack.calls


def test_greenpower_set_controls_unsupported_and_strict():
    gp = importlib.import_module("uzigbee.greenpower")
    manager = gp.GreenPowerManager(stack=_FakeStackNoGp())
    assert manager.set_proxy(True)["supported"] is False
    assert manager.set_sink(True)["supported"] is False
    assert manager.set_commissioning(True)["supported"] is False
    with pytest.raises(gp.ZigbeeError):
        manager.set_proxy(True, strict=True)
