"""Dual-device test coordinator with web portal.

Runs Zigbee coordinator + simple HTTP UI for join/control/probe.
"""

try:
    import ubinascii as binascii
except ImportError:
    import binascii

import gc
import socket
import time

import uzigbee

try:
    import network
except ImportError:
    network = None

HTTP_PORT = 80
MAX_LOG_LINES = 40
DEFAULT_STA_SSID = "STAR1"
DEFAULT_STA_PASSWORD = "wodasodowa"


def _parse_u16(value, default=0):
    if value is None:
        return int(default) & 0xFFFF
    text = str(value).strip()
    if not text:
        return int(default) & 0xFFFF
    if text.startswith(("0x", "0X")):
        out = int(text, 16)
    else:
        out = int(text)
    if out < 0 or out > 0xFFFF:
        raise ValueError("u16 out of range")
    return out


def _parse_u8(value, default=1):
    if value is None:
        return int(default)
    text = str(value).strip()
    if not text:
        return int(default)
    out = int(text)
    if out < 1 or out > 240:
        raise ValueError("endpoint out of range")
    return out


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
        self.stack = uzigbee.ZigbeeStack()
        self.local_switch = uzigbee.DimmableSwitch(
            endpoint_id=1,
            stack=self.stack,
            manufacturer="uzigbee",
            model="uzb_coord_webportal",
            sw_build_id="dualtest",
        )
        self.logs = []
        self.attr_rows = []
        self.ip = None
        self.target_short = 0x0000
        self.target_ep = 1
        self.last_probe = {}
        self.server = None
        self._smoke_done = False

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
        if int(status) == 0 and name in ("device_announce", "device_update", "device_authorized"):
            try:
                short_addr = self.stack.get_last_joined_short_addr()
            except Exception:
                short_addr = None
            if short_addr is not None:
                short_addr = int(short_addr) & 0xFFFF
                if short_addr not in (0x0000, 0xFFFF) and short_addr != self.target_short:
                    self.target_short = short_addr
                    self.log("auto target short=0x%04x ep=%d" % (self.target_short, self.target_ep))
                self._run_smoke_control_once()

    def _run_smoke_control_once(self):
        if self._smoke_done:
            return
        if self.target_short in (0x0000, 0xFFFF):
            return
        self._smoke_done = True
        try:
            self.local_switch.send_on(self.target_short, self.target_ep)
            self.log("smoke send_on short=0x%04x ep=%d" % (self.target_short, self.target_ep))
            self.local_switch.send_level(self.target_short, 96, self.target_ep)
            self.log("smoke send_level=96 short=0x%04x ep=%d" % (self.target_short, self.target_ep))
            self.local_switch.send_off(self.target_short, self.target_ep)
            self.log("smoke send_off short=0x%04x ep=%d" % (self.target_short, self.target_ep))
        except Exception as exc:
            self.log("smoke control failed err=%s" % exc)

    def _attr_cb(self, *event):
        # Support legacy and source-aware payloads.
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
        if len(self.attr_rows) > 24:
            self.attr_rows = self.attr_rows[-24:]

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
        self.stack.init(uzigbee.ROLE_COORDINATOR)
        self.stack.on_signal(self._signal_cb)
        self.stack.on_attribute(self._attr_cb)
        self.local_switch.provision(register=True)
        self.stack.start(form_network=True)
        self.log("coordinator short=0x%04x ieee=%s" % (int(self.stack.get_short_addr()) & 0xFFFF, binascii.hexlify(self.stack.get_ieee_addr()).decode()))
        try:
            self.stack.permit_join(255)
            self.log("permit_join started 255s")
        except Exception as exc:
            self.log("permit_join deferred err=%s" % exc)

    def _probe(self):
        out = {
            "target_short": int(self.target_short),
            "target_ep": int(self.target_ep),
        }
        if self.target_short in (0x0000, 0xFFFF):
            out["error"] = "target not discovered"
            self.last_probe = out
            return out
        try:
            out["onoff_ep1"] = bool(
                self.stack.get_attribute(
                    1,
                    uzigbee.CLUSTER_ID_ON_OFF,
                    uzigbee.ATTR_ON_OFF_ON_OFF,
                    uzigbee.CLUSTER_ROLE_SERVER,
                )
            )
        except Exception as exc:
            out["onoff_ep1_error"] = str(exc)
        try:
            raw = int(
                self.stack.get_attribute(
                    2,
                    uzigbee.CLUSTER_ID_TEMP_MEASUREMENT,
                    uzigbee.ATTR_TEMP_MEASUREMENT_VALUE,
                    uzigbee.CLUSTER_ROLE_SERVER,
                )
            )
            out["temp_ep2_c"] = float(raw) / 100.0
        except Exception as exc:
            out["temp_ep2_error"] = str(exc)
        try:
            status = int(
                self.stack.get_attribute(
                    3,
                    uzigbee.CLUSTER_ID_IAS_ZONE,
                    uzigbee.ATTR_IAS_ZONE_STATUS,
                    uzigbee.CLUSTER_ROLE_SERVER,
                )
            )
            out["contact_ep3"] = (status & int(uzigbee.IAS_ZONE_STATUS_ALARM1)) == 0
        except Exception as exc:
            out["contact_ep3_error"] = str(exc)
        try:
            status = int(
                self.stack.get_attribute(
                    4,
                    uzigbee.CLUSTER_ID_IAS_ZONE,
                    uzigbee.ATTR_IAS_ZONE_STATUS,
                    uzigbee.CLUSTER_ROLE_SERVER,
                )
            )
            out["motion_ep4"] = (status & int(uzigbee.IAS_ZONE_STATUS_ALARM1)) != 0
        except Exception as exc:
            out["motion_ep4_error"] = str(exc)
        self.last_probe = out
        return out

    def _send_cmd(self, action, query):
        self.target_short = _parse_u16(query.get("addr"), self.target_short)
        self.target_ep = _parse_u8(query.get("ep"), self.target_ep)
        if self.target_short in (0x0000, 0xFFFF):
            raise ValueError("target short not set")
        if action == "on":
            self.local_switch.send_on(self.target_short, self.target_ep)
            self.log("cmd on short=0x%04x ep=%d" % (self.target_short, self.target_ep))
        elif action == "off":
            self.local_switch.send_off(self.target_short, self.target_ep)
            self.log("cmd off short=0x%04x ep=%d" % (self.target_short, self.target_ep))
        elif action == "toggle":
            self.local_switch.toggle(self.target_short, self.target_ep)
            self.log("cmd toggle short=0x%04x ep=%d" % (self.target_short, self.target_ep))
        elif action == "level":
            level = int(query.get("v", "128"))
            if level < 0:
                level = 0
            if level > 254:
                level = 254
            self.local_switch.send_level(self.target_short, level, self.target_ep)
            self.log("cmd level=%d short=0x%04x ep=%d" % (level, self.target_short, self.target_ep))
        else:
            raise ValueError("unknown action")

    def _html(self):
        rows = []
        rows.append("<h2>uZigbee Coordinator Web Portal (Dual Test)</h2>")
        rows.append("<p>ip=%s target=0x%04x ep=%d</p>" % (_esc(self.ip), int(self.target_short), int(self.target_ep)))
        rows.append('<p><a href="/permit?sec=120">permit join 120s</a> | <a href="/probe">probe sensors</a></p>')
        rows.append('<p><a href="/on">on</a> | <a href="/off">off</a> | <a href="/toggle">toggle</a> | <a href="/level?v=128">level128</a></p>')
        rows.append("<h3>Last Probe</h3><pre>%s</pre>" % _esc(self.last_probe))
        rows.append("<h3>Recent Attributes</h3><pre>%s</pre>" % _esc(self.attr_rows[-10:]))
        rows.append("<h3>Logs</h3><pre>%s</pre>" % _esc("\n".join(self.logs[-20:])))
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
                self.stack.permit_join(sec)
                self.log("permit_join %ss" % sec)
                body = "ok permit_join %d" % sec
                conn.send(self._response("200 OK", body, "text/plain"))
                return
            if route == "/probe":
                out = self._probe()
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
            conn.send(self._response("500 Internal Server Error", str(exc), "text/plain"))

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
            gc.collect()
            time.sleep_ms(20)


app = App()
app.run()

