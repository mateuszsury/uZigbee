#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)

SRC_ROOT="${ROOT_DIR}/firmware/vendor_overrides"
TP_ROOT="${ROOT_DIR}/third_party"

if [[ ! -d "${SRC_ROOT}" ]]; then
  echo "[ERROR] Missing overrides directory: ${SRC_ROOT}" >&2
  exit 1
fi

# IDF 5.3's GPTimer driver enables the C6 default PLL clock directly through
# timer_ll_enable_clock; the generic source-enable API was introduced later.
# Keep upstream timer behavior for all other targets/toolchain versions.
python3 - "${TP_ROOT}/micropython-esp32/ports/esp32" <<'PY'
from pathlib import Path
import sys

port = Path(sys.argv[1])
source = port / 'machine_timer.c'
if source.exists():
    text = source.read_text()
    marker = 'UZIGBEE_IDF53_TIMER_COMPAT'
    if marker not in text:
        call = '    esp_clk_tree_enable_src(TIMER_CLK_SRC, true);'
        if text.count(call) != 1:
            raise SystemExit('Unexpected upstream timer source; review the IDF compatibility patch')
        replacement = '''    // UZIGBEE_IDF53_TIMER_COMPAT: C6 PLL clock uses timer_ll_enable_clock below.
    #if !(CONFIG_IDF_TARGET_ESP32C6 && ESP_IDF_VERSION < ESP_IDF_VERSION_VAL(5, 4, 0))
    esp_clk_tree_enable_src(TIMER_CLK_SRC, true);
    #endif'''
        source.write_text(text.replace(call, replacement))

# Upstream's Makefile ignores SDKCONFIG_DEFAULTS and its board CMake replaces
# command-line defaults. Append our profile after board selection, before the
# combined defaults file is written, so Zigbee and our partitions are enabled.
cmake = port / 'CMakeLists.txt'
if cmake.exists():
    text = cmake.read_text()
    marker = '# UZIGBEE_PROFILE_DEFAULTS'
    if marker not in text:
        anchor = '# Concatenate all sdkconfig files into a combined one for the IDF to use.'
        if text.count(anchor) != 1:
            raise SystemExit('Unexpected upstream CMake source; review profile defaults wiring')
        addition = '''# UZIGBEE_PROFILE_DEFAULTS
if(DEFINED ENV{UZIGBEE_SDKCONFIG_DEFAULTS})
    list(APPEND SDKCONFIG_DEFAULTS "$ENV{UZIGBEE_SDKCONFIG_DEFAULTS}")
endif()

'''
        cmake.write_text(text.replace(anchor, addition + anchor))
PY

copy_file() {
  local src="$1"
  local dst="$2"
  local dst_dir
  dst_dir="$(dirname "${dst}")"
  mkdir -p "${dst_dir}"
  cp -f "${src}" "${dst}"
  echo "[OK] override: ${dst#${ROOT_DIR}/}"
}

while IFS= read -r -d '' src_file; do
  rel="${src_file#${SRC_ROOT}/}"
  case "${rel}" in
    micropython-esp32/*)
      copy_file "${src_file}" "${TP_ROOT}/${rel}"
      ;;
    *)
      echo "[WARN] Unknown override namespace, skipping: ${rel}" >&2
      ;;
  esac
done < <(find "${SRC_ROOT}" -type f -print0)

# MicroPython 1.27 enables I2C target on C6 by default, but its target driver
# requires newer ESP-IDF slave callbacks than the pinned v5.3.2 provides.
# Preserve the upstream board configuration and disable only that unsupported API.
BOARD_HEADER="${TP_ROOT}/micropython-esp32/ports/esp32/boards/ESP32_GENERIC_C6/mpconfigboard.h"
if [[ -f "${BOARD_HEADER}" ]] && ! grep -q 'UZIGBEE_IDF53_I2C_TARGET_COMPAT' "${BOARD_HEADER}"; then
  cat >> "${BOARD_HEADER}" <<'EOF'

// UZIGBEE_IDF53_I2C_TARGET_COMPAT: ESP-IDF v5.3.2 lacks the v2 target callbacks.
#ifndef MICROPY_PY_MACHINE_I2C_TARGET
#define MICROPY_PY_MACHINE_I2C_TARGET (0)
#endif
EOF
fi
