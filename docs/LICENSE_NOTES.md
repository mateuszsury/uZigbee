# License Notes

## Source Code License

Project source code in this repository is released under the MIT License (see `LICENSE`).

## Third-Party Components

The firmware build uses external components with their own licenses and redistribution terms.

- MicroPython: MIT License
- ESP-IDF: Apache-2.0 (plus component-specific notices)
- `esp-zigbee-lib`: Apache-2.0
- `esp-zboss-lib`: proprietary Espressif/DSR distribution terms

## Important Redistribution Constraint

`esp-zboss-lib` is not open source and has separate licensing terms. Before publishing binary firmware images, verify that your distribution model complies with the current `esp-zboss-lib` license.

## Practical Guidance

- Safe: publish your own `uzigbee` source code and build scripts.
- Conditional: publish firmware binaries only after license compliance check for bundled Zigbee stack artifacts.
- Recommended for releases: include a short third-party notice and exact component versions used to build artifacts.
