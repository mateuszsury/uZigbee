# uzigbee external converters for Zigbee2MQTT

Files:
- `uzigbee.js`: definitions for all built-in `uzigbee` high-level devices.
- `uzigbee_custom_template.js`: starting template for custom model IDs.

## Install (Zigbee2MQTT 2.x)

1. Copy converter file(s) to your Zigbee2MQTT data directory, e.g.:
   - `<zigbee2mqtt-data>/external_converters/uzigbee.js`
2. In Zigbee2MQTT `configuration.yaml` add:

```yaml
external_converters:
  - uzigbee.js
```

3. Restart Zigbee2MQTT.
4. Re-interview or re-pair the device if needed.

## Verify converter is loaded

- In Zigbee2MQTT logs, confirm no external converter load errors.
- Device should not stay in `unsupported` state when model matches one of `uzb_*` models defined in `uzigbee.js`.

## Custom models

1. Copy `uzigbee_custom_template.js` and rename it, e.g. `uzigbee_my_device.js`.
2. Replace `zigbeeModel` and `model` with your Basic cluster `model_identifier`.
3. Adjust `extend` according to clusters exposed by your device.
4. Add this new converter file to `external_converters` and restart Zigbee2MQTT.

## Supported built-in models

- `uzb_Light`
- `uzb_DimmableLight`
- `uzb_ColorLight`
- `uzb_Switch`
- `uzb_DimmableSwitch`
- `uzb_PowerOutlet`
- `uzb_TemperatureSensor`
- `uzb_HumiditySensor`
- `uzb_PressureSensor`
- `uzb_ClimateSensor`
- `uzb_DoorLock`
- `uzb_DoorLockController`
- `uzb_Thermostat`
- `uzb_OccupancySensor`
- `uzb_IASZone`
- `uzb_ContactSensor`
- `uzb_MotionSensor`
- `uzb_WindowCovering`
