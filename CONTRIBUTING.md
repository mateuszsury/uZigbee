# Contributing

## Scope

This project targets MicroPython + Zigbee on ESP32-C6 with strict constraints:
- ESP-IDF `v5.3.2`
- MicroPython `v1.27.0`
- Zigbee operations must remain lock-safe and task-safe

## Development Workflow

1. Create a feature branch.
2. Keep changes focused and incremental.
3. Update docs for any API or behavior change.
4. Run host tests before opening a PR.

## Local Setup

1. Bootstrap vendor dependencies in WSL:
   - `bash tools/bootstrap_third_party.sh`
2. Build firmware:
   - `./build_firmware.sh --profile esp32-c6-devkit --skip-mpy-cross`
3. Run host tests:
   - `python -m pytest tests/test_import.py tests/test_network_api.py -q`

## Code Guidelines

- Prefer explicit APIs over hidden magic.
- Keep C bridge defensive: validate arguments, return clear errors.
- Avoid Python allocations in hot paths.
- Preserve callback safety: Zigbee callbacks must be scheduler-safe.
- Keep memory pressure visible in design decisions (ESP32-C6 has no PSRAM).

## Testing Expectations

- Required: host tests for changed Python APIs.
- Required for runtime/bridge changes: at least one HIL smoke on hardware.
- Recommended for behavior changes: add or update tests in `tests/`.

## Commit and PR Style

- Use descriptive commit messages.
- Include affected area in summary (e.g., `network`, `node`, `c_module`, `docs`).
- Document risk and rollback notes for low-level changes.

## Licensing

By contributing, you agree your contributions are licensed under the project MIT License.
See `docs/LICENSE_NOTES.md` for third-party Zigbee binary constraints.
