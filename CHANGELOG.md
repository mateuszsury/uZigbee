# Changelog

All notable changes to this project are documented in this file.

Format is based on Keep a Changelog and semantic versioning principles.

## [Unreleased]

### Added
- High-level Coordinator API with automatic discovery, capability mapping, and state cache.
- High-level Router/EndDevice API with declarative endpoint/capability model.
- Auto/guided/fixed commissioning modes with runtime introspection.
- Dual-node HIL orchestration utilities and stress runner.
- Coordinator web-portal examples for high-level Zigbee control paths.

### Changed
- Build flow standardized around pinned `ESP-IDF v5.3.2` and `MicroPython v1.27.0`.
- Partition layout includes explicit `vfs` partition.
- Documentation upgraded to MkDocs structure with dedicated build/API/integration guides.

### Fixed
- Zigbee + Wi-Fi coexistence integration for coordinator web workflows.
- HTTP response stability in coordinator web portal examples.
- Discovery and control reliability under multi-endpoint/high-frequency scenarios.
