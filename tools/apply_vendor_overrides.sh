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
