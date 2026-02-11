"""Coordinator + Web UI demo app for uzigbee.

This is an example application only. It is not part of the uzigbee library API.
"""

try:
    import ubinascii as binascii
except ImportError:
    import binascii

import gc
import socket
import time

import uzigbee
from uzigbee import ota as uzigbee_ota

try:
    import network
except ImportError:
    network = None


ESP_ERR_INVALID_STATE = 259
HTTP_PORT = 80
MAX_LOG_LINES = 24
DEFAULT_STA_SSID = "STAR1"
DEFAULT_STA_PASSWORD = "wodasodowa"
STA_RECONNECT_INTERVAL_MS = 15000
WIFI_HEARTBEAT_INTERVAL_MS = 10000


def parse_u16(value, default=0):
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
        raise ValueError("value out of range: %s" % text)
    return out


def parse_u8(value, default=1):
    if value is None:
        return int(default) & 0xFF
    text = str(value).strip()
    if not text:
        return int(default) & 0xFF
    out = int(text)
    if out < 1 or out > 240:
        raise ValueError("endpoint out of range: %s" % text)
    return out


def parse_query_string(raw_query):
    out = {}
    if raw_query is None:
        return out
    text = str(raw_query)
    if not text:
        return out
    for chunk in text.split("&"):
        if not chunk:
            continue
        if "=" in chunk:
            key, value = chunk.split("=", 1)
        else:
            key, value = chunk, ""
        out[key] = value.replace("+", " ")
    return out


def html_escape(text):
    s = str(text)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s


class CoordinatorWebDemo:
    def __init__(
        self,
        wifi_mode="sta",
        sta_ssid=DEFAULT_STA_SSID,
        sta_password=DEFAULT_STA_PASSWORD,
        sta_timeout_s=45,
        sta_fallback_ap=True,
        always_on_ap=True,
        ap_ssid="uZigbeeDemo",
        ap_password="uzigbee1234",
        ap_channel=6,
        target_short_addr=0x0000,
        target_endpoint=1,
    ):
        self.stack = uzigbee.ZigbeeStack()
        self.switch = uzigbee.DimmableSwitch(
            endpoint_id=1,
            stack=self.stack,
            manufacturer="uzigbee",
            model="uzb_web_demo_switch",
            sw_build_id="demo",
        )
        self.wifi_mode = str(wifi_mode).lower()
        self.sta_ssid = str(sta_ssid)
        self.sta_password = str(sta_password)
        self.sta_timeout_s = int(sta_timeout_s)
        self.sta_fallback_ap = bool(sta_fallback_ap)
        self.always_on_ap = bool(always_on_ap)
        self.ap_ssid = ap_ssid
        self.ap_password = ap_password
        self.ap_channel = int(ap_channel)
        self.target_short_addr = int(target_short_addr) & 0xFFFF
        self.target_endpoint = int(target_endpoint)
        self.last_error = ""
        self.logs = []
        self.wifi_ip = None
        self.sta_ip = None
        self.ap_ip = None
        self._ap_if = None
        self._sta_if = None
        self._server_socket = None
        self._last_sta_attempt_ms = 0
        self._last_wifi_heartbeat_ms = 0
        self._auto_target_supported = True
        self._ota_control_supported = None

    def _log(self, message):
        stamp = int(time.ticks_ms() // 1000)
        line = "[%d] %s" % (stamp, message)
        self.logs.append(line)
        if len(self.logs) > MAX_LOG_LINES:
            self.logs = self.logs[-MAX_LOG_LINES:]
        print(line)

    def _set_error(self, where, exc):
        self.last_error = "%s: %s" % (where, exc)
        self._log("ERROR " + self.last_error)

    def _adopt_last_joined_target(self):
        if not self._auto_target_supported:
            return
        try:
            short_addr = self.stack.get_last_joined_short_addr()
        except Exception as exc:
            text = str(exc)
            if "not available in firmware" in text:
                self._auto_target_supported = False
                self._log("auto-target disabled: %s" % text)
                return
            self._set_error("last_joined_short", exc)
            return

        if short_addr is None:
            return
        short_addr = int(short_addr) & 0xFFFF
        if short_addr in (0x0000, 0xFFFF):
            return
        if short_addr == self.target_short_addr:
            return
        self.target_short_addr = short_addr
        self._log(
            "auto-target short=0x%04x ep=%d" % (self.target_short_addr, self.target_endpoint)
        )

    def _signal_cb(self, signal_id, status):
        try:
            name = uzigbee.signal_name(signal_id)
        except Exception:
            name = "unknown"
        self._log("signal %s(0x%02x) status=%d" % (name, int(signal_id), int(status)))
        if int(status) == 0 and name in ("device_announce", "device_update", "device_authorized"):
            self._adopt_last_joined_target()

    def _call_with_invalid_state_ok(self, label, fn):
        try:
            return fn()
        except OSError as exc:
            if exc.args and int(exc.args[0]) == ESP_ERR_INVALID_STATE:
                self._log("%s already initialized (%d)" % (label, ESP_ERR_INVALID_STATE))
                return None
            raise

    def _self_ieee_hex(self):
        raw = self.stack.get_ieee_addr()
        return binascii.hexlify(raw).decode()

    def _self_short_hex(self):
        return "0x%04x" % int(self.stack.get_short_addr())

    def start_zigbee(self):
        self._call_with_invalid_state_ok("init", lambda: self.stack.init(uzigbee.ROLE_COORDINATOR))
        self.stack.on_signal(self._signal_cb)
        self._call_with_invalid_state_ok("switch.provision", lambda: self.switch.provision(register=True))
        self._call_with_invalid_state_ok("start", lambda: self.stack.start(form_network=True))
        self._ota_control_supported = bool(uzigbee_ota.is_control_supported(self.stack))
        self._log("ota control supported=%s" % self._ota_control_supported)
        self._log("coordinator short=%s ieee=%s" % (self._self_short_hex(), self._self_ieee_hex()))

    def setup_ap(self):
        if network is None:
            raise RuntimeError("network module is not available in this firmware")

        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(True)
        cfg = {
            "essid": self.ap_ssid,
            "channel": self.ap_channel,
        }
        if self.ap_password and len(self.ap_password) >= 8:
            cfg["password"] = self.ap_password
            if hasattr(network, "AUTH_WPA_WPA2_PSK"):
                cfg["authmode"] = network.AUTH_WPA_WPA2_PSK
        ap_if.config(**cfg)
        self._ap_if = ap_if
        self.ap_ip = ap_if.ifconfig()[0]
        if self.wifi_ip is None:
            self.wifi_ip = self.ap_ip
        self._log("wifi ap started ssid=%s ip=%s" % (self.ap_ssid, self.ap_ip))

    def setup_sta(self):
        if network is None:
            raise RuntimeError("network module is not available in this firmware")
        if not self.sta_ssid:
            raise ValueError("sta_ssid must not be empty")

        # Ensure AP interface from previous runs does not interfere with STA join.
        try:
            ap_if = network.WLAN(network.AP_IF)
            if ap_if.active():
                ap_if.active(False)
        except Exception:
            pass

        sta_if = network.WLAN(network.STA_IF)
        if sta_if.active():
            sta_if.active(False)
            time.sleep_ms(100)
        sta_if.active(True)
        if hasattr(sta_if, "config"):
            # Disable modem power save when supported to reduce STA drops.
            try:
                if hasattr(network, "PM_NONE"):
                    sta_if.config(pm=network.PM_NONE)
                else:
                    sta_if.config(pm=0)
            except Exception:
                pass
        timeout_ms = max(1, self.sta_timeout_s) * 1000
        attempts = 2
        for attempt in range(1, attempts + 1):
            if hasattr(sta_if, "disconnect"):
                try:
                    sta_if.disconnect()
                except Exception:
                    pass
            sta_if.connect(self.sta_ssid, self.sta_password)
            self._log("wifi sta connecting ssid=%s attempt=%d/%d" % (self.sta_ssid, attempt, attempts))

            start_ms = time.ticks_ms()
            while True:
                if sta_if.isconnected():
                    break
                if time.ticks_diff(time.ticks_ms(), start_ms) >= timeout_ms:
                    break
                time.sleep_ms(200)

            if sta_if.isconnected():
                break
            status = None
            if hasattr(sta_if, "status"):
                try:
                    status = sta_if.status()
                except Exception:
                    status = None
            self._log("wifi sta attempt failed status=%s" % status)

        if not sta_if.isconnected():
            status = None
            if hasattr(sta_if, "status"):
                try:
                    status = sta_if.status()
                except Exception:
                    status = None
            raise RuntimeError("sta connect timeout status=%s" % status)

        self._sta_if = sta_if
        self.sta_ip = sta_if.ifconfig()[0]
        self.wifi_ip = self.sta_ip
        self._log("wifi sta connected ssid=%s ip=%s" % (self.sta_ssid, self.sta_ip))

    def _refresh_ip_state(self):
        self.sta_ip = None
        self.ap_ip = None
        if self._sta_if is not None:
            try:
                if self._sta_if.isconnected():
                    self.sta_ip = self._sta_if.ifconfig()[0]
            except Exception:
                self.sta_ip = None
        if self._ap_if is not None:
            try:
                if self._ap_if.active():
                    self.ap_ip = self._ap_if.ifconfig()[0]
            except Exception:
                self.ap_ip = None
        if self.sta_ip:
            self.wifi_ip = self.sta_ip
        elif self.ap_ip:
            self.wifi_ip = self.ap_ip
        else:
            self.wifi_ip = None

    def _wifi_watchdog_tick(self):
        self._refresh_ip_state()
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_wifi_heartbeat_ms) >= WIFI_HEARTBEAT_INTERVAL_MS:
            self._last_wifi_heartbeat_ms = now
            sta_connected = False
            if self._sta_if is not None:
                try:
                    sta_connected = self._sta_if.isconnected()
                except Exception:
                    sta_connected = False
            self._log(
                "wifi heartbeat sta_connected=%s sta_ip=%s ap_ip=%s active_ip=%s"
                % (sta_connected, self.sta_ip, self.ap_ip, self.wifi_ip)
            )

        if self.wifi_mode != "sta" or self._sta_if is None:
            return

        try:
            if self._sta_if.isconnected():
                return
        except Exception:
            pass

        if time.ticks_diff(now, self._last_sta_attempt_ms) < STA_RECONNECT_INTERVAL_MS:
            return
        self._last_sta_attempt_ms = now
        try:
            if hasattr(self._sta_if, "disconnect"):
                self._sta_if.disconnect()
        except Exception:
            pass
        try:
            self._sta_if.connect(self.sta_ssid, self.sta_password)
            self._log("wifi sta reconnect requested ssid=%s" % self.sta_ssid)
        except Exception as exc:
            self._set_error("wifi_sta_reconnect", exc)

    def setup_wifi(self):
        mode = self.wifi_mode
        if mode == "sta":
            if self.always_on_ap:
                try:
                    self.setup_ap()
                except Exception as exc:
                    self._set_error("wifi_ap", exc)
            try:
                self.setup_sta()
                self._last_sta_attempt_ms = time.ticks_ms()
                return
            except Exception as exc:
                self._set_error("wifi_sta", exc)
                if not self.sta_fallback_ap and not self.always_on_ap:
                    raise
                if self._ap_if is None:
                    self._log("wifi sta failed, fallback to ap")
                    self.setup_ap()
                self._refresh_ip_state()
                return
        if mode == "ap":
            self.setup_ap()
            return
        raise ValueError("unsupported wifi_mode: %s" % mode)

    def set_target(self, short_addr_text, endpoint_text):
        self.target_short_addr = parse_u16(short_addr_text, self.target_short_addr)
        self.target_endpoint = parse_u8(endpoint_text, self.target_endpoint)
        self._log(
            "target updated short=0x%04x ep=%d" % (self.target_short_addr, self.target_endpoint)
        )

    def permit_join(self, seconds):
        value = int(seconds)
        if value < 1:
            value = 1
        if value > 254:
            value = 254
        self.stack.permit_join(value)
        self._log("permit_join %ds" % value)
        return value

    def cmd_on(self):
        self.switch.send_on(self.target_short_addr, self.target_endpoint)
        self._log("on short=0x%04x ep=%d" % (self.target_short_addr, self.target_endpoint))

    def cmd_off(self):
        self.switch.send_off(self.target_short_addr, self.target_endpoint)
        self._log("off short=0x%04x ep=%d" % (self.target_short_addr, self.target_endpoint))

    def cmd_toggle(self):
        self.switch.toggle(self.target_short_addr, self.target_endpoint)
        self._log("toggle short=0x%04x ep=%d" % (self.target_short_addr, self.target_endpoint))

    def cmd_level(self, level):
        value = int(level)
        if value < 0:
            value = 0
        if value > 254:
            value = 254
        self.switch.send_level(
            self.target_short_addr,
            value,
            dst_endpoint=self.target_endpoint,
            transition_ds=5,
            with_onoff=True,
        )
        self._log("level=%d short=0x%04x ep=%d" % (value, self.target_short_addr, self.target_endpoint))
        return value

    def _status_rows(self):
        rows = []
        try:
            rows.append(("coordinator_short", self._self_short_hex()))
        except Exception as exc:
            rows.append(("coordinator_short", "error: %s" % exc))
        try:
            rows.append(("coordinator_ieee", self._self_ieee_hex()))
        except Exception as exc:
            rows.append(("coordinator_ieee", "error: %s" % exc))
        rows.append(("target_short", "0x%04x" % self.target_short_addr))
        rows.append(("target_endpoint", str(self.target_endpoint)))
        rows.append(("wifi_mode", self.wifi_mode))
        rows.append(("sta_ip", str(self.sta_ip)))
        rows.append(("ap_ip", str(self.ap_ip)))
        rows.append(("wifi_ip", str(self.wifi_ip)))
        rows.append(("last_error", self.last_error or "-"))
        return rows

    def _render_page(self):
        status_rows = self._status_rows()
        status_html = "".join(
            "<tr><td>%s</td><td>%s</td></tr>"
            % (html_escape(key), html_escape(value))
            for key, value in status_rows
        )
        logs_html = "".join("<li>%s</li>" % html_escape(x) for x in self.logs[-12:])
        return """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>uZigbee Coordinator Demo</title>
  <style>
    body { font-family: sans-serif; margin: 16px; background: #f4f6f8; color: #18202a; }
    .card { background: #fff; border: 1px solid #dce2e8; border-radius: 10px; padding: 12px; margin-bottom: 12px; }
    table { width: 100%%; border-collapse: collapse; }
    td { border-bottom: 1px solid #edf1f5; padding: 6px; font-size: 14px; }
    form { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
    input, button { padding: 8px; font-size: 14px; }
    button { border: 1px solid #4d647e; background: #506d8b; color: #fff; border-radius: 6px; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; }
  </style>
</head>
<body>
  <h2>uZigbee Coordinator Demo</h2>
  <div class="card">
    <h3>Status</h3>
    <table>%s</table>
  </div>

  <div class="card">
    <h3>Pairing</h3>
    <form action="/pair" method="get">
      <input name="sec" value="60" />
      <button type="submit">Permit Join</button>
    </form>
  </div>

  <div class="card">
    <h3>Target Light</h3>
    <form action="/target" method="get">
      <input name="addr" value="0x%04x" />
      <input name="ep" value="%d" />
      <button type="submit">Set Target</button>
    </form>
    <div class="row">
      <form action="/on" method="get"><button type="submit">ON</button></form>
      <form action="/off" method="get"><button type="submit">OFF</button></form>
      <form action="/toggle" method="get"><button type="submit">TOGGLE</button></form>
      <form action="/level" method="get">
        <input name="v" value="128" />
        <button type="submit">SET LEVEL</button>
      </form>
    </div>
  </div>

  <div class="card">
    <h3>Log (latest)</h3>
    <ul>%s</ul>
  </div>
</body>
</html>
""" % (status_html, self.target_short_addr, self.target_endpoint, logs_html)

    def _handle_action(self, path, query):
        if path == "/pair":
            self.permit_join(query.get("sec", "60"))
        elif path == "/target":
            self.set_target(query.get("addr", ""), query.get("ep", "1"))
        elif path == "/on":
            self.cmd_on()
        elif path == "/off":
            self.cmd_off()
        elif path == "/toggle":
            self.cmd_toggle()
        elif path == "/level":
            self.cmd_level(query.get("v", "128"))

    def _serve_one(self, client):
        try:
            try:
                client.settimeout(2)
            except Exception:
                pass
            raw = client.recv(1024)
            if not raw:
                return
            first_line = raw.split(b"\r\n", 1)[0].decode()
            parts = first_line.split(" ")
            route = parts[1] if len(parts) >= 2 else "/"
            if "?" in route:
                path, query_text = route.split("?", 1)
            else:
                path, query_text = route, ""
            query = parse_query_string(query_text)
            try:
                self._handle_action(path, query)
            except Exception as exc:
                self._set_error(path, exc)

            body = self._render_page()
            head = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % len(body)
            client.send(head)
            client.send(body)
        except OSError as exc:
            self._set_error("client_io", exc)
        finally:
            try:
                client.close()
            except Exception:
                pass

    def serve_forever(self):
        addr = socket.getaddrinfo("0.0.0.0", HTTP_PORT)[0][-1]
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(addr)
        server.listen(2)
        server.settimeout(1)
        self._server_socket = server
        self._log("http server listening on %s:%d" % (addr[0], HTTP_PORT))

        while True:
            self._wifi_watchdog_tick()
            try:
                client, _ = server.accept()
            except OSError:
                gc.collect()
                continue
            self._serve_one(client)
            gc.collect()


def startup_smoke():
    demo = CoordinatorWebDemo()
    demo.start_zigbee()
    return {
        "short_addr": int(demo.stack.get_short_addr()),
        "ieee_hex": demo._self_ieee_hex(),
        "target_short_addr": int(demo.target_short_addr),
        "target_endpoint": int(demo.target_endpoint),
    }


def run():
    demo = CoordinatorWebDemo()
    demo.setup_wifi()
    demo.start_zigbee()
    demo.serve_forever()


if __name__ == "__main__":
    run()
