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
