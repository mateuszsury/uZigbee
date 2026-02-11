"""Coordinator + web portal demo using only high-level uzigbee API."""

import gc
import socket
import time

import uzigbee

try:
    import network
except ImportError:
    network = None

HTTP_PORT = 80
MAX_LOG_LINES = 50
DEFAULT_STA_SSID = "STAR1"
DEFAULT_STA_PASSWORD = "wodasodowa"


def _parse_u16(value, default=None):
    if value is None:
        if default is None:
            return None
        return int(default) & 0xFFFF
    text = str(value).strip()
    if not text:
        if default is None:
            return None
        return int(default) & 0xFFFF
    if text.startswith(("0x", "0X")):
        out = int(text, 16)
    else:
        out = int(text)
    if out < 0 or out > 0xFFFF:
        raise ValueError("u16 out of range")
    return int(out)


def _parse_index(value, default=1):
    if value is None:
        return int(default)
    text = str(value).strip()
    if not text:
        return int(default)
    out = int(text)
    if out < 1:
        raise ValueError("selector must be >= 1")
    return int(out)


def _parse_query(path):
    if "?" not in path:
        return path, {}
    route, raw = path.split("?", 1)
    out = {}
    for row in raw.split("&"):
        if not row:
            continue
        if "=" in row:
            k, v = row.split("=", 1)
        else:
            k, v = row, ""
        out[k] = v.replace("+", " ")
    return route, out


def _esc(value):
    text = str(value)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text


class App:
    def __init__(self):
        self.coordinator = uzigbee.Coordinator(
            auto_discovery=True,
            strict_discovery=False,
            auto_bind=False,
            auto_configure_reporting=False,
            include_power_desc=False,
            discover_timeout_ms=5000,
            discover_poll_ms=200,
            state_ttl_ms=120000,
            stale_read_policy="allow",
        )
        self.logs = []
        self.attr_rows = []
        self.ip = None
        self.target_short = None
        self.target_selector = 1
        self.last_probe = {}
        self.server = None
        self._smoke_state = 0
        self._smoke_due_ms = 0
        self._smoke_short = None
        self._smoke_selector = 1

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
        if name in ("device_associated", "device_update", "device_announce", "device_authorized"):
            self.log("discovery stats %s" % self.coordinator.discovery_stats())

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
        row = {
            "source_short": None if source_short is None else int(source_short) & 0xFFFF,
            "endpoint": int(endpoint),
            "cluster": int(cluster_id),
            "attr": int(attr_id),
            "value": value,
            "ts": int(time.ticks_ms()),
        }
        self.attr_rows.append(row)
        if len(self.attr_rows) > 30:
            self.attr_rows = self.attr_rows[-30:]

    def _schedule_smoke(self, short_addr, selector=1):
        self._smoke_short = int(short_addr) & 0xFFFF
        self._smoke_selector = int(selector)
        self._smoke_state = 1
        self._smoke_due_ms = time.ticks_add(time.ticks_ms(), 1500)
        self.log(
            "smoke scheduled short=0x%04x selector=%d"
            % (self._smoke_short, self._smoke_selector)
        )

    def _device_added_cb(self, device):
        self.log(
            "device added short=0x%04x features=%s endpoints=%s"
            % (
                int(device.short_addr) & 0xFFFF,
                sorted(tuple(device.features)),
                device.endpoints(),
            )
        )
        if device.has_feature("on_off"):
            self.target_short = int(device.short_addr) & 0xFFFF
            self.target_selector = 1
            self.log(
                "target auto short=0x%04x selector=%d"
                % (self.target_short, self.target_selector)
            )
            self._schedule_smoke(self.target_short, selector=self.target_selector)

    def _device_updated_cb(self, device):
        self.log(
            "device updated short=0x%04x features=%s"
            % (int(device.short_addr) & 0xFFFF, sorted(tuple(device.features)))
        )

    def wifi_sta(self):
        if network is None:
            raise RuntimeError("network module unavailable")
        sta = network.WLAN(network.STA_IF)
        if sta.active():
            sta.active(False)
            time.sleep_ms(100)
        sta.active(True)
        try:
            if hasattr(network, "PM_NONE"):
                sta.config(pm=network.PM_NONE)
        except Exception:
            pass
        sta.connect(DEFAULT_STA_SSID, DEFAULT_STA_PASSWORD)
        self.log("wifi connect ssid=%s" % DEFAULT_STA_SSID)
        start = time.ticks_ms()
        while not sta.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > 45000:
                raise RuntimeError("wifi connect timeout")
            time.sleep_ms(200)
        self.ip = sta.ifconfig()[0]
        self.log("wifi connected ip=%s" % self.ip)

    def zigbee_start(self):
        self.coordinator.on_signal(self._signal_cb)
        self.coordinator.on_attribute(self._attr_cb)
        self.coordinator.on_device_added(self._device_added_cb)
        self.coordinator.on_device_updated(self._device_updated_cb)
        self.coordinator.start(form_network=True)
        self.coordinator.permit_join(255, auto_discover=True)
        self.log("coordinator high-level started")
        self.log("permit_join started 255s")

    def _find_device(self, query=None, require_switch=False):
        query = query or {}
        selector = _parse_index(query.get("idx"), self.target_selector)
        requested_short = _parse_u16(query.get("addr"), self.target_short)
        device = None

        if requested_short is not None:
            device = self.coordinator.get_device(requested_short)
            if device is None:
                try:
                    device = self.coordinator.discover_device(requested_short, strict=False)
                except Exception:
                    device = None
            if device is not None:
                self.target_short = int(device.short_addr) & 0xFFFF
                self.target_selector = int(selector)

        if device is None and self.target_short is not None:
            device = self.coordinator.get_device(self.target_short)

        if device is None:
            device = self.coordinator.select_device(feature="on_off")
            if device is not None:
                self.target_short = int(device.short_addr) & 0xFFFF
                self.target_selector = int(selector)

        if device is None:
            raise ValueError("target device not discovered")
        if require_switch and not device.has_feature("on_off"):
            raise ValueError("target does not expose on_off feature")
        return device, selector

    def _run_smoke_step(self):
        if self._smoke_state <= 0:
            return
        now_ms = time.ticks_ms()
        if time.ticks_diff(now_ms, int(self._smoke_due_ms)) < 0:
            return

        device = self.coordinator.get_device(self._smoke_short)
        if device is None:
            self.log("smoke aborted missing device 0x%04x" % int(self._smoke_short))
            self._smoke_state = 0
            return

        try:
            endpoint = device.switch(self._smoke_selector)
            if self._smoke_state == 1:
                endpoint.on()
                self.log(
                    "smoke on short=0x%04x selector=%d"
                    % (int(device.short_addr), int(self._smoke_selector))
                )
                self._smoke_state = 2
                self._smoke_due_ms = time.ticks_add(now_ms, 700)
                return
            if self._smoke_state == 2:
                endpoint.level(96)
                self.log(
                    "smoke level=96 short=0x%04x selector=%d"
                    % (int(device.short_addr), int(self._smoke_selector))
                )
                self._smoke_state = 3
                self._smoke_due_ms = time.ticks_add(now_ms, 700)
                return
            if self._smoke_state == 3:
                endpoint.off()
                self.log(
                    "smoke off short=0x%04x selector=%d"
                    % (int(device.short_addr), int(self._smoke_selector))
                )
                self._smoke_state = 0
                return
        except Exception as exc:
            self.log("smoke failed err=%s" % exc)
            self._smoke_state = 0

    def _probe(self, query=None):
        query = query or {}
        device, selector = self._find_device(query=query, require_switch=False)
        out = {
            "short_addr": int(device.short_addr),
            "selector": int(selector),
            "features": sorted(tuple(device.features)),
            "endpoints": device.endpoints(),
        }

        try:
            if device.has_feature("on_off"):
                out["onoff"] = bool(device.switch(selector).read.on_off(use_cache=False))
        except Exception as exc:
            out["onoff_error"] = str(exc)

        try:
            if device.has_feature("temperature"):
                out["temperature_c"] = float(
                    device.temperature_sensor(1).read.temperature(use_cache=False)
                )
        except Exception as exc:
            out["temperature_error"] = str(exc)

        try:
            if device.has_feature("occupancy"):
                out["occupancy"] = int(
                    device.occupancy_sensor(1).read.occupancy(use_cache=False)
                )
        except Exception as exc:
            out["occupancy_error"] = str(exc)

        if device.has_feature("ias_zone"):
            try:
                zone_1 = device.ias_zone(1).read.ias_zone_status(use_cache=False)
                out["ias_zone_1_status"] = int(zone_1)
                out["ias_zone_1_alarm"] = bool(
                    int(zone_1) & int(uzigbee.IAS_ZONE_STATUS_ALARM1)
                )
            except Exception as exc:
                out["ias_zone_1_error"] = str(exc)
            try:
                zone_2 = device.ias_zone(2).read.ias_zone_status(use_cache=False)
                out["ias_zone_2_status"] = int(zone_2)
                out["ias_zone_2_alarm"] = bool(
                    int(zone_2) & int(uzigbee.IAS_ZONE_STATUS_ALARM1)
                )
            except Exception as exc:
                out["ias_zone_2_error"] = str(exc)

        self.last_probe = out
        return out

    def _send_cmd(self, action, query):
        device, selector = self._find_device(query=query, require_switch=True)
        endpoint = device.switch(selector)
        self.target_short = int(device.short_addr) & 0xFFFF
        self.target_selector = int(selector)

        if action == "on":
            endpoint.on()
            self.log("cmd on short=0x%04x selector=%d" % (self.target_short, selector))
            return
        if action == "off":
            endpoint.off()
            self.log("cmd off short=0x%04x selector=%d" % (self.target_short, selector))
            return
        if action == "toggle":
            endpoint.toggle()
            self.log("cmd toggle short=0x%04x selector=%d" % (self.target_short, selector))
            return
        if action == "level":
            level = int(query.get("v", "128"))
            if level < 0:
                level = 0
            if level > 254:
                level = 254
            endpoint.level(level)
            self.log(
                "cmd level=%d short=0x%04x selector=%d"
                % (level, self.target_short, selector)
            )
            return
        raise ValueError("unknown action")

    def _device_rows(self):
        out = []
        for device in self.coordinator.list_devices():
            life = device.lifecycle(offline_after_ms=self.coordinator.offline_after_ms)
            out.append(
                {
                    "short_addr": "0x%04x" % (int(device.short_addr) & 0xFFFF),
                    "ieee": device.ieee_hex,
                    "features": sorted(tuple(device.features)),
                    "endpoints": device.endpoints(),
                    "online": bool(life.get("online")),
                    "last_seen_ms": int(life.get("last_seen_ms", 0)),
                }
            )
        return out

    def _html(self):
        rows = []
        rows.append("<h2>uZigbee Coordinator High-Level Web Portal</h2>")
        rows.append(
            "<p>ip=%s target=%s selector=%d</p>"
            % (
                _esc(self.ip),
                "none"
                if self.target_short is None
                else ("0x%04x" % (int(self.target_short) & 0xFFFF)),
                int(self.target_selector),
            )
        )
        rows.append(
            '<p><a href="/permit?sec=120">permit join 120s</a> | '
            '<a href="/discover">process discovery</a> | '
            '<a href="/probe">probe</a></p>'
        )
        rows.append(
            '<p><a href="/on">on</a> | <a href="/off">off</a> | '
            '<a href="/toggle">toggle</a> | <a href="/level?v=128">level128</a></p>'
        )
        rows.append(
            '<p>manual target: /target?addr=0xA4F0&amp;idx=1 | list: <a href="/devices">devices</a></p>'
        )
        rows.append("<h3>Devices</h3><pre>%s</pre>" % _esc(self._device_rows()))
        rows.append("<h3>Last Probe</h3><pre>%s</pre>" % _esc(self.last_probe))
        rows.append("<h3>Recent Attributes</h3><pre>%s</pre>" % _esc(self.attr_rows[-12:]))
        rows.append("<h3>Logs</h3><pre>%s</pre>" % _esc("\n".join(self.logs[-24:])))
        return "\n".join(rows)

    def _response(self, code, body, ctype="text/html"):
        if isinstance(body, str):
            body = body.encode()
        hdr = (
            "HTTP/1.1 %s\r\n"
            "Content-Type: %s\r\n"
            "Content-Length: %d\r\n"
            "Connection: close\r\n\r\n"
        ) % (code, ctype, len(body))
        return hdr.encode() + body

    def _handle(self, conn):
        req = conn.recv(1024)
        if not req:
            return
        try:
            head = req.decode(errors="ignore").split("\r\n", 1)[0]
            _, path, _ = head.split(" ", 2)
        except Exception:
            conn.send(self._response("400 Bad Request", "bad request", "text/plain"))
            return

        route, query = _parse_query(path)
        try:
            if route == "/permit":
                sec = int(query.get("sec", "120"))
                self.coordinator.permit_join(sec, auto_discover=True)
                self.log("permit_join %ss" % sec)
                conn.send(self._response("200 OK", "ok permit_join %d" % sec, "text/plain"))
                return

            if route == "/discover":
                addr = _parse_u16(query.get("addr"), None)
                if addr is None:
                    out = self.coordinator.process_pending_discovery(max_items=8)
                    self.log("discover queue %s" % out)
                    conn.send(self._response("200 OK", str(out), "text/plain"))
                    return
                device = self.coordinator.discover_device(addr, strict=False)
                self.log("discover addr=0x%04x ok features=%s" % (addr, sorted(tuple(device.features))))
                conn.send(
                    self._response(
                        "200 OK",
                        "ok short=0x%04x features=%s"
                        % (int(device.short_addr), sorted(tuple(device.features))),
                        "text/plain",
                    )
                )
                return

            if route == "/target":
                addr = _parse_u16(query.get("addr"), None)
                idx = _parse_index(query.get("idx"), self.target_selector)
                if addr is None:
                    raise ValueError("missing addr")
                self.target_short = int(addr) & 0xFFFF
                self.target_selector = int(idx)
                self.log(
                    "target manual short=0x%04x selector=%d"
                    % (self.target_short, self.target_selector)
                )
                conn.send(self._response("200 OK", "ok", "text/plain"))
                return

            if route == "/devices":
                conn.send(self._response("200 OK", str(self._device_rows()), "text/plain"))
                return

            if route == "/probe":
                out = self._probe(query=query)
                self.log("probe %s" % out)
                conn.send(self._response("200 OK", str(out), "text/plain"))
                return

            if route in ("/on", "/off", "/toggle", "/level"):
                self._send_cmd(route[1:], query)
                conn.send(self._response("200 OK", "ok", "text/plain"))
                return

            body = "<html><body>%s</body></html>" % self._html()
            conn.send(self._response("200 OK", body))
        except Exception as exc:
            self.log("error route=%s err=%s" % (route, exc))
            conn.send(
                self._response(
                    "500 Internal Server Error", str(exc), "text/plain"
                )
            )

    def run(self):
        self.wifi_sta()
        self.zigbee_start()

        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", HTTP_PORT))
        s.listen(2)
        s.settimeout(0.25)
        self.server = s
        self.log("web server started http://%s:%d" % (self.ip, HTTP_PORT))

        while True:
            try:
                conn, _ = s.accept()
            except Exception:
                conn = None
            if conn is not None:
                try:
                    self._handle(conn)
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass

            self.coordinator.process_pending_discovery(max_items=2)
            self._run_smoke_step()
            gc.collect()
            time.sleep_ms(30)


app = App()
app.run()
