"""HIL: coordinator high-level test for endpoint overlap + long-run toggle."""

import time

import uzigbee


MAX_RUNTIME_S = 420
TOGGLE_PERIOD_MS = 1000
TARGET_ROUNDS = 120
AUTO_CHANNEL_PREFERRED = (15, 20, 25, 11)
AUTO_CHANNEL_BLACKLIST = (26,)
SIGNAL_PANID_CONFLICT = int(getattr(uzigbee, "SIGNAL_PANID_CONFLICT_DETECTED", 0x31))


class App:
    def __init__(self):
        self.coordinator = self._new_coordinator()
        self.target = None
        self.round_count = 0
        self.error_count = 0
        self.next_toggle_ms = 0
        self.start_ms = time.ticks_ms()
        self._conflict_simulated = False

    def _new_coordinator(self):
        kwargs = {
            "network_mode": "guided",
            "auto_channel_scan_wifi": False,
            "auto_channel_preferred": AUTO_CHANNEL_PREFERRED,
            "auto_channel_blacklist": AUTO_CHANNEL_BLACKLIST,
            "auto_discovery": True,
            "strict_discovery": False,
            "include_power_desc": False,
            "fallback_without_power_desc": True,
            "opportunistic_last_joined_scan": True,
            "discover_timeout_ms": 5000,
            "discover_poll_ms": 150,
            "join_debounce_ms": 1200,
            "discovery_retry_max": 6,
            "discovery_retry_base_ms": 250,
            "discovery_retry_max_backoff_ms": 5000,
            "self_heal_enabled": True,
            "self_heal_retry_max": 3,
            "self_heal_retry_base_ms": 200,
            "self_heal_retry_max_backoff_ms": 2000,
        }
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
                self._log("coordinator compat: drop unsupported kwarg %s" % key)

    def _log(self, msg):
        print("[coord-dual %d] %s" % (int(time.ticks_ms() // 1000), msg))

    def _signal_cb(self, signal_id, status):
        try:
            name = uzigbee.signal_name(signal_id)
        except Exception:
            name = "unknown"
        self._log("signal %s(0x%02x) status=%d" % (name, int(signal_id), int(status)))

    def _device_added_cb(self, device):
        self._log(
            "device_added short=0x%04x endpoints=%s features=%s"
            % (
                int(device.short_addr) & 0xFFFF,
                device.endpoints(),
                sorted(tuple(device.features)),
            )
        )
        if device.has_feature("on_off") and self.target is None:
            self.target = device
            self.next_toggle_ms = time.ticks_add(time.ticks_ms(), 1500)
            self._log("target_set short=0x%04x" % (int(device.short_addr) & 0xFFFF))

    def _ensure_target(self):
        if self.target is not None:
            return
        found = self.coordinator.select_device(feature="on_off")
        if found is not None:
            self.target = found
            self.next_toggle_ms = time.ticks_add(time.ticks_ms(), 1500)
            self._log("target_auto short=0x%04x" % (int(found.short_addr) & 0xFFFF))

    def _verify_overlap_ready(self, timeout_ms=90000):
        if self.target is None:
            return False
        start_ms = time.ticks_ms()
        next_refresh_ms = start_ms
        while True:
            eps = self.target.feature_endpoints("on_off")
            self._log("target_onoff_endpoints=%s" % (eps,))
            if len(eps) >= 2:
                return True

            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, int(next_refresh_ms)) >= 0:
                try:
                    self.coordinator.discover_device(self.target.short_addr, strict=False)
                    refreshed = self.coordinator.get_device(self.target.short_addr)
                    if refreshed is not None:
                        self.target = refreshed
                    self._log(
                        "refresh_discovery short=0x%04x"
                        % (int(self.target.short_addr) & 0xFFFF)
                    )
                except Exception as exc:
                    self._log("refresh_discovery err=%s" % exc)
                next_refresh_ms = time.ticks_add(now_ms, 4000)

            self.coordinator.process_pending_discovery(max_items=8)
            self._ensure_target()
            if self.target is None:
                self._log("TEST_FAIL target disappeared during overlap verification")
                return False
            if time.ticks_diff(now_ms, start_ms) > int(timeout_ms):
                self._log("TEST_FAIL on_off endpoint overlap missing: endpoints=%s" % (eps,))
                return False
            time.sleep_ms(120)

    def _toggle_round(self):
        if self.target is None:
            return
        now_ms = time.ticks_ms()
        if time.ticks_diff(now_ms, int(self.next_toggle_ms)) < 0:
            return

        state_ep1 = (self.round_count % 2) == 0
        state_ep2 = not state_ep1

        try:
            ep1 = self.target.switch(1)
            ep2 = self.target.switch(2)
            if state_ep1:
                ep1.on()
            else:
                ep1.off()
            if state_ep2:
                ep2.on()
            else:
                ep2.off()

            if (self.round_count % 10) == 0:
                read1 = ep1.read.on_off(use_cache=False)
                read2 = ep2.read.on_off(use_cache=False)
                self._log(
                    "readback ep1=%s ep2=%s round=%d"
                    % ("ON" if read1 else "OFF", "ON" if read2 else "OFF", int(self.round_count))
                )

            self.round_count += 1
            self._log(
                "round=%d ep1=%s ep2=%s short=0x%04x"
                % (
                    int(self.round_count),
                    "ON" if state_ep1 else "OFF",
                    "ON" if state_ep2 else "OFF",
                    int(self.target.short_addr) & 0xFFFF,
                )
            )
            if (not self._conflict_simulated) and self.round_count >= 20:
                if hasattr(self.coordinator, "_handle_signal"):
                    self._log("simulate_conflict signal=panid_conflict_detected")
                    try:
                        self.coordinator._handle_signal(SIGNAL_PANID_CONFLICT, 0)
                    except Exception as exc:
                        self._log("simulate_conflict_err %s" % exc)
                    self._conflict_simulated = True
        except Exception as exc:
            self.error_count += 1
            self._log("toggle_error count=%d err=%s" % (int(self.error_count), exc))

        self.next_toggle_ms = time.ticks_add(now_ms, TOGGLE_PERIOD_MS)

    def run(self):
        self.coordinator.on_signal(self._signal_cb)
        self.coordinator.on_device_added(self._device_added_cb)
        if hasattr(self.coordinator, "on_commissioning_event"):
            self.coordinator.on_commissioning_event(
                lambda event: self._log("commissioning_event %s" % event)
            )
        self.coordinator.start(form_network=True)
        self._log("coordinator_started")
        try:
            self._log("network_info=%s" % self.coordinator.network_info())
        except Exception:
            pass

        wait_start_ms = time.ticks_ms()
        next_permit_ms = wait_start_ms
        while True:
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, next_permit_ms) >= 0:
                try:
                    self.coordinator.permit_join(120)
                    self._log("permit_join 120s")
                except Exception as exc:
                    self._log("permit_join_retry err=%s" % exc)
                next_permit_ms = time.ticks_add(now_ms, 5000)

            self.coordinator.process_pending_discovery(max_items=6)
            self._ensure_target()

            if self.target is not None:
                break

            if time.ticks_diff(now_ms, wait_start_ms) > 180000:
                self._log("TEST_FAIL timeout waiting_for_target")
                return
            time.sleep_ms(120)

        if not self._verify_overlap_ready():
            return

        self.next_toggle_ms = time.ticks_add(time.ticks_ms(), 1500)
        self._log("target_ready short=0x%04x" % (int(self.target.short_addr) & 0xFFFF))

        while True:
            self.coordinator.process_pending_discovery(max_items=4)
            self._ensure_target()
            self._toggle_round()

            if self.round_count >= TARGET_ROUNDS and self.error_count == 0 and self.target is not None:
                self._log(
                    "TEST_PASS rounds=%d short=0x%04x"
                    % (int(self.round_count), int(self.target.short_addr) & 0xFFFF)
                )
                return

            elapsed_ms = time.ticks_diff(time.ticks_ms(), int(self.start_ms))
            if elapsed_ms > MAX_RUNTIME_S * 1000:
                self._log(
                    "TEST_FAIL timeout rounds=%d errors=%d target=%s"
                    % (
                        int(self.round_count),
                        int(self.error_count),
                        "none" if self.target is None else ("0x%04x" % (int(self.target.short_addr) & 0xFFFF)),
                    )
                )
                return

            time.sleep_ms(50)


App().run()
