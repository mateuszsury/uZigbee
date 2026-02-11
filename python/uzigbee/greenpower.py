"""Green Power Proxy/Sink helpers (signal-driven with optional control hooks)."""

from .core import (
    ZigbeeStack,
    ZigbeeError,
    signal_name,
    SIGNAL_GPP_COMMISSIONING,
    SIGNAL_GPP_MODE_CHANGE,
    SIGNAL_GPP_APPROVE_COMMISSIONING,
)


_GPP_SIGNALS = (
    int(SIGNAL_GPP_COMMISSIONING),
    int(SIGNAL_GPP_MODE_CHANGE),
    int(SIGNAL_GPP_APPROVE_COMMISSIONING),
)

_PROXY_METHODS = (
    "set_green_power_proxy",
    "green_power_proxy_set",
    "gp_set_proxy_mode",
    "zgp_set_proxy_mode",
    "set_gp_proxy_mode",
)

_SINK_METHODS = (
    "set_green_power_sink",
    "green_power_sink_set",
    "gp_set_sink_mode",
    "zgp_set_sink_mode",
    "set_gp_sink_mode",
)

_COMMISSION_METHODS = (
    "set_green_power_commissioning",
    "green_power_commissioning_set",
    "gp_set_commissioning",
    "zgp_set_commissioning",
    "set_gp_commissioning",
)


def gp_signal_ids():
    return _GPP_SIGNALS


def is_gp_signal(signal_id):
    return int(signal_id) in _GPP_SIGNALS


def _has_method(stack, method_names):
    for name in method_names:
        if callable(getattr(stack, name, None)):
            return True
    return False


def capabilities(stack):
    return {
        "signals": True,
        "proxy_control": _has_method(stack, _PROXY_METHODS),
        "sink_control": _has_method(stack, _SINK_METHODS),
        "commissioning_control": _has_method(stack, _COMMISSION_METHODS),
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


class GreenPowerManager:
    __slots__ = (
        "stack",
        "proxy_enabled",
        "sink_enabled",
        "commissioning_allowed",
        "last_signal_id",
        "last_signal_name",
        "last_signal_status",
        "signal_count",
        "_event_queue_max",
        "_events",
        "_on_event_cb",
    )

    def __init__(
        self,
        stack=None,
        proxy_enabled=False,
        sink_enabled=False,
        commissioning_allowed=False,
        event_queue_max=64,
    ):
        self.stack = stack if stack is not None else ZigbeeStack()
        self.proxy_enabled = bool(proxy_enabled)
        self.sink_enabled = bool(sink_enabled)
        self.commissioning_allowed = bool(commissioning_allowed)
        self.last_signal_id = None
        self.last_signal_name = None
        self.last_signal_status = None
        self.signal_count = 0
        self._event_queue_max = int(event_queue_max)
        if self._event_queue_max < 1:
            self._event_queue_max = 1
        self._events = []
        self._on_event_cb = None

    def on_event(self, callback=None):
        self._on_event_cb = callback
        return self

    def status(self):
        return {
            "proxy_enabled": bool(self.proxy_enabled),
            "sink_enabled": bool(self.sink_enabled),
            "commissioning_allowed": bool(self.commissioning_allowed),
            "signal_count": int(self.signal_count),
            "last_signal_id": self.last_signal_id,
            "last_signal_name": self.last_signal_name,
            "last_signal_status": self.last_signal_status,
            "event_queue_depth": len(self._events),
            "capabilities": capabilities(self.stack),
        }

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

    def process_signal(self, signal_id, status, payload=None):
        signal_id = int(signal_id)
        status = int(status)
        if not is_gp_signal(signal_id):
            return False

        self.signal_count += 1
        self.last_signal_id = signal_id
        self.last_signal_name = signal_name(signal_id)
        self.last_signal_status = status

        event_payload = {
            "signal_id": signal_id,
            "signal_name": self.last_signal_name,
            "status": status,
        }
        if payload is not None:
            event_payload["payload"] = payload

        if signal_id == int(SIGNAL_GPP_APPROVE_COMMISSIONING):
            event_payload["approved"] = bool(status == 0 and self.commissioning_allowed)
        self._emit("green_power_signal", event_payload)
        return True

    def install_signal_handler(self, chain_callback=None):
        if not hasattr(self.stack, "on_signal"):
            raise ZigbeeError("stack.on_signal not available")

        def _handler(signal_id, status):
            self.process_signal(signal_id, status)
            if chain_callback is not None:
                chain_callback(signal_id, status)

        self.stack.on_signal(_handler)
        return _handler

    def set_proxy(self, enabled=True, strict=False):
        desired = bool(enabled)
        out = _call_variants(
            self.stack,
            _PROXY_METHODS,
            (
                ((), {"enabled": desired}),
                ((desired,), {}),
            ),
        )
        out["requested"] = desired
        if out.get("ok"):
            self.proxy_enabled = desired
            return out
        if strict:
            raise ZigbeeError(out.get("error") or out.get("reason") or "green power proxy control failed")
        return out

    def set_sink(self, enabled=True, strict=False):
        desired = bool(enabled)
        out = _call_variants(
            self.stack,
            _SINK_METHODS,
            (
                ((), {"enabled": desired}),
                ((desired,), {}),
            ),
        )
        out["requested"] = desired
        if out.get("ok"):
            self.sink_enabled = desired
            return out
        if strict:
            raise ZigbeeError(out.get("error") or out.get("reason") or "green power sink control failed")
        return out

    def set_commissioning(self, allowed=True, duration_s=60, strict=False):
        desired = bool(allowed)
        out = _call_variants(
            self.stack,
            _COMMISSION_METHODS,
            (
                ((), {"enabled": desired, "duration_s": int(duration_s)}),
                ((), {"enabled": desired}),
                ((desired, int(duration_s)), {}),
                ((desired,), {}),
            ),
        )
        out["requested"] = desired
        out["duration_s"] = int(duration_s)
        if out.get("ok"):
            self.commissioning_allowed = desired
            return out
        if strict:
            raise ZigbeeError(out.get("error") or out.get("reason") or "green power commissioning control failed")
        return out

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
