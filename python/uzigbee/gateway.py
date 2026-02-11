"""Gateway-mode helper for bridging Zigbee API over external transports.

This module is transport-agnostic. It provides:
- event queue + callback hooks,
- command dispatcher for high-level coordinator/device operations,
- JSON frame helpers for line-based TCP/HTTP/WebSocket bridges.
"""

try:
    import ujson as _json
except ImportError:
    try:
        import json as _json
    except ImportError:
        _json = None

try:
    import time as _time
except ImportError:
    _time = None

from .core import ZigbeeError, signal_name
from .network import Coordinator


def _ticks_ms():
    if _time is None:
        return 0
    if hasattr(_time, "ticks_ms"):
        return int(_time.ticks_ms())
    return int(_time.time() * 1000)


def _parse_short_addr(value):
    if isinstance(value, int):
        return int(value) & 0xFFFF
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("short_addr cannot be empty")
        return int(text, 0) & 0xFFFF
    raise ValueError("short_addr must be int or string")


def _parse_bool(value, default=False):
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off"):
            return False
    return bool(value)


class Gateway:
    """High-level Zigbee gateway facade (Coordinator + command/event bridge)."""

    __slots__ = (
        "coordinator",
        "event_queue_max",
        "_event_cb",
        "_events",
        "_custom_ops",
    )

    def __init__(self, coordinator=None, event_queue_max=64):
        self.coordinator = coordinator if coordinator is not None else Coordinator(auto_discovery=True)
        self.event_queue_max = int(event_queue_max)
        if self.event_queue_max < 1:
            self.event_queue_max = 1
        self._event_cb = None
        self._events = []
        self._custom_ops = {}

    def on_event(self, callback=None):
        self._event_cb = callback
        return self

    def register_op(self, name, callback):
        if callback is None or not callable(callback):
            raise ValueError("custom op callback must be callable")
        op_name = str(name).strip().lower()
        if not op_name:
            raise ValueError("custom op name cannot be empty")
        self._custom_ops[op_name] = callback
        return int(len(self._custom_ops))

    def unregister_op(self, name):
        op_name = str(name).strip().lower()
        if op_name in self._custom_ops:
            del self._custom_ops[op_name]
            return 1
        return 0

    def ops(self):
        out = list(self._custom_ops.keys())
        out.sort()
        return tuple(out)

    def start(self, form_network=True):
        self.coordinator.on_signal(self._on_signal)
        self.coordinator.on_attribute(self._on_attribute)
        self.coordinator.on_device_added(self._on_device_added)
        self.coordinator.on_device_updated(self._on_device_updated)
        self.coordinator.start(form_network=bool(form_network))
        self._emit("gateway_started", {"form_network": bool(form_network)})
        return self

    def permit_join(self, duration_s=60, auto_discover=True):
        self.coordinator.permit_join(duration_s=int(duration_s), auto_discover=bool(auto_discover))
        return int(duration_s)

    def list_devices(self, online=None):
        out = []
        for device in self.coordinator.list_devices(online=online):
            out.append(self._device_brief(device))
        return tuple(out)

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

    def process_command(self, command):
        command = command or {}
        op = str(command.get("op", "")).strip().lower()
        if not op:
            return {"ok": False, "error": "missing op"}
        try:
            if op in self._custom_ops:
                result = self._invoke_custom_op(op, command)
            else:
                result = self._dispatch_op(op, command)
            return {"ok": True, "op": op, "result": result}
        except Exception as exc:
            return {"ok": False, "op": op, "error": str(exc)}

    def decode_frame(self, frame):
        if _json is None:
            raise ZigbeeError("json module unavailable")
        if isinstance(frame, (bytes, bytearray)):
            frame = bytes(frame).decode("utf-8")
        if not isinstance(frame, str):
            raise ValueError("frame must be str/bytes")
        return _json.loads(frame)

    def encode_frame(self, payload):
        if _json is None:
            raise ZigbeeError("json module unavailable")
        return _json.dumps(payload)

    def process_frame(self, frame):
        command = self.decode_frame(frame)
        response = self.process_command(command)
        return self.encode_frame(response)

    def _invoke_custom_op(self, op, command):
        callback = self._custom_ops[op]
        try:
            return callback(self, command)
        except TypeError:
            return callback(command)

    def _dispatch_op(self, op, command):
        if op == "ping":
            return {"status": "pong", "ts_ms": _ticks_ms()}
        if op in ("permit_join", "pair"):
            return {
                "duration_s": self.permit_join(
                    duration_s=int(command.get("duration_s", 60)),
                    auto_discover=_parse_bool(command.get("auto_discover", True), default=True),
                )
            }
        if op in ("list_devices", "devices"):
            online = command.get("online", None)
            if online is not None:
                online = _parse_bool(online, default=True)
            return {"devices": self.list_devices(online=online)}
        if op in ("get_device", "device"):
            device = self._resolve_device(command)
            return self._device_full(device)
        if op in ("discover", "discover_device"):
            short_addr = _parse_short_addr(command.get("short_addr"))
            strict = command.get("strict", None)
            if strict is not None:
                strict = _parse_bool(strict, default=False)
            device = self.coordinator.discover_device(short_addr=short_addr, strict=strict)
            return self._device_full(device)
        if op in ("process_discovery", "process_pending_discovery"):
            count = self.coordinator.process_pending_discovery(max_items=int(command.get("max_items", 4)))
            return {"processed": int(count), "pending": self.coordinator.pending_discovery()}
        if op == "pending_discovery":
            return {"pending": self.coordinator.pending_discovery()}
        if op == "stats":
            return {
                "discovery": self.coordinator.discovery_stats(),
                "automation": self.coordinator.automation_stats(),
                "pending": self.coordinator.pending_discovery(),
                "queue_depth": len(self._events),
            }
        if op in ("read", "device_read"):
            device = self._resolve_device(command)
            return self._device_read(device, command)
        if op in ("control", "device_control"):
            device = self._resolve_device(command)
            return self._device_control(device, command)
        raise ValueError("unsupported op '{}'".format(op))

    def _resolve_device(self, command):
        if "short_addr" in command and command.get("short_addr") is not None:
            short_addr = _parse_short_addr(command.get("short_addr"))
            device = self.coordinator.get_device(short_addr)
            if device is None:
                raise ValueError("device not found for short_addr 0x{:04x}".format(short_addr))
            return device
        if "ieee_addr" in command and command.get("ieee_addr") is not None:
            ieee_addr = command.get("ieee_addr")
            device = self.coordinator.get_device_by_ieee(ieee_addr)
            if device is None:
                raise ValueError("device not found for ieee_addr {}".format(ieee_addr))
            return device
        raise ValueError("command must include short_addr or ieee_addr")

    def _device_read(self, device, command):
        metric = str(command.get("metric", "")).strip().lower()
        if not metric:
            raise ValueError("missing metric for read op")
        use_cache = _parse_bool(command.get("use_cache", True), default=True)
        method_name = {
            "on_off": "on_off",
            "level": "level",
            "lock_state": "lock_state",
            "temperature": "temperature",
            "humidity": "humidity",
            "pressure": "pressure",
            "occupancy": "occupancy",
            "thermostat_temperature": "thermostat_temperature",
            "thermostat_setpoint": "thermostat_heating_setpoint",
            "thermostat_mode": "thermostat_system_mode",
            "cover_lift": "cover_lift",
            "cover_tilt": "cover_tilt",
            "ias_zone_status": "ias_zone_status",
            "ias_alarm": "ias_alarm",
            "power_w": "power_w",
            "voltage_v": "voltage_v",
            "current_a": "current_a",
        }.get(metric)
        if method_name is None or not hasattr(device.read, method_name):
            raise ValueError("unsupported read metric '{}'".format(metric))
        value = getattr(device.read, method_name)(use_cache=use_cache)
        return {
            "short_addr": int(device.short_addr),
            "metric": metric,
            "value": value,
            "use_cache": bool(use_cache),
        }

    def _device_control(self, device, command):
        action = str(command.get("action", "")).strip().lower()
        value = command.get("value", None)
        options = command.get("options") or {}
        if not isinstance(options, dict):
            raise ValueError("options must be a dict")
        control = device.control

        if action == "on":
            result = control.on()
        elif action == "off":
            result = control.off()
        elif action == "toggle":
            result = control.toggle()
        elif action == "level":
            if value is None:
                raise ValueError("control action 'level' requires value")
            result = control.level(
                level=int(value),
                transition_ds=int(options.get("transition_ds", 0)),
                with_onoff=_parse_bool(options.get("with_onoff", True), default=True),
            )
        elif action == "lock":
            result = control.lock()
        elif action == "unlock":
            result = control.unlock()
        elif action == "thermostat_mode":
            if value is None:
                raise ValueError("control action 'thermostat_mode' requires value")
            result = control.thermostat_system_mode(int(value), check=_parse_bool(options.get("check", False)))
        elif action == "thermostat_setpoint":
            if value is None:
                raise ValueError("control action 'thermostat_setpoint' requires value")
            result = control.thermostat_heating_setpoint(float(value), check=_parse_bool(options.get("check", False)))
        elif action == "cover_lift":
            if value is None:
                raise ValueError("control action 'cover_lift' requires value")
            result = control.cover_lift(int(value), check=_parse_bool(options.get("check", False)))
        elif action == "cover_tilt":
            if value is None:
                raise ValueError("control action 'cover_tilt' requires value")
            result = control.cover_tilt(int(value), check=_parse_bool(options.get("check", False)))
        elif action == "ias_alarm":
            if value is None:
                raise ValueError("control action 'ias_alarm' requires value")
            result = control.ias_alarm(_parse_bool(value, default=False), check=_parse_bool(options.get("check", False)))
        elif action == "power_w":
            if value is None:
                raise ValueError("control action 'power_w' requires value")
            result = control.power_w(int(value), check=_parse_bool(options.get("check", False)))
        elif action == "voltage_v":
            if value is None:
                raise ValueError("control action 'voltage_v' requires value")
            result = control.voltage_v(int(value), check=_parse_bool(options.get("check", False)))
        elif action == "current_a":
            if value is None:
                raise ValueError("control action 'current_a' requires value")
            result = control.current_a(float(value), check=_parse_bool(options.get("check", False)))
        else:
            raise ValueError("unsupported control action '{}'".format(action))

        return {
            "short_addr": int(device.short_addr),
            "action": action,
            "value": result,
        }

    def _device_brief(self, device):
        endpoints = list(device.endpoint_clusters.keys())
        endpoints.sort()
        features = list(device.features)
        features.sort()
        return {
            "short_addr": int(device.short_addr),
            "ieee_addr": device.ieee_hex,
            "features": tuple(features),
            "online": bool(device.is_online(offline_after_ms=self.coordinator.offline_after_ms)),
            "last_seen_ms": int(device.last_seen_ms),
            "endpoints": tuple(int(ep) for ep in endpoints),
        }

    def _device_full(self, device):
        data = device.to_dict()
        data["online"] = bool(device.is_online(offline_after_ms=self.coordinator.offline_after_ms))
        data["ieee_addr"] = device.ieee_hex
        return data

    def _emit(self, event, payload):
        item = {
            "event": str(event),
            "ts_ms": int(_ticks_ms()),
            "payload": payload,
        }
        self._events.append(item)
        overflow = len(self._events) - int(self.event_queue_max)
        if overflow > 0:
            del self._events[:overflow]
        if self._event_cb is not None:
            try:
                self._event_cb(item["event"], item["payload"])
            except TypeError:
                self._event_cb(item)
            except Exception:
                pass

    def _on_signal(self, signal_id, status):
        self._emit(
            "signal",
            {
                "signal_id": int(signal_id),
                "signal_name": signal_name(signal_id),
                "status": int(status),
            },
        )

    def _on_attribute(self, *event):
        payload = {"event_len": int(len(event))}
        if len(event) == 5:
            endpoint, cluster_id, attr_id, value, status = event
            payload.update(
                {
                    "endpoint": int(endpoint),
                    "cluster_id": int(cluster_id),
                    "attr_id": int(attr_id),
                    "value": value,
                    "status": int(status),
                }
            )
        elif len(event) >= 7:
            source_short_addr, endpoint, cluster_id, attr_id, value, attr_type, status = event[:7]
            payload.update(
                {
                    "source_short_addr": int(source_short_addr) & 0xFFFF,
                    "endpoint": int(endpoint),
                    "cluster_id": int(cluster_id),
                    "attr_id": int(attr_id),
                    "value": value,
                    "attr_type": int(attr_type),
                    "status": int(status),
                }
            )
        else:
            payload["raw"] = event
        self._emit("attribute", payload)

    def _on_device_added(self, device):
        self._emit("device_added", self._device_brief(device))

    def _on_device_updated(self, device):
        self._emit("device_updated", self._device_brief(device))
