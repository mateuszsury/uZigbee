"""Router high-level demo: Zigbee color light endpoint mirrored to NeoPixel on GPIO8."""

import gc
import time

import uzigbee

try:
    from machine import Pin
except Exception as exc:
    print("router_fail machine.Pin unavailable: %s" % exc)
    raise

try:
    from neopixel import NeoPixel
except Exception as exc:
    print("neopixel module missing, fallback bitstream driver: %s" % exc)
    import machine

    class NeoPixel:
        def __init__(self, pin, n, bpp=3):
            self.pin = pin
            self.n = int(n)
            self.bpp = int(bpp)
            self.buf = bytearray(self.n * self.bpp)

        def __setitem__(self, index, value):
            i = int(index) * self.bpp
            r, g, b = [int(v) & 0xFF for v in value]
            # WS2812 uses GRB byte order.
            self.buf[i + 0] = g
            self.buf[i + 1] = r
            self.buf[i + 2] = b

        def __getitem__(self, index):
            i = int(index) * self.bpp
            g = int(self.buf[i + 0])
            r = int(self.buf[i + 1])
            b = int(self.buf[i + 2])
            return (r, g, b)

        def write(self):
            machine.bitstream(self.pin, 0, (400, 850, 800, 450), self.buf)


LED_PIN = 8
LED_COUNT = 1
ENDPOINT_ID = 1
ACTOR_NAME = "neo_color"
# Default safe join mask (11/15/20/25) for auto/guided commissioning.
AUTO_JOIN_CHANNEL_MASK = (1 << 11) | (1 << 15) | (1 << 20) | (1 << 25)
# Advanced override only: keep None for default guided+auto commissioning.
# Example:
# FIXED_NETWORK_PROFILE = {"channel": 20, "pan_id": 0x1A62, "extended_pan_id": "00124b0001c6c6c6"}
FIXED_NETWORK_PROFILE = None


def _clamp(v, lo, hi):
    v = float(v)
    if v < float(lo):
        return float(lo)
    if v > float(hi):
        return float(hi)
    return float(v)


def _linear_to_srgb(v):
    if v <= 0.0031308:
        return 12.92 * v
    return 1.055 * (v ** (1.0 / 2.4)) - 0.055


def _xy_to_rgb(x_raw, y_raw, level):
    x = _clamp(float(int(x_raw) & 0xFFFF) / 65535.0, 0.0001, 1.0)
    y = _clamp(float(int(y_raw) & 0xFFFF) / 65535.0, 0.0001, 1.0)
    z = _clamp(1.0 - x - y, 0.0, 1.0)
    bri = _clamp(float(int(level) & 0xFF) / 254.0, 0.0, 1.0)
    if bri <= 0.0:
        return 0, 0, 0

    Y = bri
    X = (Y / y) * x
    Z = (Y / y) * z

    r_lin = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g_lin = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b_lin = X * 0.051713 - Y * 0.121364 + Z * 1.011530

    r = _clamp(_linear_to_srgb(_clamp(r_lin, 0.0, 1.0)), 0.0, 1.0)
    g = _clamp(_linear_to_srgb(_clamp(g_lin, 0.0, 1.0)), 0.0, 1.0)
    b = _clamp(_linear_to_srgb(_clamp(b_lin, 0.0, 1.0)), 0.0, 1.0)
    return int(round(r * 255.0)), int(round(g * 255.0)), int(round(b * 255.0))


def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return int(time.ticks_ms())
    return int(time.time() * 1000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return int(time.ticks_diff(int(a), int(b)))
    return int(a) - int(b)


def _ticks_add(a, b):
    if hasattr(time, "ticks_add"):
        return int(time.ticks_add(int(a), int(b)))
    return int(a) + int(b)


def _is_joined_short(short_addr):
    if short_addr is None:
        return False
    try:
        value = int(short_addr) & 0xFFFF
    except Exception:
        return False
    # 0xFFFE = unknown short, 0xFFFF = invalid.
    return value not in (0xFFFE, 0xFFFF)


class App:
    def __init__(self):
        self.router = self._new_router()
        self.router.add_light(endpoint_id=ENDPOINT_ID, name=ACTOR_NAME, dimmable=True, color=True)
        self.router.on_signal(self._signal_cb)
        if hasattr(self.router, "on_attribute"):
            self.router.on_attribute(self._on_attr)
        elif hasattr(self.router, "stack") and hasattr(self.router.stack, "on_attribute"):
            self.router.stack.on_attribute(self._on_attr)
            print("router compat: using router.stack.on_attribute fallback")
        else:
            print("router_fail attribute callback API unavailable")
            raise AttributeError("router attribute callback API unavailable")

        self.np = NeoPixel(Pin(LED_PIN, Pin.OUT), LED_COUNT)
        self.state_on = False
        self.state_level = 254
        self.state_x = 0x616B
        self.state_y = 0x607D
        self.state_ct = 250
        self._apply_led()
        self.joined = False
        self._join_attempt = 0
        self._next_join_try_ms = 0
        self._join_confirmed_session = False

    def _new_router(self):
        kwargs = {
            "auto_register": True,
            "commissioning_mode": "guided",
            "auto_join_channel_mask": AUTO_JOIN_CHANNEL_MASK,
            "join_retry_max": 8,
            "join_retry_base_ms": 700,
            "join_retry_max_backoff_ms": 12000,
        }
        fixed_profile = FIXED_NETWORK_PROFILE
        if isinstance(fixed_profile, dict):
            channel = fixed_profile.get("channel", None)
            pan_id = fixed_profile.get("pan_id", None)
            ext_pan_id = fixed_profile.get("extended_pan_id", None)
            if channel is not None and pan_id is not None and ext_pan_id:
                kwargs["commissioning_mode"] = "fixed"
                kwargs["channel"] = int(channel)
                kwargs["pan_id"] = int(pan_id)
                kwargs["extended_pan_id"] = str(ext_pan_id)
        while True:
            try:
                return uzigbee.Router(**kwargs)
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
                print("router compat: drop unsupported kwarg %s" % key)

    def _signal_cb(self, signal_id, status):
        try:
            name = uzigbee.signal_name(signal_id)
        except Exception:
            name = "unknown"
        signal_id = int(signal_id)
        status = int(status)
        print("signal %s(0x%02x) status=%d" % (name, int(signal_id), int(status)))
        if name == "steering":
            if status == 0:
                self._join_confirmed_session = True
            elif status < 0:
                self._join_confirmed_session = False

    def _apply_led(self):
        if not self.state_on or int(self.state_level) <= 0:
            rgb = (0, 0, 0)
        else:
            rgb = _xy_to_rgb(self.state_x, self.state_y, self.state_level)
        self.np[0] = rgb
        self.np.write()
        return rgb

    def _on_attr(self, *event):
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
        if int(endpoint) != ENDPOINT_ID:
            return

        cluster_id = int(cluster_id) & 0xFFFF
        attr_id = int(attr_id) & 0xFFFF
        if cluster_id == int(uzigbee.CLUSTER_ID_ON_OFF) and attr_id == int(uzigbee.ATTR_ON_OFF_ON_OFF):
            self.state_on = bool(value)
        elif cluster_id == int(uzigbee.CLUSTER_ID_LEVEL_CONTROL) and attr_id == int(uzigbee.ATTR_LEVEL_CONTROL_CURRENT_LEVEL):
            self.state_level = int(value) & 0xFF
        elif cluster_id == int(uzigbee.CLUSTER_ID_COLOR_CONTROL) and attr_id == int(uzigbee.ATTR_COLOR_CONTROL_CURRENT_X):
            self.state_x = int(value) & 0xFFFF
        elif cluster_id == int(uzigbee.CLUSTER_ID_COLOR_CONTROL) and attr_id == int(uzigbee.ATTR_COLOR_CONTROL_CURRENT_Y):
            self.state_y = int(value) & 0xFFFF
        elif cluster_id == int(uzigbee.CLUSTER_ID_COLOR_CONTROL) and attr_id == int(uzigbee.ATTR_COLOR_CONTROL_COLOR_TEMPERATURE):
            self.state_ct = int(value) & 0xFFFF
        else:
            return

        rgb = self._apply_led()
        print(
            "attr src=%s ep=%d cluster=0x%04x attr=0x%04x value=%s -> rgb=%s on=%s level=%d xy=(%d,%d) ct=%d"
            % (
                "none" if source_short is None else ("0x%04x" % (int(source_short) & 0xFFFF)),
                int(endpoint),
                int(cluster_id),
                int(attr_id),
                value,
                rgb,
                bool(self.state_on),
                int(self.state_level),
                int(self.state_x),
                int(self.state_y),
                int(self.state_ct),
            )
        )

    def run(self):
        self._ensure_join(force=True)
        status = self.router.status()
        print(
            "router_ready short=%s ieee=%s endpoints=%s"
            % (status.get("short_addr"), status.get("ieee_hex"), status.get("endpoint_ids"))
        )

        counter = 0
        while True:
            self._ensure_join(force=False)
            rgb = tuple(int(v) for v in self.np[0])
            print(
                "tick=%d neo rgb=%s on=%s level=%d xy=(%d,%d) ct=%d"
                % (
                    int(counter),
                    rgb,
                    bool(self.state_on),
                    int(self.state_level),
                    int(self.state_x),
                    int(self.state_y),
                    int(self.state_ct),
                )
            )
            counter += 1
            gc.collect()
            time.sleep(1)

    def _ensure_join(self, force=False):
        now = _ticks_ms()
        if (not force) and _ticks_diff(now, self._next_join_try_ms) < 0:
            return

        if force and self._join_attempt == 0:
            self._join_attempt += 1
            print("router_join_retry attempt=%d (initial)" % int(self._join_attempt))
            try:
                self.router.start(join_parent=True)
            except Exception as exc:
                print("router_join_retry_error %s" % exc)
            self._next_join_try_ms = _ticks_add(now, 3000)
            return

        status = self.router.status()
        short_addr = status.get("short_addr")
        if self._join_confirmed_session and _is_joined_short(short_addr):
            if not self.joined:
                self.joined = True
                print("router_joined short=%s ieee=%s" % (short_addr, status.get("ieee_hex")))
            self._next_join_try_ms = _ticks_add(now, 12000)
            return

        self.joined = False
        self._join_attempt += 1
        print("router_join_retry attempt=%d" % int(self._join_attempt))
        try:
            if self._join_attempt == 1:
                self.router.start(join_parent=True)
            else:
                self.router.join_parent()
        except Exception as exc:
            print("router_join_retry_error %s" % exc)
        self._next_join_try_ms = _ticks_add(now, 10000)


App().run()
