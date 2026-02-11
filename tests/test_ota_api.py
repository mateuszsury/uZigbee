import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStack:
    def __init__(self):
        self.calls = []
        self.control_supported = False
        self.server_supported = False
        self.client_start_supported = False

    def ota_client_control_supported(self):
        self.calls.append(("ota_client_control_supported",))
        return bool(self.control_supported)

    def ota_client_query_interval_set(self, endpoint_id=1, interval_min=5):
        self.calls.append(("ota_client_query_interval_set", int(endpoint_id), int(interval_min)))

    def ota_client_query_image_req(self, server_ep=1, server_addr=0):
        self.calls.append(("ota_client_query_image_req", int(server_ep), int(server_addr)))

    def ota_client_query_image_stop(self):
        self.calls.append(("ota_client_query_image_stop",))

    def ota_server_start(self, image_path, file_version, hw_version):
        self.calls.append(("ota_server_start", str(image_path), int(file_version), int(hw_version)))
        if not self.server_supported:
            raise TypeError("unsupported")
        return 0

    def ota_server_stop(self):
        self.calls.append(("ota_server_stop",))
        if not self.server_supported:
            raise TypeError("unsupported")
        return 0

    def ota_client_start(self, callback):
        self.calls.append(("ota_client_start", bool(callback is not None)))
        if not self.client_start_supported:
            raise TypeError("unsupported")
        return 0

    def ota_client_stop(self):
        self.calls.append(("ota_client_stop",))
        if not self.client_start_supported:
            raise TypeError("unsupported")
        return 0


def test_ota_helper_calls():
    ota = importlib.import_module("uzigbee.ota")
    stack = _FakeStack()
    assert ota.is_control_supported(stack) is False
    assert ota.set_query_interval(stack, endpoint_id=2, interval_min=10) == (2, 10)
    assert ota.query_image(stack, server_ep=3, server_addr=4) == (3, 4)
    assert ota.stop_query(stack) is True
    assert stack.calls == [
        ("ota_client_control_supported",),
        ("ota_client_query_interval_set", 2, 10),
        ("ota_client_query_image_req", 3, 4),
        ("ota_client_query_image_stop",),
    ]


def test_ota_if_supported_helpers_skip_when_unsupported():
    ota = importlib.import_module("uzigbee.ota")
    stack = _FakeStack()
    assert ota.set_query_interval_if_supported(stack, endpoint_id=2, interval_min=10) is False
    assert ota.query_image_if_supported(stack, server_ep=3, server_addr=4) is False
    assert ota.stop_query_if_supported(stack) is False
    assert stack.calls == [
        ("ota_client_control_supported",),
        ("ota_client_control_supported",),
        ("ota_client_control_supported",),
    ]


def test_ota_if_supported_helpers_execute_when_supported():
    ota = importlib.import_module("uzigbee.ota")
    stack = _FakeStack()
    stack.control_supported = True
    assert ota.set_query_interval_if_supported(stack, endpoint_id=2, interval_min=10) is True
    assert ota.query_image_if_supported(stack, server_ep=3, server_addr=4) is True
    assert ota.stop_query_if_supported(stack) is True
    assert stack.calls == [
        ("ota_client_control_supported",),
        ("ota_client_query_interval_set", 2, 10),
        ("ota_client_control_supported",),
        ("ota_client_query_image_req", 3, 4),
        ("ota_client_control_supported",),
        ("ota_client_query_image_stop",),
    ]


def test_ota_server_fallback_when_unsupported():
    ota = importlib.import_module("uzigbee.ota")
    stack = _FakeStack()
    out = ota.start_server(stack, image_path="fw.bin", file_version=1, hw_version=1)
    assert out["started"] is False
    assert out["reason"] == "unsupported"
    assert ota.stop_server(stack)["stopped"] is False
    assert ota.capabilities(stack) == {"client_control": False, "server_control": True}


def test_ota_server_start_stop_when_supported():
    ota = importlib.import_module("uzigbee.ota")
    stack = _FakeStack()
    stack.server_supported = True
    out_start = ota.start_server(stack, image_path="fw.bin", file_version=2, hw_version=3)
    out_stop = ota.stop_server(stack)
    assert out_start["started"] is True
    assert out_stop["stopped"] is True
    assert ("ota_server_start", "fw.bin", 2, 3) in stack.calls
    assert ("ota_server_stop",) in stack.calls


def test_ota_client_start_stop_manager_and_status():
    ota = importlib.import_module("uzigbee.ota")
    stack = _FakeStack()
    stack.control_supported = True
    stack.client_start_supported = True
    manager = ota.OtaManager(stack)

    started = manager.start_client(callback=lambda *_: None)
    assert started["started"] is True
    assert manager.status()["state"] == ota.OTA_STATE_CLIENT_ACTIVE

    manager.set_query_interval(endpoint_id=1, interval_min=6)
    manager.query_image(server_ep=1, server_addr=0x00)
    assert manager.stop_query() is True

    stopped = manager.stop_client()
    assert stopped["stopped"] is True
    status = manager.status()
    assert status["state"] == ota.OTA_STATE_IDLE
    assert status["client_started"] is False


def test_ota_start_client_strict_raises_when_unsupported():
    ota = importlib.import_module("uzigbee.ota")
    stack = _FakeStack()
    try:
        ota.start_client(stack, strict=True)
        raised = False
    except Exception as exc:
        raised = "not available" in str(exc).lower() or "ota method" in str(exc).lower()
    assert raised is True
