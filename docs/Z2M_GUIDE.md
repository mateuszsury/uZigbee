# uzigbee + Zigbee2MQTT Guide

This guide focuses on the fastest path from flash to stable Zigbee2MQTT (Z2M)
integration for uzigbee firmware.

## 1) Quick Start (5 minutes)

1. Build firmware (WSL):
   - `./build_firmware.sh --profile esp32-c6-devkit --skip-mpy-cross`
2. Flash from Windows (example `COM3`):
   - `python -m esptool --chip esp32c6 --port COM3 --baud 460800 write-flash @third_party/micropython-esp32/ports/esp32/build-ESP32_GENERIC_C6-uzigbee/flash_args`
3. Start coordinator demo:
   - `python -m mpremote connect COM3 run examples/coordinator_web_demo.py`
4. Enable pairing from UI (`permit_join`) and pair target device.
5. Install external converter:
   - copy `z2m_converters/uzigbee.js` into Z2M `external_converters/`
   - add to Z2M `configuration.yaml`:

```yaml
external_converters:
  - uzigbee.js
```

6. Restart Zigbee2MQTT, then re-interview or re-pair if required.

## 2) Troubleshooting Interview Failures

Most frequent causes and fixes:

1. Device remains `unsupported` in Z2M:
   - verify `external_converters: - uzigbee.js` is loaded.
   - confirm model exists in converter:
     - `uzb_Light`, `uzb_DimmableLight`, `uzb_ColorLight`, `uzb_Switch`,
       `uzb_DimmableSwitch`, `uzb_PowerOutlet`, `uzb_TemperatureSensor`,
       `uzb_HumiditySensor`, `uzb_PressureSensor`, `uzb_ClimateSensor`,
       `uzb_DoorLock`, `uzb_DoorLockController`, `uzb_Thermostat`,
       `uzb_OccupancySensor`, `uzb_IASZone`, `uzb_ContactSensor`,
       `uzb_MotionSensor`, `uzb_WindowCovering`.
2. Partial interview (missing exposes):
   - keep device awake during interview.
   - re-run interview after restart of Z2M and coordinator.
   - verify endpoint/cluster provisioning from device role API.
3. Join succeeds but commands do not work:
   - validate target short address in coordinator logs.
   - validate endpoint used by command matches discovered endpoint.
4. Flaky serial/HIL runs on COM ports:
   - use resilient runner:
     - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_z2m_validate_smoke.py tests/hil_z2m_setters_smoke.py --retries 4 --timeout 180`

## 3) Add Custom Device to Z2M

When your uzigbee device has a new `model_identifier`:

1. Choose final model string exposed by Basic cluster, for example
   `uzb_CustomWeatherStation`.
2. Add converter definition in `z2m_converters/uzigbee.js` or separate file.
3. Map `fromZigbee`/`toZigbee`/`exposes` to your clusters and commands.
4. Restart Z2M and run re-interview.
5. Validate end-to-end using your HIL smoke scripts.

## 4) Create External Converter from Template

1. Copy template:
   - `z2m_converters/uzigbee_custom_template.js`
2. Rename, for example:
   - `uzigbee_my_device.js`
3. Set:
   - `zigbeeModel`
   - `model`
   - `vendor`
   - `description`
4. Add proper extend/exposes for your device type.
5. Register file in Z2M `configuration.yaml` under `external_converters`.

## 5) Validate Full Matrix (Automation)

Run interview-oriented suite:

- dry run (metadata + converter coverage only):
  - `python tools/z2m_interview_suite.py --skip-hil --report-json docs/z2m_interview_report_dryrun.json`
- full HIL run:
  - `python tools/z2m_interview_suite.py --ports COM3 COM5 --retries 4 --timeout 180 --report-json docs/z2m_interview_report.json`
- HA discovery contract validation:
  - `python tools/ha_discovery_suite.py --converter z2m_converters/uzigbee.js --report-json docs/ha_discovery_report.json --strict-extends`

## 6) Current Scope and Limits

1. Unified firmware image: coordinator/router/end-device role is runtime
   selected, not separate firmware variants.
2. Board profiles currently map supported ESP32-C6 boards to
   `ESP32_GENERIC_C6` build target:
   - `esp32-c6-devkit`
   - `xiao-esp32c6`
   - `firebeetle-esp32c6`
3. Upstream `zigbee-herdsman-converters` PR is tracked as a separate plan item.
