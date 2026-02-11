"""NCP/RCP mode helpers (runtime mode manager with safe firmware fallback)."""

try:
    import ujson as _json
except ImportError:
    try:
        import json as _json
    except ImportError:
        _json = None

from .core import ZigbeeStack, ZigbeeError, signal_name


NCP_MODE_NCP = "ncp"
NCP_MODE_RCP = "rcp"
NCP_MODE_DISABLED = "disabled"

TRANSPORT_UART = "uart"
TRANSPORT_SPI = "spi"
TRANSPORT_USB = "usb"

_MODE_VALUES = (
    NCP_MODE_NCP,
    NCP_MODE_RCP,
    NCP_MODE_DISABLED,
)

_TRANSPORT_VALUES = (
    TRANSPORT_UART,
    TRANSPORT_SPI,
    TRANSPORT_USB,
)

_NCP_START_METHODS = (
    "start_ncp_mode",
    "ncp_start",
    "set_ncp_mode",
    "enable_ncp_mode",
)

_RCP_START_METHODS = (
    "start_rcp_mode",
    "rcp_start",
    "set_rcp_mode",
    "enable_rcp_mode",
    "spinel_rcp_start",
)

_STOP_METHODS = (
    "stop_ncp_rcp_mode",
    "ncp_stop",
    "rcp_stop",
    "spinel_rcp_stop",
    "disable_ncp_mode",
    "disable_rcp_mode",
)

_NCP_SEND_METHODS = (
    "ncp_send_frame",
    "ncp_write_frame",
    "spinel_write",
)

_RCP_SEND_METHODS = (
    "rcp_send_frame",
    "rcp_write_frame",
    "spinel_write",
)


def _normalize_mode(mode):
    mode = str(mode).strip().lower()
    if mode not in _MODE_VALUES:
        raise ValueError("unsupported mode '{}'".format(mode))
    return mode


def _normalize_transport(transport):
    transport = str(transport).strip().lower()
    if transport not in _TRANSPORT_VALUES:
        raise ValueError("unsupported transport '{}'".format(transport))
    return transport


def _has_method(stack, method_names):
    for name in method_names:
        if callable(getattr(stack, name, None)):
            return True
    return False


def capabilities(stack):
    return {
        "ncp_start_control": _has_method(stack, _NCP_START_METHODS),
        "rcp_start_control": _has_method(stack, _RCP_START_METHODS),
        "stop_control": _has_method(stack, _STOP_METHODS),
        "ncp_frame_tx": _has_method(stack, _NCP_SEND_METHODS),
        "rcp_frame_tx": _has_method(stack, _RCP_SEND_METHODS),
    }


def _call_variants(stack, method_names, call_variants):
    for method_name in method_names:
        method = getattr(stack, method_name, None)
        if method is None:
            continue
        for args, kwargs in call_variants:
            try:
                result = method(*args, **kwargs)
            except TypeError:
                continue
            except Exception as exc:
                return {
                    "ok": False,
                    "supported": True,
                    "method": method_name,
                    "error": str(exc),
                }
            return {
                "ok": True,
                "supported": True,
                "method": method_name,
                "result": result,
            }
    return {
        "ok": False,
        "supported": False,
        "reason": "unsupported",
    }


def encode_frame_hex(frame):
    if isinstance(frame, (bytes, bytearray)):
        return bytes(frame).hex()
    raise ValueError("frame must be bytes-like")


def decode_frame_hex(text):
    if isinstance(text, (bytes, bytearray)):
        text = bytes(text).decode("ascii")
    if not isinstance(text, str):
        raise ValueError("hex text must be str/bytes")
    value = text.strip().lower()
    if value.startswith("0x"):
        value = value[2:]
    if not value:
        return b""
    if len(value) % 2 != 0:
        raise ValueError("hex text length must be even")
    try:
        return bytes.fromhex(value)
    except Exception:
        raise ValueError("invalid hex frame")


class NcpRcpManager:
    __slots__ = (
        "stack",
        "mode",
        "transport",
        "port",
        "baudrate",
        "flow_control",
        "active",
        "last_error",
        "last_result",
        "signal_count",
        "_events",
        "_event_queue_max",
        "_on_event_cb",
    )

    def __init__(
        self,
        stack=None,
        mode=NCP_MODE_NCP,
        transport=TRANSPORT_UART,
        port=None,
        baudrate=115200,
        flow_control=False,
        event_queue_max=64,
    ):
        self.stack = stack if stack is not None else ZigbeeStack()
        self.mode = _normalize_mode(mode)
        self.transport = _normalize_transport(transport)
        self.port = None if port is None else str(port)
        self.baudrate = int(baudrate)
        if self.baudrate < 1200:
            self.baudrate = 1200
        self.flow_control = bool(flow_control)
        self.active = False
        self.last_error = None
        self.last_result = None
        self.signal_count = 0
        self._events = []
        self._event_queue_max = int(event_queue_max)
        if self._event_queue_max < 1:
            self._event_queue_max = 1
        self._on_event_cb = None

    def on_event(self, callback=None):
        self._on_event_cb = callback
        return self

    def configure(self, mode=None, transport=None, port=None, baudrate=None, flow_control=None):
        if mode is not None:
            self.mode = _normalize_mode(mode)
        if transport is not None:
            self.transport = _normalize_transport(transport)
        if port is not None:
            self.port = None if port is None else str(port)
        if baudrate is not None:
            self.baudrate = int(baudrate)
            if self.baudrate < 1200:
                self.baudrate = 1200
        if flow_control is not None:
            self.flow_control = bool(flow_control)
        return self.status()

    def status(self):
        return {
            "mode": str(self.mode),
            "transport": str(self.transport),
            "port": self.port,
            "baudrate": int(self.baudrate),
            "flow_control": bool(self.flow_control),
            "active": bool(self.active),
            "signal_count": int(self.signal_count),
            "event_queue_depth": len(self._events),
            "capabilities": capabilities(self.stack),
            "last_error": self.last_error,
            "last_result": self.last_result,
        }

    def start(self, strict=False):
        if self.mode == NCP_MODE_DISABLED:
            self.active = False
            self.last_error = None
            self.last_result = {
                "ok": True,
                "supported": True,
                "mode": NCP_MODE_DISABLED,
            }
            self._emit("ncp_mode_start", dict(self.last_result))
            return dict(self.last_result)

        methods = _NCP_START_METHODS if self.mode == NCP_MODE_NCP else _RCP_START_METHODS
        variants = (
            ((), {"transport": self.transport, "port": self.port, "baudrate": int(self.baudrate), "flow_control": bool(self.flow_control)}),
            ((), {"port": self.port, "baudrate": int(self.baudrate), "flow_control": bool(self.flow_control)}),
            ((), {"port": self.port, "baudrate": int(self.baudrate)}),
            ((), {"baudrate": int(self.baudrate)}),
            ((self.transport, self.port, int(self.baudrate), bool(self.flow_control)), {}),
            ((self.port, int(self.baudrate), bool(self.flow_control)), {}),
            ((self.port, int(self.baudrate)), {}),
            ((), {}),
        )
        out = _call_variants(self.stack, methods, variants)
        out["mode"] = str(self.mode)
        out["transport"] = str(self.transport)
        out["port"] = self.port
        out["baudrate"] = int(self.baudrate)
        out["flow_control"] = bool(self.flow_control)
        self.last_result = dict(out)
        if out.get("ok"):
            self.active = True
            self.last_error = None
            self._emit("ncp_mode_start", dict(out))
            return out
        self.active = False
        self.last_error = out.get("error") or out.get("reason")
        if strict:
            raise ZigbeeError(self.last_error or "ncp/rcp start failed")
        self._emit("ncp_mode_start_failed", dict(out))
        return out

    def stop(self, strict=False):
        out = _call_variants(self.stack, _STOP_METHODS, (((), {}),))
        out["mode"] = str(self.mode)
        self.last_result = dict(out)
        if out.get("ok"):
            self.active = False
            self.last_error = None
            self._emit("ncp_mode_stop", dict(out))
            return out
        self.last_error = out.get("error") or out.get("reason")
        if strict:
            raise ZigbeeError(self.last_error or "ncp/rcp stop failed")
        self._emit("ncp_mode_stop_failed", dict(out))
        return out

    def send_host_frame(self, frame, strict=False):
        frame = bytes(frame)
        methods = _NCP_SEND_METHODS if self.mode == NCP_MODE_NCP else _RCP_SEND_METHODS
        out = _call_variants(
            self.stack,
            methods,
            (
                ((), {"frame": frame}),
                ((frame,), {}),
            ),
        )
        out["mode"] = str(self.mode)
        out["size"] = len(frame)
        self.last_result = dict(out)
        if out.get("ok"):
            self.last_error = None
            self._emit("frame_tx", {"mode": str(self.mode), "size": len(frame), "hex": frame.hex()})
            return out
        self.last_error = out.get("error") or out.get("reason")
        if strict:
            raise ZigbeeError(self.last_error or "host frame tx failed")
        self._emit("frame_tx_failed", dict(out))
        return out

    def receive_device_frame(self, frame):
        frame = bytes(frame)
        event = {"mode": str(self.mode), "size": len(frame), "hex": frame.hex()}
        self._emit("frame_rx", event)
        return event

    def process_signal(self, signal_id, status):
        signal_id = int(signal_id)
        status = int(status)
        self.signal_count += 1
        event = {
            "signal_id": signal_id,
            "signal_name": signal_name(signal_id),
            "status": status,
        }
        self._emit("signal", event)
        return event

    def install_signal_handler(self, chain_callback=None):
        if not hasattr(self.stack, "on_signal"):
            raise ZigbeeError("stack.on_signal not available")

        def _handler(signal_id, status):
            self.process_signal(signal_id, status)
            if chain_callback is not None:
                chain_callback(signal_id, status)

        self.stack.on_signal(_handler)
        return _handler

    def poll_event(self, default=None):
        if not self._events:
            return default
        return self._events.pop(0)

    def drain_events(self, max_items=None):
        if max_items is None:
            max_items = len(self._events)
        max_items = int(max_items)
        if max_items < 0:
            max_items = 0
        out = []
        while self._events and len(out) < max_items:
            out.append(self._events.pop(0))
        return tuple(out)

    def decode_frame(self, text):
        return decode_frame_hex(text)

    def encode_frame(self, frame):
        return encode_frame_hex(frame)

    def decode_json(self, text):
        if _json is None:
            raise ZigbeeError("json module unavailable")
        if isinstance(text, (bytes, bytearray)):
            text = bytes(text).decode("utf-8")
        return _json.loads(text)

    def encode_json(self, payload):
        if _json is None:
            raise ZigbeeError("json module unavailable")
        return _json.dumps(payload)

    def _emit(self, event, payload):
        row = {
            "event": str(event),
            "payload": payload,
        }
        self._events.append(row)
        overflow = len(self._events) - int(self._event_queue_max)
        if overflow > 0:
            del self._events[:overflow]
        if self._on_event_cb is not None:
            try:
                self._on_event_cb(row["event"], row["payload"])
            except TypeError:
                self._on_event_cb(row)
            except Exception:
                pass
