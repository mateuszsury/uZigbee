"use strict";

const m = require("zigbee-herdsman-converters/lib/modernExtend");

/*
Template for custom uzigbee devices.
Copy this file, change model IDs, and tune extend[] for your endpoint/cluster mix.
*/

const definitions = [
  {
    zigbeeModel: ["uzb_CustomDevice"],
    model: "uzb_CustomDevice",
    vendor: "uzigbee",
    description: "Custom uzigbee device template",
    extend: [
      m.onOff(),
      m.temperature(),
      // Examples:
      // m.humidity(),
      // m.pressure(),
      // m.occupancy(),
      // m.iasZoneAlarm({ zoneType: "generic", zoneAttributes: ["alarm_1"] }),
      // m.windowCovering({ controls: ["lift"] }),
      // m.lock({ pinCodeCount: 30 }),
    ],
  },
];

module.exports = definitions;
