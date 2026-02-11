# Home Assistant Integration (via Zigbee2MQTT)

Status for current test run (`2026-02-10`):
- Z2M HIL matrix: `22/22 PASS` (`docs/z2m_interview_report.json`)
- HA discovery contract suite: `18/18 PASS` (`docs/ha_discovery_report.json`)

## Scope

This integration path validates Home Assistant compatibility through:
1. Zigbee2MQTT interview and converter coverage for all built-in uzigbee models.
2. Discovery-domain compatibility for HA entities.
3. Device class and unit mapping checks (`°C`, `%`, `hPa`, `W`, `V`, `A`) from converter capabilities.
4. Device reaction path validated by HIL control tests (on device, COM3).

## Commands Used

1. Full Zigbee2MQTT interview-oriented HIL suite:
   - `python tools/z2m_interview_suite.py --ports COM3 --retries 3 --timeout 180 --report-json docs/z2m_interview_report.json`
2. Home Assistant discovery compatibility suite:
   - `python tools/ha_discovery_suite.py --converter z2m_converters/uzigbee.js --report-json docs/ha_discovery_report.json --strict-extends`

## Notes

1. In this run, `COM3` was active and used for HIL; `COM5` was not available.
2. Discovery validation is converter/discovery-contract level and does not require live HA container.
3. External converter remains the supported integration path at this stage (`z2m_converters/uzigbee.js`).
