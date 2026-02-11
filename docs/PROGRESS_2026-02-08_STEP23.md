# Progress 2026-02-08 - Step 23

Scope:
- implement next planned HA devices from `plan.md`: `DoorLock`, `DoorLockController`, `Thermostat`, `OccupancySensor`.
- deliver full path: C bridge + Python API + high-level devices + tests + firmware build + flash + HIL.

Implemented:
- C core:
  - `c_module/uzb_core.h`
    - added endpoint creators:
      - `uzb_core_create_door_lock_endpoint`
      - `uzb_core_create_door_lock_controller_endpoint`
      - `uzb_core_create_thermostat_endpoint`
      - `uzb_core_create_occupancy_sensor_endpoint`
    - added command sender:
      - `uzb_core_send_lock_cmd`
  - `c_module/uzb_core.c`
    - new endpoint kinds:
      - `DOOR_LOCK`, `DOOR_LOCK_CONTROLLER`, `THERMOSTAT`, `OCCUPANCY_SENSOR`
    - registration support:
      - `esp_zb_door_lock_ep_create`
      - `esp_zb_door_lock_controller_ep_create`
      - `esp_zb_thermostat_ep_create`
      - custom occupancy endpoint with Occupancy Sensing server cluster
    - lock/unlock command send path:
      - `esp_zb_zcl_lock_door_cmd_req`
      - `esp_zb_zcl_unlock_door_cmd_req`
    - lock discipline preserved for all Zigbee API calls.
- C MicroPython module:
  - `c_module/mod_uzigbee.c`
    - new wrappers:
      - `create_door_lock`
      - `create_door_lock_controller`
      - `create_thermostat`
      - `create_occupancy_sensor`
      - `send_lock_cmd`
    - exported new constants:
      - cluster IDs, attribute IDs, command IDs and device IDs for door lock/thermostat/occupancy.
- Python core API:
  - `python/uzigbee/core.py`
    - constants for:
      - `CLUSTER_ID_DOOR_LOCK`, `CLUSTER_ID_THERMOSTAT`, `CLUSTER_ID_OCCUPANCY_SENSING`
      - `ATTR_DOOR_LOCK_LOCK_STATE`
      - `ATTR_THERMOSTAT_LOCAL_TEMPERATURE`, `ATTR_THERMOSTAT_OCCUPIED_HEATING_SETPOINT`, `ATTR_THERMOSTAT_SYSTEM_MODE`
      - `ATTR_OCCUPANCY_SENSING_OCCUPANCY`
      - `DEVICE_ID_DOOR_LOCK`, `DEVICE_ID_DOOR_LOCK_CONTROLLER`, `DEVICE_ID_THERMOSTAT`, `DEVICE_ID_OCCUPANCY_SENSOR`
      - `CMD_DOOR_LOCK_LOCK_DOOR`, `CMD_DOOR_LOCK_UNLOCK_DOOR`
    - new methods:
      - `create_door_lock`, `create_door_lock_controller`, `create_thermostat`, `create_occupancy_sensor`
      - `send_lock_cmd`
- High-level device layer:
  - `python/uzigbee/devices.py`
    - added classes:
      - `DoorLock`
      - `DoorLockController`
      - `Thermostat`
      - `OccupancySensor`
    - each class includes provisioning path + attribute APIs + callback handling.
  - `python/uzigbee/__init__.py`
    - exported new classes and constants.

Tests:
- Host unit tests:
  - command:
    - `pytest -q tests/test_core_api.py tests/test_devices_api.py tests/test_import.py`
  - result:
    - `28 passed`.
- Added HIL smoke scripts:
  - `tests/hil_zigbee_bridge_addr_smoke.py`
  - `tests/hil_door_lock_smoke.py`
  - `tests/hil_door_lock_controller_smoke.py`
  - `tests/hil_thermostat_smoke.py`
  - `tests/hil_occupancy_sensor_smoke.py`

Firmware build and flash:
- WSL build:
  - `BOARD=ESP32_GENERIC_C6`
  - `BUILD=build-ESP32_GENERIC_C6-uzigbee-step23a`
  - result: PASS
  - `micropython.bin = 0x250bb0`
  - free app partition: `0x19a450` (~41%).
- Flash (Windows):
  - target: `COM3` (ESP32-C6)
  - result: PASS.

HIL on device (`COM3`):
- PASS:
  - `tests/hil_zigbee_bridge_addr_smoke.py`
  - `tests/hil_door_lock_smoke.py`
  - `tests/hil_door_lock_controller_smoke.py`
  - `tests/hil_thermostat_smoke.py`
  - `tests/hil_occupancy_sensor_smoke.py`
- IEEE/short address check via bridge:
  - `ieee = 644c4efeffca4c40`
  - `short = 0x0`
  - values matched between `uzigbee` and `_uzigbee`.

Operational note:
- Batch `mpremote` loops were unstable (raw-REPL entry). Stable sequence used:
  - pulse reset to run-mode,
  - then `python -m mpremote connect COM3 resume soft-reset run <test>`.

Plan updates:
- `plan.md` updated:
  - marked done:
    - `DoorLock`, `DoorLockController`
    - `Thermostat`
    - `OccupancySensor`
  - kept pending:
    - `ContactSensor`, `MotionSensor` (IAS Zone path).
