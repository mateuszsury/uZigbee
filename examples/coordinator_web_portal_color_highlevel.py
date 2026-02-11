"""Coordinator web portal (high-level API) for remote Zigbee color light control."""

import gc
import socket
import time

import uzigbee
try:
    import ujson as json
except ImportError:
    import json

try:
    import network
except ImportError:
    network = None


HTTP_PORT = 80
DEFAULT_STA_SSID = "STAR1"
DEFAULT_STA_PASSWORD = "wodasodowa"
DEFAULT_AP_SSID = "uZigbee-C6-Coord"
DEFAULT_AP_PASSWORD = "uzigbee123"
MAX_LOG_LINES = 60
AUTO_COLOR_CYCLE = True
# Advanced override only: keep None for default guided+auto commissioning.
# Example:
# FIXED_NETWORK_PROFILE = {"channel": 20, "pan_id": 0x1A62, "extended_pan_id": "00124b0001c6c6c6"}
FIXED_NETWORK_PROFILE = None
PORTAL_HTML_CANDIDATES = (
    "portal_color.html",
    "/portal_color.html",
    "www/portal_color.html",
    "/www/portal_color.html",
)


def _parse_query(path):
    if "?" not in path:
        return path, {}
    route, raw = path.split("?", 1)
    out = {}
    for row in raw.split("&"):
        if not row:
            continue
        if "=" in row:
            key, value = row.split("=", 1)
        else:
            key, value = row, ""
        out[key] = value.replace("+", " ")
    return route, out


def _esc(value):
    text = str(value)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text


def _clamp(v, lo, hi):
    v = int(v)
    if v < int(lo):
        return int(lo)
    if v > int(hi):
        return int(hi)
    return int(v)


def _float_or(value, default):
    try:
        return float(value)
    except Exception:
        return float(default)


def _int_or(value, default):
    try:
        return int(value)
    except Exception:
        return int(default)


def _srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def _rgb_to_xy(r, g, b):
    rf = _srgb_to_linear(float(r) / 255.0)
    gf = _srgb_to_linear(float(g) / 255.0)
    bf = _srgb_to_linear(float(b) / 255.0)

    x_val = rf * 0.664511 + gf * 0.154324 + bf * 0.162028
    y_val = rf * 0.283881 + gf * 0.668433 + bf * 0.047685
    z_val = rf * 0.000088 + gf * 0.072310 + bf * 0.986039
    xyz_sum = x_val + y_val + z_val
    if xyz_sum <= 0.0:
        return 0, 0

    x = x_val / xyz_sum
    y = y_val / xyz_sum
    return _clamp(round(x * 65535.0), 0, 65535), _clamp(round(y * 65535.0), 0, 65535)


def _json_safe(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode()
        except Exception:
            return repr(value)
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            out.append(_json_safe(item))
        return out
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            out[str(key)] = _json_safe(item)
        return out
    return str(value)


class App:
    def __init__(self):
        self.logs = []
        self.attr_rows = []
        self.ip = None
        self.target_short = None
        self.target_selector = 1
        self.last_probe = {}
        self.coordinator = self._new_coordinator()
        self._auto_step = 0
        self._auto_next_ms = 0
        self._auto_last_scan_ms = 0
        self._permit_open = False
        self._permit_sec = 255
        self._permit_retry_count = 0
        self._next_permit_try_ms = 0
        self.wifi_mode = "none"
        self._pending_discover_short = None
        self._pending_discover_due_ms = 0
        self._pending_discover_attempt = 0
        self._portal_html = None
        self._portal_html_checked = False

    def _new_coordinator(self):
        # Keep compatibility with older frozen uzigbee builds that may not expose all kwargs yet.
        kwargs = {
            "network_mode": "guided",
            "auto_channel_scan_wifi": True,
            "auto_channel_preferred": (15, 20, 25, 11),
            "auto_channel_blacklist": (26,),
            "auto_discovery": True,
            "strict_discovery": False,
            "include_power_desc": False,
            "fallback_without_power_desc": True,
            "opportunistic_last_joined_scan": True,
            "discover_timeout_ms": 5000,
            "discover_poll_ms": 200,
            "join_debounce_ms": 900,
            "discovery_retry_max": 12,
            "discovery_retry_base_ms": 500,
            "discovery_retry_max_backoff_ms": 8000,
        }
        fixed_profile = FIXED_NETWORK_PROFILE
        if isinstance(fixed_profile, dict):
            channel = fixed_profile.get("channel", None)
            pan_id = fixed_profile.get("pan_id", None)
            ext_pan_id = fixed_profile.get("extended_pan_id", None)
            if channel is not None and pan_id is not None and ext_pan_id:
                kwargs["network_mode"] = "fixed"
                kwargs["channel"] = int(channel)
                kwargs["pan_id"] = int(pan_id)
                kwargs["extended_pan_id"] = str(ext_pan_id)
        while True:
            try:
                return uzigbee.Coordinator(**kwargs)
            except TypeError as exc:
                msg = str(exc)
                if "unexpected keyword argument" not in msg:
                    raise
                parts = msg.split("'")
                if len(parts) < 2:
                    raise
                key = parts[1]
                if key not in kwargs:
                    raise
                kwargs.pop(key, None)
                self.log("coordinator compat: drop unsupported kwarg %s" % key)

    def log(self, msg):
        row = "[%d] %s" % (int(time.ticks_ms() // 1000), msg)
        self.logs.append(row)
        if len(self.logs) > MAX_LOG_LINES:
            self.logs = self.logs[-MAX_LOG_LINES:]
        print(row)

    def _signal_cb(self, signal_id, status):
        try:
            name = uzigbee.signal_name(signal_id)
        except Exception:
            name = "unknown"
        self.log("signal %s(0x%02x) status=%d" % (name, int(signal_id), int(status)))
        if int(status) == 0 and name in ("device_associated", "device_update", "device_announce", "device_authorized"):
            stack = getattr(self.coordinator, "stack", None)
            if stack is None or (not hasattr(stack, "get_last_joined_short_addr")):
                return
            try:
                short_addr = int(stack.get_last_joined_short_addr()) & 0xFFFF
            except Exception:
                return
            if short_addr in (0x0000, 0xFFFE, 0xFFFF):
                return
            self._pending_discover_short = short_addr
            # Give NWK/ZDO a short settling window after association to avoid transient INVALID_STATE.
            self._pending_discover_due_ms = time.ticks_add(time.ticks_ms(), 5000)
            self._pending_discover_attempt = 0
            self.log("discovery scheduled short=0x%04x" % short_addr)

    def _attr_cb(self, *event):
        if len(event) == 5:
            endpoint, cluster_id, attr_id, value, status = event
            source_short = None
        elif len(event) == 6:
            endpoint, cluster_id, attr_id, value, _atype, status = event
            source_short = None
        elif len(event) >= 7:
            source_short, endpoint, cluster_id, attr_id, value, _atype, status = event[:7]
        else:
            return
        if int(status) != 0:
            return
        self.attr_rows.append(
            {
                "src": None if source_short is None else ("0x%04x" % (int(source_short) & 0xFFFF)),
                "ep": int(endpoint),
                "cluster": "0x%04x" % (int(cluster_id) & 0xFFFF),
                "attr": "0x%04x" % (int(attr_id) & 0xFFFF),
                "value": value,
            }
        )
        if len(self.attr_rows) > 30:
            self.attr_rows = self.attr_rows[-30:]

    def _device_added_cb(self, device):
        self.log(
            "device_added short=0x%04x features=%s endpoints=%s"
            % (int(device.short_addr) & 0xFFFF, sorted(tuple(device.features)), device.endpoints())
        )
        if device.has_feature("color"):
            self.target_short = int(device.short_addr) & 0xFFFF
            self.target_selector = 1
            self.log("target auto short=0x%04x selector=1" % self.target_short)

    def _maybe_discover_pending_target(self):
        if self._pending_discover_short is None:
            return
        if self.target_short is not None:
            self._pending_discover_short = None
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, int(self._pending_discover_due_ms)) < 0:
            return

        short_addr = int(self._pending_discover_short) & 0xFFFF
        self._pending_discover_attempt += 1
        try:
            device = self.coordinator.discover_device(short_addr, strict=False)
            self.log(
                "discovery ok short=0x%04x features=%s"
                % (short_addr, sorted(tuple(device.features)))
            )
            if device.has_feature("color"):
                self.target_short = int(device.short_addr) & 0xFFFF
                self.target_selector = 1
                self.log("target discovered short=0x%04x selector=1" % self.target_short)
                self._pending_discover_short = None
                return
        except Exception as exc:
            if self._pending_discover_attempt <= 3 or (self._pending_discover_attempt % 5) == 0:
                self.log(
                    "discovery retry #%d short=0x%04x err=%s"
                    % (int(self._pending_discover_attempt), short_addr, exc)
                )
        self._pending_discover_due_ms = time.ticks_add(now, 2000)

    def wifi_sta(self, timeout_ms=45000):
        if network is None:
            raise RuntimeError("network module unavailable")
        sta = network.WLAN(network.STA_IF)
        if sta.active():
            sta.active(False)
            time.sleep_ms(100)
        sta.active(True)
        sta.connect(DEFAULT_STA_SSID, DEFAULT_STA_PASSWORD)
        self.log("wifi connect ssid=%s" % DEFAULT_STA_SSID)
        start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > int(timeout_ms):
                raise RuntimeError("wifi connect timeout")
            time.sleep_ms(200)
        self.ip = sta.ifconfig()[0]
        self.log("wifi connected ip=%s" % self.ip)
        self.wifi_mode = "sta"

    def wifi_ap(self):
        if network is None:
            raise RuntimeError("network module unavailable")
        ap = network.WLAN(network.AP_IF)
        if ap.active():
            ap.active(False)
            time.sleep_ms(100)
        ap.active(True)
        auth = getattr(network, "AUTH_WPA2_PSK", 3)
        # Keep AP available for manual UI access when STA is unavailable on bench.
        ap.config(essid=DEFAULT_AP_SSID, password=DEFAULT_AP_PASSWORD, authmode=auth)
        self.ip = ap.ifconfig()[0]
        self.log("wifi ap fallback ssid=%s ip=%s" % (DEFAULT_AP_SSID, self.ip))
        self.wifi_mode = "ap"

    def start(self):
        self.coordinator.on_signal(self._signal_cb)
        self.coordinator.on_attribute(self._attr_cb)
        self.coordinator.on_device_added(self._device_added_cb)
        self.coordinator.start(form_network=True)
        self.log("coordinator_started")
        self._permit_open = False
        self._permit_sec = 255
        self._permit_retry_count = 0
        self._next_permit_try_ms = 0

    def _ensure_permit_join(self):
        if self._permit_open:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self._next_permit_try_ms) < 0:
            return
        try:
            self.coordinator.permit_join(self._permit_sec, auto_discover=True)
            self._permit_open = True
            self.log("permit_join open %ss" % int(self._permit_sec))
            return
        except Exception as exc:
            self._permit_retry_count += 1
            if self._permit_retry_count <= 3 or (self._permit_retry_count % 8) == 0:
                self.log("permit_join retry #%d err=%s" % (int(self._permit_retry_count), exc))
        self._next_permit_try_ms = time.ticks_add(now, 700)

    def _resolve_target(self, query):
        idx = _int_or(query.get("idx", self.target_selector), self.target_selector)
        if idx < 1:
            idx = 1
        addr = query.get("addr")
        if addr:
            base = 16 if str(addr).startswith(("0x", "0X")) else 10
            self.target_short = _clamp(int(addr, base), 0, 0xFFFF)
            self.target_selector = idx

        device = None
        if self.target_short is not None:
            device = self.coordinator.get_device(self.target_short)
            if device is None:
                try:
                    device = self.coordinator.discover_device(self.target_short, strict=False)
                except Exception:
                    device = None
        if device is None:
            device = self.coordinator.wait_for_device(
                features=("on_off", "level", "color"),
                timeout_ms=0,
                poll_ms=80,
                process_batch=6,
                permit_join_s=None,
                auto_discover=True,
                default=None,
            )
        if device is None:
            device = self.coordinator.select_device(features=("on_off", "level", "color"))
            if device is not None:
                self.target_short = int(device.short_addr) & 0xFFFF
                self.target_selector = idx
        if device is None:
            raise ValueError("color light target not discovered")

        endpoint = device.feature("color", selector=idx)
        return device, endpoint, idx

    def _probe(self, query):
        device, endpoint, idx = self._resolve_target(query)
        endpoint_id = getattr(endpoint, "endpoint_id", None)
        # Probe strictly from cache. Any forced read path on this firmware/SDK mix
        # can hit Zigbee stack asserts when called immediately after join.
        on_raw = device.get_state(0x0006, 0x0000, default=None, allow_stale=True, endpoint_id=endpoint_id)
        level_raw = device.get_state(0x0008, 0x0000, default=None, allow_stale=True, endpoint_id=endpoint_id)
        x_raw = device.get_state(0x0300, 0x0003, default=None, allow_stale=True, endpoint_id=endpoint_id)
        y_raw = device.get_state(0x0300, 0x0004, default=None, allow_stale=True, endpoint_id=endpoint_id)
        ct_raw = device.get_state(0x0300, 0x0007, default=None, allow_stale=True, endpoint_id=endpoint_id)
        out = {
            "short_addr": "0x%04x" % (int(device.short_addr) & 0xFFFF),
            "selector": int(idx),
            "features": sorted(tuple(device.features)),
            "endpoints": device.endpoints(),
            "on": None if on_raw is None else bool(on_raw),
            "level": None if level_raw is None else int(level_raw),
            "xy": None if (x_raw is None or y_raw is None) else (int(x_raw), int(y_raw)),
            "ct": None if ct_raw is None else int(ct_raw),
        }
        self.last_probe = out
        return out

    def _control(self, action, query):
        device, endpoint, idx = self._resolve_target(query)
        if action == "on":
            endpoint.on()
            self.log("on short=0x%04x idx=%d" % (int(device.short_addr) & 0xFFFF, int(idx)))
            return
        if action == "off":
            endpoint.off()
            self.log("off short=0x%04x idx=%d" % (int(device.short_addr) & 0xFFFF, int(idx)))
            return
        if action == "toggle":
            endpoint.toggle()
            self.log("toggle short=0x%04x idx=%d" % (int(device.short_addr) & 0xFFFF, int(idx)))
            return
        if action == "level":
            value = _clamp(_int_or(query.get("v", 128), 128), 0, 254)
            endpoint.level(value)
            self.log("level=%d short=0x%04x idx=%d" % (value, int(device.short_addr) & 0xFFFF, int(idx)))
            return
        if action == "xy":
            x = _clamp(_int_or(query.get("x", 32000), 32000), 0, 65535)
            y = _clamp(_int_or(query.get("y", 32000), 32000), 0, 65535)
            t = _clamp(_int_or(query.get("t", 0), 0), 0, 0xFFFF)
            endpoint.color_xy(x, y, transition_ds=t)
            self.log("xy=(%d,%d) t=%d short=0x%04x idx=%d" % (x, y, t, int(device.short_addr) & 0xFFFF, int(idx)))
            return
        if action == "ct":
            value = _clamp(_int_or(query.get("v", 300), 300), 0, 0xFFFF)
            t = _clamp(_int_or(query.get("t", 0), 0), 0, 0xFFFF)
            endpoint.color_temperature(value, transition_ds=t)
            self.log("ct=%d t=%d short=0x%04x idx=%d" % (value, t, int(device.short_addr) & 0xFFFF, int(idx)))
            return
        if action == "rgb":
            r = _clamp(_int_or(query.get("r", 255), 255), 0, 255)
            g = _clamp(_int_or(query.get("g", 255), 255), 0, 255)
            b = _clamp(_int_or(query.get("b", 255), 255), 0, 255)
            bri = _float_or(query.get("bri", 1.0), 1.0)
            if bri < 0.0:
                bri = 0.0
            if bri > 1.0:
                bri = 1.0
            x, y = _rgb_to_xy(r, g, b)
            level = _clamp(round(bri * 254.0), 0, 254)
            if level == 0:
                endpoint.off()
            else:
                endpoint.on()
                endpoint.level(level)
                endpoint.color_xy(x, y)
            self.log(
                "rgb=(%d,%d,%d) bri=%.3f -> level=%d xy=(%d,%d) short=0x%04x idx=%d"
                % (r, g, b, float(bri), level, x, y, int(device.short_addr) & 0xFFFF, int(idx))
            )
            return
        raise ValueError("unsupported action")

    def _maybe_auto_cycle(self):
        if not AUTO_COLOR_CYCLE:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self._auto_last_scan_ms) >= 1200:
            self._auto_last_scan_ms = now
            if self.target_short is None:
                device = self.coordinator.wait_for_device(
                    features=("on_off", "level", "color"),
                    timeout_ms=0,
                    poll_ms=80,
                    process_batch=6,
                    permit_join_s=None,
                    auto_discover=True,
                    default=None,
                )
                if device is not None:
                    self.target_short = int(device.short_addr) & 0xFFFF
                    self.target_selector = 1
                    self._auto_step = 0
                    self._auto_next_ms = now
                    self.log("auto target short=0x%04x selector=1" % self.target_short)

        if self.target_short is None:
            return
        if time.ticks_diff(now, self._auto_next_ms) < 0:
            return

        try:
            device = self.coordinator.get_device(self.target_short)
            if device is None:
                self.target_short = None
                return
            endpoint = device.feature("color", selector=self.target_selector)
            step = int(self._auto_step)
            if step == 0:
                endpoint.on()
                self.log("auto on")
            elif step == 1:
                endpoint.level(64)
                self.log("auto level=64")
            elif step == 2:
                endpoint.color_xy(45750, 19660)
                self.log("auto xy red-ish")
            elif step == 3:
                endpoint.color_xy(10922, 45874)
                self.log("auto xy green-ish")
            elif step == 4:
                endpoint.color_xy(9830, 3932)
                self.log("auto xy blue-ish")
            else:
                endpoint.off()
                self.log("auto off")
            self._auto_step = (step + 1) % 6
            self._auto_next_ms = time.ticks_add(now, 1100)
        except Exception as exc:
            self.log("auto cycle error: %s" % exc)
            self._auto_next_ms = time.ticks_add(now, 1500)

    def _response(self, code, body, ctype="text/html"):
        if isinstance(body, str):
            body = body.encode()
        header = (
            "HTTP/1.1 %s\r\n"
            "Content-Type: %s\r\n"
            "Content-Length: %d\r\n"
            "Connection: close\r\n\r\n"
        ) % (code, ctype, len(body))
        return header.encode() + body

    def _send_response(self, conn, code, body, ctype="text/html"):
        payload = self._response(code, body, ctype)
        try:
            conn.sendall(payload)
            return
        except AttributeError:
            pass
        sent = 0
        total = len(payload)
        while sent < total:
            n = conn.send(payload[sent:])
            if n is None or int(n) <= 0:
                raise OSError("socket send failed")
            sent += int(n)

    def _load_portal_html(self):
        if self._portal_html_checked:
            return self._portal_html
        self._portal_html_checked = True
        for candidate in PORTAL_HTML_CANDIDATES:
            try:
                with open(candidate, "r") as f:
                    self._portal_html = f.read()
                self.log("portal html loaded from %s" % candidate)
                return self._portal_html
            except Exception:
                pass
        self.log("portal html missing, using embedded fallback")
        return None

    def _status_payload(self):
        return {
            "ip": self.ip,
            "wifi_mode": self.wifi_mode,
            "target_short": None if self.target_short is None else ("0x%04x" % (int(self.target_short) & 0xFFFF)),
            "target_selector": int(self.target_selector),
            "last_probe": _json_safe(self.last_probe),
            "recent_attributes": _json_safe(self.attr_rows[-16:]),
            "logs": _json_safe(self.logs[-28:]),
            "permit_open": bool(self._permit_open),
            "permit_sec": int(self._permit_sec),
            "pending_discovery_short": None
            if self._pending_discover_short is None
            else ("0x%04x" % (int(self._pending_discover_short) & 0xFFFF)),
        }

    def _html(self):
        rows = []
        rows.append("<h2>uZigbee Coordinator Color Web Portal (High-Level API)</h2>")
        rows.append("<p>ip=%s target=%s selector=%d</p>" % (
            _esc(self.ip),
            "none" if self.target_short is None else ("0x%04x" % (int(self.target_short) & 0xFFFF)),
            int(self.target_selector),
        ))
        rows.append('<p><a href="/permit?sec=120">permit join 120s</a> | <a href="/discover">discover queue</a> | <a href="/probe">probe</a></p>')
        rows.append('<p><a href="/on">on</a> | <a href="/off">off</a> | <a href="/toggle">toggle</a> | <a href="/level?v=128">level 128</a></p>')
        rows.append('<p><a href="/rgb?r=255&g=0&b=0&bri=0.1">red</a> | <a href="/rgb?r=0&g=255&b=0&bri=0.1">green</a> | <a href="/rgb?r=0&g=0&b=255&bri=0.1">blue</a> | <a href="/rgb?r=0&g=0&b=0&bri=0">black</a></p>')
        rows.append('<p>manual: /xy?x=30000&y=20000&t=0 | /ct?v=300&t=0 | /target?addr=0x1234&idx=1</p>')
        rows.append("<h3>Last Probe</h3><pre>%s</pre>" % _esc(self.last_probe))
        rows.append("<h3>Recent Attributes</h3><pre>%s</pre>" % _esc(self.attr_rows[-12:]))
        rows.append("<h3>Logs</h3><pre>%s</pre>" % _esc("\n".join(self.logs[-24:])))
        return "\n".join(rows)

    def _embedded_portal_html(self):
        return """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>uZigbee Coordinator Color Portal</title>
<style>
body{font-family:Segoe UI,sans-serif;background:#101923;color:#e6eef7;margin:12px}
.card{border:1px solid #29405a;background:#162434;border-radius:10px;padding:10px;margin:8px 0}
button,input{padding:8px;border-radius:6px;border:1px solid #355170;background:#0f1b29;color:#e6eef7}
button{cursor:pointer;background:#2d6da5}
pre{background:#0b1520;padding:8px;border-radius:6px;max-height:220px;overflow:auto}
</style></head><body>
<h2>uZigbee Coordinator Color Web Portal</h2>
<div class="card">
<button onclick="call('/permit?sec=180')">permit 180s</button>
<button onclick="call('/discover')">discover</button>
<button onclick="probe()">probe</button>
target <input id="addr" placeholder="0x1234"> idx <input id="idx" type="number" value="1" min="1" style="width:70px">
<button onclick="setTarget()">set target</button>
</div>
<div class="card">
<button onclick="api('/on')">on</button>
<button onclick="api('/off')">off</button>
<button onclick="api('/toggle')">toggle</button>
level <input id="lv" type="number" min="0" max="254" value="128" style="width:90px">
<button onclick="setLevel()">set level</button>
</div>
<div class="card">
rgb <input id="rgb" type="color" value="#ff0000">
bri <input id="bri" type="range" min="0" max="100" value="10">
<button onclick="setRGB()">set rgb</button>
<button onclick="preset(255,0,0,10)">red</button>
<button onclick="preset(0,255,0,10)">green</button>
<button onclick="preset(0,0,255,10)">blue</button>
<button onclick="preset(0,0,0,0)">black</button>
</div>
<div class="card">status<pre id="status">loading...</pre></div>
<div class="card">probe<pre id="probe">n/a</pre></div>
<script>
async function call(path){const r=await fetch(path);const t=await r.text();if(!r.ok) throw new Error(path+' '+r.status+' '+t);return t;}
function tgt(){const a=document.getElementById('addr').value.trim();const i=Math.max(1,Number(document.getElementById('idx').value||1));let q='idx='+i;if(a){q+='&addr='+encodeURIComponent(a)}return q;}
async function api(p){await call(p+'?'+tgt());await refresh();}
async function setTarget(){await call('/target?'+tgt());await refresh();await probe();}
async function setLevel(){const v=Math.max(0,Math.min(254,Number(document.getElementById('lv').value||128)));await call('/level?v='+v+'&'+tgt());await probe();}
function hex2rgb(h){h=h.replace('#','');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];}
async function setRGB(){const [r,g,b]=hex2rgb(document.getElementById('rgb').value);const bri=(Number(document.getElementById('bri').value||10)/100).toFixed(3);await call('/rgb?r='+r+'&g='+g+'&b='+b+'&bri='+bri+'&'+tgt());await probe();}
async function preset(r,g,b,bri){document.getElementById('rgb').value='#'+[r,g,b].map(x=>x.toString(16).padStart(2,'0')).join('');document.getElementById('bri').value=bri;await setRGB();}
async function probe(){try{document.getElementById('probe').textContent=await call('/probe?'+tgt());}catch(e){document.getElementById('probe').textContent=String(e);}}
async function refresh(){try{const r=await fetch('/status');document.getElementById('status').textContent=await r.text();}catch(e){document.getElementById('status').textContent=String(e);}}
setInterval(refresh,2000);refresh();
</script></body></html>"""

    def _render_root(self):
        portal_html = self._load_portal_html()
        if portal_html:
            return portal_html
        return self._embedded_portal_html()

    def _read_request_line(self, conn, max_bytes=4096):
        data = b""
        while len(data) < int(max_bytes):
            try:
                chunk = conn.recv(256)
            except Exception:
                break
            if not chunk:
                break
            data += chunk
            # Read full request headers before responding. Closing a socket with
            # unread request bytes can generate TCP RST on some browser stacks.
            if b"\r\n\r\n" in data or b"\n\n" in data:
                break
        if not data:
            return None
        line = data.split(b"\r\n", 1)[0]
        line = line.split(b"\n", 1)[0]
        try:
            return line.decode("utf-8", "ignore").strip()
        except Exception:
            return None

    def _handle(self, conn):
        try:
            conn.settimeout(1.0)
        except Exception:
            pass
        line = self._read_request_line(conn)
        if not line:
            return
        try:
            parts = line.split()
            if len(parts) < 2:
                raise ValueError("invalid request line")
            path = parts[1]
        except Exception:
            try:
                self.log("client_io bad_request line=%s" % _esc(line))
                self._send_response(conn, "400 Bad Request", "bad request", "text/plain")
            except Exception as exc:
                self.log("client_io send400 err=%s" % exc)
            return

        route, query = _parse_query(path)
        self.log("http route=%s" % route)
        try:
            if route == "/":
                self._send_response(conn, "200 OK", self._render_root(), "text/html")
                return
            if route == "/status":
                payload = json.dumps(self._status_payload())
                self._send_response(conn, "200 OK", payload, "application/json")
                return
            if route == "/permit":
                sec = _clamp(_int_or(query.get("sec", 120), 120), 1, 255)
                self.coordinator.permit_join(sec, auto_discover=True)
                self.log("permit_join %ss" % sec)
                self._send_response(conn, "200 OK", "ok", "text/plain")
                return
            if route == "/discover":
                out = self.coordinator.process_pending_discovery(max_items=8)
                self.log("discover %s" % out)
                self._send_response(conn, "200 OK", str(out), "text/plain")
                return
            if route == "/target":
                _ = self._resolve_target(query)
                self._send_response(conn, "200 OK", "ok", "text/plain")
                return
            if route == "/probe":
                out = self._probe(query)
                self.log("probe %s" % out)
                self._send_response(conn, "200 OK", str(out), "text/plain")
                return
            if route in ("/on", "/off", "/toggle", "/level", "/xy", "/ct", "/rgb"):
                self._control(route[1:], query)
                self._send_response(conn, "200 OK", "ok", "text/plain")
                return

            body = "<html><body>%s</body></html>" % self._html()
            self._send_response(conn, "200 OK", body)
        except Exception as exc:
            self.log("error route=%s err=%s" % (route, exc))
            try:
                self._send_response(conn, "500 Internal Server Error", str(exc), "text/plain")
            except Exception as send_exc:
                self.log("client_io send500 err=%s" % send_exc)

    def run(self):
        wifi_attempt = 0
        while wifi_attempt < 2:
            wifi_attempt += 1
            try:
                self.wifi_sta(timeout_ms=15000)
                break
            except Exception as exc:
                self.log("wifi retry #%d err=%s" % (int(wifi_attempt), exc))
                time.sleep_ms(1000)
        if self.ip is None:
            self.wifi_ap()
        self.start()

        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", HTTP_PORT))
        server.listen(2)
        server.settimeout(0.25)
        self.log("web server started http://%s:%d" % (self.ip, HTTP_PORT))

        while True:
            try:
                conn, _ = server.accept()
            except Exception:
                conn = None
            if conn is not None:
                try:
                    self._handle(conn)
                except Exception as exc:
                    self.log("client_io loop err=%s" % exc)
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
            self.coordinator.process_pending_discovery(max_items=2)
            self._ensure_permit_join()
            self._maybe_discover_pending_target()
            self._maybe_auto_cycle()
            gc.collect()
            time.sleep_ms(30)


App().run()
