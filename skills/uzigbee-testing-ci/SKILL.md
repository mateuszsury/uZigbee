# Skill: uzigbee-testing-ci

Purpose: Add tests and CI coverage for firmware, Python API, and integration.

Use when:
- Adding tests under tests/
- Setting up CI or hardware-in-the-loop workflows
- Creating release binaries

Test layers:
- Python unit tests (ZCL constants, core classes, devices)
- C unit or component tests where feasible
- Integration tests with real Zigbee devices (two-node minimum)

CI workflow ideas:
- Build firmware for each board config
- Produce binaries as artifacts
- Run Python unit tests (host-side)
- Optional HIL jobs with tagged runners

Keep in mind:
- Many features need real hardware; document manual steps.
- Provide minimal example scripts to verify basic join and on/off.
