# uzigbee

MicroPython Zigbee library for ESP32-C6, built on ESP-Zigbee-SDK (ZBOSS), with:
- native C bridge for MicroPython
- high-level Coordinator / Router / EndDevice APIs
- Zigbee2MQTT and Home Assistant integration workflows

## Project Goals

- Keep a single, practical API surface for Zigbee device development in MicroPython.
- Provide production-focused tooling for build, flash, hardware-in-the-loop (HIL), and CI artifacts.
- Stay RAM-aware for ESP32-C6 constraints (512 KB SRAM, no PSRAM).

## Current Scope

- Pinned toolchain:
  - ESP-IDF `v5.3.2`
  - MicroPython `v1.27.0`
- Runtime roles:
  - Coordinator
  - Router
  - EndDevice
- High-level automation:
  - auto commissioning (`auto` / `guided` / `fixed`)
  - discovery, endpoint/capability mapping, lifecycle/state cache
  - reporting and binding helpers

## Documentation

- Main docs index: `docs/index.md`
- Getting started: `docs/GETTING_STARTED.md`
- Build and flash: `docs/BUILD.md`
- API reference: `docs/API.md`
- Usage examples: `docs/EXAMPLES.md`
- Zigbee2MQTT guide: `docs/Z2M_GUIDE.md`
- Home Assistant integration: `docs/HA_INTEGRATION.md`
- Memory constraints: `docs/MEMORY.md`
- Licensing notes for Zigbee binaries: `docs/LICENSE_NOTES.md`

## Quick Start

1. Bootstrap pinned dependencies in WSL:
   - `bash tools/bootstrap_third_party.sh`
2. Build firmware in WSL (fast incremental path):
   - `./build_firmware.sh --profile esp32-c6-devkit --skip-mpy-cross`
3. Flash from Windows (use offsets from `<build_dir>/flash_args`).
4. Run host smoke tests:
   - `python -m pytest tests/test_import.py tests/test_network_api.py -q`
5. Run HIL smoke tests:
   - `python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_basic_identity_smoke.py --retries 3`

Full commands and variants are in `docs/BUILD.md` and `docs/EXAMPLES.md`.

## Repository Layout

- `c_module/` native MicroPython C bridge and Zigbee integration
- `python/uzigbee/` Python API (core + high-level orchestration)
- `firmware/` manifests, sdkconfig defaults, partitions, board profiles
- `examples/` runnable device and coordinator examples
- `tests/` host and HIL tests
- `tools/` build/flash/test runners and utilities
- `docs/` full project documentation

## Development

- Contribution guide: `CONTRIBUTING.md`
- Security policy: `SECURITY.md`
- Changelog: `CHANGELOG.md`
- Code of conduct: `CODE_OF_CONDUCT.md`

## License

Project source code is licensed under the MIT License. See `LICENSE`.

Important:
- Zigbee binary dependencies (for example `esp-zboss-lib`) have separate redistribution terms.
- Review `docs/LICENSE_NOTES.md` before publishing firmware binaries.
