# Board Profiles

This directory defines hardware profiles consumed by `build_firmware.sh`.

Each profile is a small `.env` file with the following keys:
- `PROFILE_ID`
- `PROFILE_DESCRIPTION`
- `PROFILE_BOARD`
- `PROFILE_SDKCONFIG_DEFAULTS`

The profile does not create a separate firmware flavor. It only selects build
defaults (board target and sdkconfig defaults path) for one shared uzigbee
firmware image.

Supported profile IDs:
- `esp32-c6-devkit`
- `xiao-esp32c6`
- `firebeetle-esp32c6`

Usage examples:
- `./build_firmware.sh --list-profiles`
- `./build_firmware.sh --profile xiao-esp32c6 --skip-mpy-cross`
