# Getting Started

This guide gets `uzigbee` running on ESP32-C6 in the fastest reproducible path.

## 1. Prerequisites

- Windows host with Python and `mpremote` / `esptool`.
- WSL (Ubuntu recommended) for firmware build.
- Two ESP32-C6 boards for coordinator/router end-to-end tests (optional, but recommended).

## 2. Bootstrap Dependencies (WSL)

From repo root:

```bash
bash tools/bootstrap_third_party.sh
```

This installs pinned sources:
- `ESP-IDF v5.3.2` into `third_party/esp-idf`
- `MicroPython v1.27.0` into `third_party/micropython-esp32`

Then it applies required `uzigbee` vendor overrides from `firmware/vendor_overrides/`.

## 3. Build Firmware (WSL)

```bash
./build_firmware.sh --profile esp32-c6-devkit --skip-mpy-cross
```

For first build (or after submodule refresh):

```bash
./build_firmware.sh --profile esp32-c6-devkit --force-mpy-cross --submodules
```

## 4. Flash Firmware (Windows)

1. Open generated `flash_args` from build directory.
2. Flash with `esptool` (or your existing flash helper).

Example:

```powershell
python -m esptool --chip esp32c6 --port COM5 --baud 460800 write-flash @<build_dir>\flash_args
```

## 5. Sanity Check on Device

```powershell
python -m mpremote connect COM5 resume exec "import _uzigbee,uzigbee; print(_uzigbee.__name__, uzigbee.__name__)"
```

## 6. Host Tests

```powershell
python -m pytest tests/test_import.py tests/test_network_api.py -q
```

## 7. HIL Smoke (optional, recommended)

```powershell
python tools/hil_runner.py --ports COM3 COM5 --tests tests/hil_basic_identity_smoke.py --retries 3
```

## 8. Next Steps

- API usage examples: `docs/EXAMPLES.md`
- Full API reference: `docs/API.md`
- Zigbee2MQTT workflow: `docs/Z2M_GUIDE.md`
