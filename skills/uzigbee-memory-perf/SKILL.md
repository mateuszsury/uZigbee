# Skill: uzigbee-memory-perf

Purpose: Keep RAM/flash usage within ESP32-C6 limits.

Use when:
- OOM occurs, stack overflows, or performance regressions
- Changing sdkconfig, partition table, or enabling features

Checklist:
- Disable WiFi unless gateway mode is required.
- Freeze Python modules to flash.
- Reduce logging: CONFIG_LOG_DEFAULT_LEVEL_WARN or lower.
- Tune stack sizes for Zigbee and MicroPython tasks.
- Use size optimization: CONFIG_COMPILER_OPTIMIZATION_SIZE.
- Keep ring buffers small and static.
- Consider ZED-only builds for end devices.
- Use gc.threshold() and schedule gc.collect() at safe times.

Metrics to track:
- heap_caps_get_free_size(MALLOC_CAP_8BIT)
- MicroPython gc.mem_free()
- Firmware size vs partition
