"""Touchlink commissioning helpers (signal-driven with optional control hooks)."""

from .core import (
    ZigbeeStack,
    ZigbeeError,
    signal_name,
    SIGNAL_TOUCHLINK_NWK_STARTED,
    SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER,
    SIGNAL_TOUCHLINK,
    SIGNAL_TOUCHLINK_TARGET,
    SIGNAL_TOUCHLINK_NWK,
    SIGNAL_TOUCHLINK_TARGET_FINISHED,
)


TOUCHLINK_STATE_IDLE = "idle"
TOUCHLINK_STATE_INITIATOR = "initiator"
TOUCHLINK_STATE_TARGET = "target"
TOUCHLINK_STATE_FINISHED = "finished"


_TOUCHLINK_SIGNALS = (
    int(SIGNAL_TOUCHLINK_NWK_STARTED),
    int(SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER),
    int(SIGNAL_TOUCHLINK),
    int(SIGNAL_TOUCHLINK_TARGET),
    int(SIGNAL_TOUCHLINK_NWK),
    int(SIGNAL_TOUCHLINK_TARGET_FINISHED),
)

_INITIATOR_START_METHODS = (
    "start_touchlink_commissioning",
    "touchlink_start",
    "bdb_start_touchlink",
    "touchlink_commissioning_start",
)

_INITIATOR_STOP_METHODS = (
    "stop_touchlink_commissioning",
    "touchlink_stop",
    "bdb_cancel_touchlink",
    "touchlink_commissioning_stop",
)

_TARGET_MODE_METHODS = (
    "set_touchlink_target",
    "touchlink_target_set",
    "touchlink_target_mode",
    "touchlink_enable_target",
)

_FACTORY_RESET_METHODS = (
    "touchlink_factory_reset",
    "start_touchlink_factory_reset",
    "bdb_touchlink_factory_reset",
)


def touchlink_signal_ids():
    return _TOUCHLINK_SIGNALS


def is_touchlink_signal(signal_id):
    return int(signal_id) in _TOUCHLINK_SIGNALS


def _has_method(stack, method_names):
    for name in method_names:
        if callable(getattr(stack, name, None)):
            return True
    return False


def capabilities(stack):
    return {
        "signals": True,
        "initiator_control": _has_method(stack, _INITIATOR_START_METHODS),
        "initiator_stop_control": _has_method(stack, _INITIATOR_STOP_METHODS),
        "target_control": _has_method(stack, _TARGET_MODE_METHODS),
        "factory_reset_control": _has_method(stack, _FACTORY_RESET_METHODS),
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


class TouchlinkManager:
    __slots__ = (
        "stack",
        "state",
        "initiator_active",
        "target_mode_enabled",
        "signal_count",
        "last_signal_id",
        "last_signal_name",
        "last_signal_status",
        "_event_queue_max",
        "_events",
        "_on_event_cb",
    )

    def __init__(self, stack=None, event_queue_max=64):
        self.stack = stack if stack is not None else ZigbeeStack()
        self.state = TOUCHLINK_STATE_IDLE
        self.initiator_active = False
        self.target_mode_enabled = False
        self.signal_count = 0
        self.last_signal_id = None
        self.last_signal_name = None
        self.last_signal_status = None
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
            "state": str(self.state),
            "initiator_active": bool(self.initiator_active),
            "target_mode_enabled": bool(self.target_mode_enabled),
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
        if not is_touchlink_signal(signal_id):
            return False

        self.signal_count += 1
        self.last_signal_id = signal_id
        self.last_signal_name = signal_name(signal_id)
        self.last_signal_status = status

        if signal_id in (
            int(SIGNAL_TOUCHLINK_NWK_STARTED),
            int(SIGNAL_TOUCHLINK_NWK_JOINED_ROUTER),
            int(SIGNAL_TOUCHLINK_NWK),
            int(SIGNAL_TOUCHLINK),
        ):
            self.state = TOUCHLINK_STATE_INITIATOR
            self.initiator_active = True
        elif signal_id == int(SIGNAL_TOUCHLINK_TARGET):
            self.state = TOUCHLINK_STATE_TARGET
            self.target_mode_enabled = True
        elif signal_id == int(SIGNAL_TOUCHLINK_TARGET_FINISHED):
            self.state = TOUCHLINK_STATE_FINISHED
            self.initiator_active = False
            self.target_mode_enabled = False

        event_payload = {
            "signal_id": signal_id,
            "signal_name": self.last_signal_name,
            "status": status,
        }
        if payload is not None:
            event_payload["payload"] = payload

        self._emit("touchlink_signal", event_payload)
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

    def start_initiator(self, channel=None, strict=False):
        variants = []
        if channel is not None:
            variants.append(((), {"channel": int(channel)}))
            variants.append(((int(channel),), {}))
        variants.append(((), {}))
        out = _call_variants(self.stack, _INITIATOR_START_METHODS, tuple(variants))
        out["channel"] = None if channel is None else int(channel)
        if out.get("ok"):
            self.state = TOUCHLINK_STATE_INITIATOR
            self.initiator_active = True
            return out
        if strict:
            raise ZigbeeError(out.get("error") or out.get("reason") or "touchlink initiator start failed")
        return out

    def stop_initiator(self, strict=False):
        out = _call_variants(self.stack, _INITIATOR_STOP_METHODS, (((), {}),))
        if out.get("ok"):
            self.initiator_active = False
            if not self.target_mode_enabled:
                self.state = TOUCHLINK_STATE_IDLE
            return out
        if strict:
            raise ZigbeeError(out.get("error") or out.get("reason") or "touchlink initiator stop failed")
        return out

    def set_target_mode(self, enabled=True, strict=False):
        desired = bool(enabled)
        out = _call_variants(
            self.stack,
            _TARGET_MODE_METHODS,
            (
                ((), {"enabled": desired}),
                ((desired,), {}),
            ),
        )
        out["requested"] = desired
        if out.get("ok"):
            self.target_mode_enabled = desired
            self.state = TOUCHLINK_STATE_TARGET if desired else TOUCHLINK_STATE_IDLE
            return out
        if strict:
            raise ZigbeeError(out.get("error") or out.get("reason") or "touchlink target mode change failed")
        return out

    def factory_reset(self, strict=False):
        out = _call_variants(self.stack, _FACTORY_RESET_METHODS, (((), {}),))
        if out.get("ok"):
            self.state = TOUCHLINK_STATE_IDLE
            self.initiator_active = False
            self.target_mode_enabled = False
            return out
        if strict:
            raise ZigbeeError(out.get("error") or out.get("reason") or "touchlink factory reset failed")
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
