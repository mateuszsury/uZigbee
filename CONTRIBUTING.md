# Contributing to uZigbee

Thank you for your interest in contributing! This guide will help you get started.

## Architecture Overview

uZigbee is structured as a layered system:

```
ESP32-C6 Hardware → C Bridge (ESP-Zigbee-SDK) → MicroPython API → Zigbee Network
```

- **`c_module/`** — Native C bridge between MicroPython and ESP-Zigbee-SDK (ZBOSS)
- **`python/uzigbee/`** — High-level Python API (Coordinator, Router, EndDevice)
- **`firmware/`** — Build profiles, partitions, sdkconfig
- **`tests/`** — Host tests and hardware-in-the-loop (HIL) tests
- **`tools/`** — Build, flash, and test runner utilities

For a visual overview, see the [architecture diagram](assets/architecture.svg).

## Scope & Constraints

This project targets MicroPython + Zigbee on ESP32-C6 with strict constraints:

| Constraint | Value |
|---|---|
| ESP-IDF | `v5.3.2` |
| MicroPython | `v1.27.0` |
| RAM | 512 KB SRAM, **no PSRAM** |
| Safety | Zigbee operations must be lock-safe and task-safe |

## Getting Started

### 1. Clone and bootstrap

```bash
git clone https://github.com/mateuszsury/uZigbee.git
cd uZigbee
bash tools/bootstrap_third_party.sh   # WSL / Linux
```

### 2. Build firmware

```bash
./build_firmware.sh --profile esp32-c6-devkit --skip-mpy-cross
```

### 3. Run host tests

```bash
python -m pytest tests/test_import.py tests/test_network_api.py -q
```

See [BUILD.md](docs/BUILD.md) for full build options and [EXAMPLES.md](docs/EXAMPLES.md) for usage.

## Development Workflow

1. Create a feature branch from `main`.
2. Keep changes focused and incremental.
3. Update docs for any API or behavior change.
4. Run host tests before opening a PR.
5. Include HIL test results for runtime/bridge changes.

## Code Guidelines

- **Explicit over magic** — prefer clear APIs over hidden behavior.
- **Defensive C bridge** — validate arguments, return clear errors.
- **Minimize allocations** — avoid Python allocations in hot paths.
- **Callback safety** — Zigbee callbacks must be scheduler-safe.
- **Memory awareness** — keep RAM pressure visible in design decisions.

## Testing Expectations

| Change Type | Required Testing |
|---|---|
| Python API changes | Host tests for changed APIs |
| C bridge / runtime changes | Host tests + at least one HIL smoke on hardware |
| Behavior changes | Add or update tests in `tests/` |

## Good First Issues

Look for issues labeled [`good first issue`](https://github.com/mateuszsury/uZigbee/labels/good%20first%20issue) to find beginner-friendly tasks. These typically involve:

- Documentation improvements
- Adding test coverage for existing APIs
- Small Python-layer enhancements

## Commit and PR Style

- Use descriptive commit messages with affected area prefix (e.g., `network:`, `node:`, `c_module:`, `docs:`).
- Document risk and rollback notes for low-level changes.
- Fill out the PR template completely.

## Licensing

By contributing, you agree your contributions are licensed under the project [MIT License](LICENSE).

> **Note:** Zigbee binary dependencies (e.g., `esp-zboss-lib`) have separate redistribution terms. See [LICENSE_NOTES.md](docs/LICENSE_NOTES.md) for details.
