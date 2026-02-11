"""HIL: coordinator high-level autodiscovery + 1s switch control loop."""

import time

import uzigbee


MAX_RUNTIME_S = 180
TOGGLE_PERIOD_MS = 1000
TARGET_TOGGLES = 12


class App:
    def __init__(self):
        self.coordinator = uzigbee.Coordinator(
            auto_discovery=True,
            strict_discovery=False,
            include_power_desc=False,
            fallback_without_power_desc=True,
            opportunistic_last_joined_scan=True,
            discover_timeout_ms=4000,
            discover_poll_ms=150,
            join_debounce_ms=1200,
            discovery_retry_max=5,
            discovery_retry_base_ms=250,
            discovery_retry_max_backoff_ms=4000,
        )
        self.target = None
        self.toggle_count = 0
        self.error_count = 0
        self.next_toggle_ms = 0
        self.toggle_state = False
        self.start_ms = time.ticks_ms()

    def _log(self, msg):
        print("[coord %d] %s" % (int(time.ticks_ms() // 1000), msg))

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
            self.next_toggle_ms = time.ticks_add(time.ticks_ms(), 1000)
            self._log("target_set short=0x%04x" % (int(device.short_addr) & 0xFFFF))

    def _device_updated_cb(self, device):
        self._log("device_updated short=0x%04x" % (int(device.short_addr) & 0xFFFF))

    def _ensure_target(self):
        if self.target is not None:
            return
        found = self.coordinator.select_device(feature="on_off")
        if found is not None:
            self.target = found
            self.next_toggle_ms = time.ticks_add(time.ticks_ms(), 1000)
            self._log("target_auto short=0x%04x" % (int(found.short_addr) & 0xFFFF))

    def _toggle_once(self):
        if self.target is None:
            return
        now_ms = time.ticks_ms()
        if time.ticks_diff(now_ms, int(self.next_toggle_ms)) < 0:
            return

        self.toggle_state = not self.toggle_state
        try:
            endpoint = self.target.switch(1)
            if self.toggle_state:
                endpoint.on()
            else:
                endpoint.off()
            self.toggle_count += 1
            self._log(
                "toggle_sent count=%d state=%s short=0x%04x"
                % (
                    int(self.toggle_count),
                    "ON" if self.toggle_state else "OFF",
                    int(self.target.short_addr) & 0xFFFF,
                )
            )
        except Exception as exc:
            self.error_count += 1
            self._log("toggle_error count=%d err=%s" % (int(self.error_count), exc))

        self.next_toggle_ms = time.ticks_add(now_ms, TOGGLE_PERIOD_MS)

    def run(self):
        self.coordinator.on_signal(self._signal_cb)
        self.coordinator.on_device_added(self._device_added_cb)
        self.coordinator.on_device_updated(self._device_updated_cb)
        self.coordinator.start(form_network=True)
        self._log("coordinator_started")

        self.target = self.coordinator.wait_for_device(
            feature="on_off",
            timeout_ms=90000,
            poll_ms=120,
            process_batch=6,
            permit_join_s=255,
            auto_discover=True,
            default=None,
        )
        if self.target is None:
            self._log("TEST_FAIL timeout waiting_for_target")
            return
        self.next_toggle_ms = time.ticks_add(time.ticks_ms(), 1000)
        self._log("target_ready short=0x%04x" % (int(self.target.short_addr) & 0xFFFF))

        while True:
            self.coordinator.process_pending_discovery(max_items=4)
            self._toggle_once()

            if self.toggle_count >= TARGET_TOGGLES and self.error_count == 0 and self.target is not None:
                self._log(
                    "TEST_PASS toggles=%d short=0x%04x"
                    % (int(self.toggle_count), int(self.target.short_addr) & 0xFFFF)
                )
                return

            elapsed_ms = time.ticks_diff(time.ticks_ms(), int(self.start_ms))
            if elapsed_ms > MAX_RUNTIME_S * 1000:
                self._log(
                    "TEST_FAIL timeout toggles=%d errors=%d target=%s"
                    % (
                        int(self.toggle_count),
                        int(self.error_count),
                        "none" if self.target is None else ("0x%04x" % (int(self.target.short_addr) & 0xFFFF)),
                    )
                )
                return

            time.sleep_ms(50)


App().run()
