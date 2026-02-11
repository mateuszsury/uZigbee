"""HIL smoke for coordinator web demo prerequisites."""

import socket
import time

import uzigbee

try:
    import network
except ImportError:
    network = None


ESP_ERR_INVALID_STATE = 259

z = uzigbee.ZigbeeStack()
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
print("uzigbee.hil.webdemo.short_addr", hex(short_addr))
print("uzigbee.hil.webdemo.ieee_len", len(ieee))

if network is not None:
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    kwargs = {"essid": "uZigbeeDemoTest", "channel": 6}
    if hasattr(network, "AUTH_WPA_WPA2_PSK"):
        kwargs["authmode"] = network.AUTH_WPA_WPA2_PSK
        kwargs["password"] = "uzigbee1234"
    ap.config(**kwargs)
    ip = ap.ifconfig()[0]
    print("uzigbee.hil.webdemo.ap_ip", ip)

    # Bind test only, no long-running server in smoke.
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 8080))
    s.listen(1)
    s.close()
    ap.active(False)

stats = z.event_stats()
print("uzigbee.hil.webdemo.stats", stats)
assert len(ieee) == 8
assert stats["dropped_queue_full"] == 0
assert stats["dropped_schedule_fail"] == 0
print("uzigbee.hil.webdemo.result PASS")
