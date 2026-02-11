# Progress 2026-02-06 Step 1

Scope:
- First end-to-end firmware build for `ESP32_GENERIC_C6` with uzigbee C module and frozen Python package.
- Flash and basic runtime smoke test on hardware (`COM5`).

What was done:
- Fixed Zigbee GP link failure by forcing linker symbol pull-in in:
  - `third_party/micropython-esp32/ports/esp32/esp32_common.cmake`
  - Added `-Wl,--undefined=zb_zcl_green_power_cluster_handler` for `CONFIG_ZB_ENABLED && CONFIG_ZB_ZCZR && CONFIG_ZB_GP_ENABLED`.
- Set GP explicitly in defaults:
  - `firmware/sdkconfig.defaults`: `CONFIG_ZB_GP_ENABLED=y`
- Ensured build uses project partition layout:
  - `firmware/sdkconfig.defaults`: `CONFIG_PARTITION_TABLE_CUSTOM_FILENAME="../../../../firmware/partitions.csv"`
- Increased app partition for current firmware size:
  - `firmware/partitions.csv`: factory partition `0x200000 -> 0x210000`
- Fixed corrupted MicroPython helper script that blocked final image merge:
  - `third_party/micropython-esp32/ports/esp32/makeimg.py`

Build result:
- `micropython.bin` generated successfully.
- Final size check:
  - app size: `0x201ae0`
  - app partition: `0x210000`
  - free: `0xe520` (~3%)

Flash result (`COM5`):
- `bootloader.bin`, `partition-table.bin`, `micropython.bin` written successfully via `esptool`.

Smoke tests (device):
- `mpremote connect COM5 resume exec "import _uzigbee"`: OK
- `mpremote connect COM5 resume exec "import uzigbee"`: OK
- `mpremote connect COM5 soft-reset exec "import uzigbee; z=uzigbee.ZigbeeStack(); z.init(uzigbee.ROLE_COORDINATOR); z.start(form_network=False)"`: OK
- `permit_join(30)` currently returns `OSError: -1` (expected for current early stack state / no formed network context).

Notes:
- Keep isolated WSL environment (`tools/wsl-env.sh`) to avoid cross-project ESP-IDF conflicts.
- Do not share `build-*` directories between parallel agents.
