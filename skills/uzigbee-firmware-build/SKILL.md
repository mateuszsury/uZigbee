# Skill: uzigbee-firmware-build

Purpose: Manage ESP-IDF/MicroPython build integration for ESP32-C6 firmware.

Use when:
- Editing firmware build scripts (firmware/), sdkconfig.defaults, partitions.csv
- Changing boards/ configs or USER_C_MODULES/FROZEN_MANIFEST wiring
- Adding esp-zigbee-lib / esp-zboss-lib deps or build flags

Workflow:
1. Confirm target board and role.
   - Coordinator/router/end-device affects Zigbee config and RAM.
2. Pin toolchain versions.
   - ESP-IDF v5.3.2
   - MicroPython v1.27.0
3. Wire Zigbee deps.
   - Add esp-zigbee-lib and esp-zboss-lib to idf_component.yml (ESP32 port).
4. Update config files:
   - firmware/sdkconfig.defaults
   - firmware/partitions.csv
   - firmware/boards/<BOARD> as needed
5. Build steps:
   - make -C mpy-cross
   - make BOARD=<BOARD> USER_C_MODULES=<path>/c_module/micropython.cmake FROZEN_MANIFEST=<path>/firmware/manifest.py
6. Flash / monitor:
   - tools/flash.sh and tools/monitor.sh (if present)

Checklist:
- Partition table fits firmware size.
- Zigbee role config matches target (ZC/ZR/ZED).
- WiFi disabled unless required.
- Optimization flags set for size.
- Stack sizes tuned for Zigbee + MicroPython.

Artifacts:
- Firmware binary
- Map or size report for RAM/flash sanity
