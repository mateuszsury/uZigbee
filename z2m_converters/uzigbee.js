"use strict";

const m = require("zigbee-herdsman-converters/lib/modernExtend");

const definitions = [
  {
    zigbeeModel: ["uzb_Light"],
    model: "uzb_Light",
    vendor: "uzigbee",
    description: "MicroPython ZigBee On/Off Light",
    extend: [m.onOff(), m.identify()],
  },
  {
    zigbeeModel: ["uzb_DimmableLight"],
    model: "uzb_DimmableLight",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Dimmable Light",
    extend: [m.light()],
  },
  {
    zigbeeModel: ["uzb_ColorLight"],
    model: "uzb_ColorLight",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Color Light",
    extend: [m.light({ colorTemp: { range: [153, 500] }, color: { modes: ["xy", "hs"], applyRedFix: false } })],
  },
  {
    zigbeeModel: ["uzb_Switch"],
    model: "uzb_Switch",
    vendor: "uzigbee",
    description: "MicroPython ZigBee On/Off Switch Controller",
    extend: [m.commandsOnOff()],
  },
  {
    zigbeeModel: ["uzb_DimmableSwitch"],
    model: "uzb_DimmableSwitch",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Dimmable Switch Controller",
    extend: [m.commandsOnOff(), m.commandsLevelCtrl()],
  },
  {
    zigbeeModel: ["uzb_PowerOutlet"],
    model: "uzb_PowerOutlet",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Smart Plug",
    extend: [m.onOff(), m.electricityMeter()],
  },
  {
    zigbeeModel: ["uzb_TemperatureSensor"],
    model: "uzb_TemperatureSensor",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Temperature Sensor",
    extend: [m.temperature()],
  },
  {
    zigbeeModel: ["uzb_HumiditySensor"],
    model: "uzb_HumiditySensor",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Humidity Sensor",
    extend: [m.humidity()],
  },
  {
    zigbeeModel: ["uzb_PressureSensor"],
    model: "uzb_PressureSensor",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Pressure Sensor",
    extend: [m.pressure()],
  },
  {
    zigbeeModel: ["uzb_ClimateSensor"],
    model: "uzb_ClimateSensor",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Climate Sensor (Temperature, Humidity, Pressure)",
    extend: [m.temperature(), m.humidity(), m.pressure()],
  },
  {
    zigbeeModel: ["uzb_DoorLock"],
    model: "uzb_DoorLock",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Door Lock",
    extend: [m.lock({ pinCodeCount: 30 })],
  },
  {
    zigbeeModel: ["uzb_DoorLockController"],
    model: "uzb_DoorLockController",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Door Lock Controller (command source)",
    extend: [m.identify()],
  },
  {
    zigbeeModel: ["uzb_Thermostat"],
    model: "uzb_Thermostat",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Thermostat",
    extend: [
      m.thermostat({
        setpoints: { values: { occupiedHeatingSetpoint: { min: 5, max: 30, step: 0.5 } } },
        systemMode: { values: ["off", "heat"] },
      }),
    ],
  },
  {
    zigbeeModel: ["uzb_OccupancySensor"],
    model: "uzb_OccupancySensor",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Occupancy Sensor",
    extend: [m.occupancy()],
  },
  {
    zigbeeModel: ["uzb_IASZone"],
    model: "uzb_IASZone",
    vendor: "uzigbee",
    description: "MicroPython ZigBee IAS Zone (generic)",
    extend: [m.iasZoneAlarm({ zoneType: "generic", zoneAttributes: ["alarm_1", "alarm_2", "tamper", "battery_low"] })],
  },
  {
    zigbeeModel: ["uzb_ContactSensor"],
    model: "uzb_ContactSensor",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Contact Sensor",
    extend: [m.iasZoneAlarm({ zoneType: "contact", zoneAttributes: ["alarm_1", "tamper", "battery_low"] })],
  },
  {
    zigbeeModel: ["uzb_MotionSensor"],
    model: "uzb_MotionSensor",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Motion Sensor",
    extend: [m.iasZoneAlarm({ zoneType: "occupancy", zoneAttributes: ["alarm_1", "tamper", "battery_low"] })],
  },
  {
    zigbeeModel: ["uzb_WindowCovering"],
    model: "uzb_WindowCovering",
    vendor: "uzigbee",
    description: "MicroPython ZigBee Window Covering",
    extend: [m.windowCovering({ controls: ["lift", "tilt"] })],
  },
];

module.exports = definitions;
