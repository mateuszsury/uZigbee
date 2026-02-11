# Build

Pinned toolchain (non-negotiable):
- ESP-IDF `v5.3.2`
- MicroPython `v1.27.0`

## 1. Bootstrap (WSL)

```bash
bash tools/bootstrap_third_party.sh
```

This prepares:
- `third_party/esp-idf`
- `third_party/micropython-esp32`
- vendor override sync from `firmware/vendor_overrides/`

## 2. Build Firmware

Default incremental build:

```bash
./build_firmware.sh --profile esp32-c6-devkit --skip-mpy-cross
```

First build / full refresh:

```bash
./build_firmware.sh --profile esp32-c6-devkit --force-mpy-cross --submodules
```

Clean rebuild in selected build dir:

```bash
./build_firmware.sh --profile esp32-c6-devkit --build build-ESP32_GENERIC_C6-uzigbee-clean --clean --force-mpy-cross
```

## 3. Board Profiles

List profiles:

```bash
./build_firmware.sh --list-profiles
```

Examples:

```bash
./build_firmware.sh --profile esp32-c6-devkit --skip-mpy-cross
./build_firmware.sh --profile xiao-esp32c6 --skip-mpy-cross
./build_firmware.sh --profile firebeetle-esp32c6 --skip-mpy-cross
```

## 4. Flash (Windows)

Use generated `flash_args` file from build directory.

Example:

```powershell
python -m esptool --chip esp32c6 --port COM5 --baud 460800 write-flash @<build_dir>\flash_args
```

## 5. Verify Firmware

```powershell
python -m mpremote connect COM5 resume exec "import _uzigbee,uzigbee; print(_uzigbee.__name__, uzigbee.__name__)"
```

## 6. CI Artifacts

- Workflow template (needs `workflow` token scope when enabling): `.github/workflows-disabled/firmware-artifacts.yml`
- Local packager:

```bash
bash tools/package_firmware_artifacts.sh <build_dir> [output_dir]
```

## 7. Notes

- Single universal firmware image; role is runtime-selected by API (`Coordinator` / `Router` / `EndDevice`).
- Build script has lock protection for parallel-agent environments.
- Partition layout includes explicit `vfs` partition (`firmware/partitions.csv`).
