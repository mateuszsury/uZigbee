# AGENTS.md

<INSTRUCTIONS>
## Project Summary
- MicroPython ZigBee library for ESP32-C6 built on ESP-Zigbee-SDK (ZBOSS).
- Requires custom MicroPython firmware with a C module bridge.
- Python API provides core primitives and high-level HA devices.

## Non-Negotiables
- ESP-IDF v5.3.2 (pinned).
- MicroPython v1.27.0 (pinned).
- Zigbee stack must run in a dedicated FreeRTOS task; all Zigbee API calls must hold the Zigbee lock.
- Zigbee -> Python callbacks must be scheduled onto the MicroPython scheduler (no Python allocation in Zigbee task).
- ESP32-C6 has 512 KB SRAM, no PSRAM. Treat RAM as critical.
- Frozen modules are the default for the Python layer.

## Planned Repo Layout
- firmware/ : build scripts, sdkconfig.defaults, partitions.csv, boards/
- c_module/ : C bridge and event queue
- python/uzigbee/ : Python API and devices
- docs/ : documentation
- tests/ : unit + integration tests
- tools/ : flash/monitor helpers

## Build Notes (reference)
- Build uses the MicroPython ESP32 port with USER_C_MODULES and FROZEN_MANIFEST.
- Zigbee deps are esp-zigbee-lib and esp-zboss-lib.
- See skills/uzigbee-firmware-build/SKILL.md for the exact workflow.

## Skills
- uzigbee-firmware-build: ESP-IDF/MicroPython build system, sdkconfig, partitions, board support.
  file: skills/uzigbee-firmware-build/SKILL.md
- uzigbee-c-module: C bridge, Zigbee task, locking, event queue, callbacks.
  file: skills/uzigbee-c-module/SKILL.md
- uzigbee-python-api: Python core API, devices, constants, frozen modules.
  file: skills/uzigbee-python-api/SKILL.md
- uzigbee-zigbee-protocol: ZCL/ZDO, reporting, binding, groups/scenes, security, OTA.
  file: skills/uzigbee-zigbee-protocol/SKILL.md
- uzigbee-memory-perf: RAM/flash optimization, GC tuning, profiling.
  file: skills/uzigbee-memory-perf/SKILL.md
- uzigbee-testing-ci: unit tests, integration tests, CI build artifacts.
  file: skills/uzigbee-testing-ci/SKILL.md
- uzigbee-docs-release: docs, examples, release binaries, license checklist.
  file: skills/uzigbee-docs-release/SKILL.md

## Skill Trigger Rules
- If a task matches a skill description or references its area, open and follow that skill.
- If multiple skills apply, use the minimal set and state the order.
- If a skill is missing, say so and continue with the best fallback.

## Style Conventions
- Prefer small, explicit APIs over implicit magic.
- Avoid heavy Python allocations in hot paths.
- Keep C code defensive: validate inputs, return errors clearly.

</INSTRUCTIONS>
