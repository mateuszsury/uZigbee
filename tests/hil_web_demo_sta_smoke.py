"""HIL smoke for coordinator web demo with WiFi STA connection."""

import socket
import time

import uzigbee

try:
    import network
except ImportError:
    network = None


ESP_ERR_INVALID_STATE = 259
STA_SSID = "STAR1"
STA_PASSWORD = "wodasodowa"
STA_TIMEOUT_S = 60

z = uzigbee.ZigbeeStack()
if network is None:
    raise RuntimeError("network module is not available in this firmware")

sta = network.WLAN(network.STA_IF)
sta.active(True)
if hasattr(sta, "disconnect"):
    try:
        sta.disconnect()
    except Exception:
        pass
sta.connect(STA_SSID, STA_PASSWORD)

start_ms = time.ticks_ms()
timeout_ms = STA_TIMEOUT_S * 1000
while not sta.isconnected():
    if time.ticks_diff(time.ticks_ms(), start_ms) >= timeout_ms:
        break
    time.sleep_ms(200)

assert sta.isconnected(), "STA connect timeout for SSID STAR1"
ip = sta.ifconfig()[0]
print("uzigbee.hil.webdemo.sta.ip", ip)

z.init(uzigbee.ROLE_COORDINATOR)

switch = uzigbee.DimmableSwitch(
    endpoint_id=1,
    stack=z,
    manufacturer="uzigbee",
    model="uzb_web_demo_switch",
    sw_build_id="demo",
)

try:
    switch.provision(register=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

try:
    z.start(form_network=True)
except OSError as exc:
    if not exc.args or exc.args[0] != ESP_ERR_INVALID_STATE:
        raise

time.sleep(1)

short_addr = int(z.get_short_addr())
ieee = z.get_ieee_addr()
print("uzigbee.hil.webdemo.sta.short_addr", hex(short_addr))
print("uzigbee.hil.webdemo.sta.ieee_len", len(ieee))

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 8080))
s.listen(1)
s.close()

stats = z.event_stats()
print("uzigbee.hil.webdemo.sta.stats", stats)
assert len(ieee) == 8
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.webdemo.sta.result PASS")
