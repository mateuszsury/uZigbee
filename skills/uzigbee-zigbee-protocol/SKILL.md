# Skill: uzigbee-zigbee-protocol

Purpose: Implement Zigbee protocol features (ZCL/ZDO, binding, reporting, security, OTA).

Use when:
- Adding cluster commands or attributes
- Implementing ZDO requests or commissioning
- Working on binding tables, groups/scenes, OTA, security

Rules:
- Time-critical responses should be handled in C where possible.
- Python receives notifications, not latency-critical duties.
- Follow Zigbee Cluster Library (ZCL) data types and endian rules.

Scope checklist:
- ZCL command send/receive helpers
- Attribute reporting configuration
- Binding / unbinding
- Groups and scenes
- ZDO discovery and descriptor requests
- Install codes, network key handling
- OTA server/client flows
- Touchlink and Green Power (if enabled)

Integration points:
- c_module/uzb_zcl.c
- c_module/uzb_zdo.c
- python/uzigbee/zcl.py
- python/uzigbee/reporting.py
- python/uzigbee/groups.py
- python/uzigbee/scenes.py
- python/uzigbee/ota.py

Caution:
- Validate cluster IDs and attribute IDs.
- Ensure callbacks are scheduled into MicroPython, not called inline.
