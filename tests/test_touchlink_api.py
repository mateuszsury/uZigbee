import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStackNoTouchlink:
    def __init__(self):
        self.signal_cb = None

    def on_signal(self, callback):
        self.signal_cb = callback
        return None


class _FakeStackWithTouchlink(_FakeStackNoTouchlink):
    def __init__(self):
        super().__init__()
        self.calls = []

    def start_touchlink_commissioning(self, channel=None):
        self.calls.append(("start_touchlink_commissioning", None if channel is None else int(channel)))
        return 0

    def stop_touchlink_commissioning(self):
        self.calls.append(("stop_touchlink_commissioning",))
        return 0

    def set_touchlink_target(self, enabled=False):
        self.calls.append(("set_touchlink_target", bool(enabled)))
        return 0

    def touchlink_factory_reset(self):
        self.calls.append(("touchlink_factory_reset",))
        return 0


def test_touchlink_signal_helpers():
    tl = importlib.import_module("uzigbee.touchlink")
    ids = tl.touchlink_signal_ids()
    assert len(ids) >= 6
    for signal_id in ids:
        assert tl.is_touchlink_signal(signal_id) is True
    assert tl.is_touchlink_signal(0xFFFF) is False


def test_touchlink_capabilities_supported_and_unsupported():
    tl = importlib.import_module("uzigbee.touchlink")
    no_tl = _FakeStackNoTouchlink()
    with_tl = _FakeStackWithTouchlink()
    assert tl.capabilities(no_tl) == {
        "signals": True,
        "initiator_control": False,
        "initiator_stop_control": False,
        "target_control": False,
        "factory_reset_control": False,
    }
    assert tl.capabilities(with_tl) == {
        "signals": True,
        "initiator_control": True,
        "initiator_stop_control": True,
        "target_control": True,
        "factory_reset_control": True,
    }


def test_touchlink_manager_signal_processing_and_events():
    tl = importlib.import_module("uzigbee.touchlink")
    manager = tl.TouchlinkManager(stack=_FakeStackNoTouchlink(), event_queue_max=2)
    assert manager.process_signal(tl.SIGNAL_TOUCHLINK_NWK_STARTED, 0) is True
    assert manager.process_signal(tl.SIGNAL_TOUCHLINK_TARGET, 0) is True
    assert manager.process_signal(tl.SIGNAL_TOUCHLINK_TARGET_FINISHED, 0) is True
    # queue bounded to 2
    events = manager.drain_events()
    assert len(events) == 2
    assert manager.status()["state"] == tl.TOUCHLINK_STATE_FINISHED
    assert manager.status()["signal_count"] == 3


def test_touchlink_install_signal_handler_chain():
    tl = importlib.import_module("uzigbee.touchlink")
    stack = _FakeStackNoTouchlink()
    seen = []
    manager = tl.TouchlinkManager(stack=stack)
    manager.install_signal_handler(chain_callback=lambda sid, status: seen.append((int(sid), int(status))))
    stack.signal_cb(tl.SIGNAL_TOUCHLINK, 1)
    assert seen == [(int(tl.SIGNAL_TOUCHLINK), 1)]
    event = manager.poll_event()
    assert event["payload"]["signal_name"] == "touchlink"


def test_touchlink_control_methods_supported():
    tl = importlib.import_module("uzigbee.touchlink")
    stack = _FakeStackWithTouchlink()
    manager = tl.TouchlinkManager(stack=stack)

    started = manager.start_initiator(channel=11)
    assert started["ok"] is True
    assert manager.status()["initiator_active"] is True

    target = manager.set_target_mode(True)
    assert target["ok"] is True
    assert manager.status()["target_mode_enabled"] is True

    stopped = manager.stop_initiator()
    assert stopped["ok"] is True

    reset = manager.factory_reset()
    assert reset["ok"] is True
    assert manager.status()["state"] == tl.TOUCHLINK_STATE_IDLE


def test_touchlink_control_methods_unsupported_and_strict():
    tl = importlib.import_module("uzigbee.touchlink")
    manager = tl.TouchlinkManager(stack=_FakeStackNoTouchlink())
    assert manager.start_initiator()["supported"] is False
    assert manager.stop_initiator()["supported"] is False
    assert manager.set_target_mode(True)["supported"] is False
    assert manager.factory_reset()["supported"] is False
    with pytest.raises(tl.ZigbeeError):
        manager.start_initiator(strict=True)
