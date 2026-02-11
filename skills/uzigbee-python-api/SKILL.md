# Skill: uzigbee-python-api

Purpose: Build the Python-facing API and high-level device classes.

Use when:
- Editing python/uzigbee/*.py or firmware/manifest.py
- Adding constants, core classes, device models, or helpers

Guidelines:
- Keep API simple for beginners but expose full control for advanced use.
- Use const() for IDs and flags to reduce RAM.
- Prefer frozen modules for core library code.
- Avoid heavy imports; keep module load cheap.

Core modules:
- __init__.py: public API, constants
- core.py: ZigbeeStack, Endpoint, Cluster, Attribute
- zcl.py: cluster IDs, attribute IDs, ZCL types
- devices.py, sensors.py: HA devices and sensors
- reporting.py, groups.py, scenes.py, ota.py, gateway.py

Patterns:
- Singleton ZigbeeStack.
- Endpoint/Cluster composition.
- on(event, handler) for signals and callbacks.
- Provide small convenience wrappers, keep low-level access in _uzigbee.

Testing:
- Add unit tests for ZCL constants, cluster creation, and device models.
