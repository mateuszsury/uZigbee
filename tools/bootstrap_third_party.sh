#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
TP_DIR="${ROOT_DIR}/third_party"

IDF_TAG="v5.3.2"
MPY_TAG="v1.27.0"

IDF_DIR="${TP_DIR}/esp-idf"
MPY_DIR="${TP_DIR}/micropython-esp32"

log() {
  printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"
}

clone_or_update() {
  local url="$1"
  local dir="$2"
  local ref="$3"

  if [[ -d "${dir}/.git" ]]; then
    log "Updating ${dir} -> ${ref}"
    git -C "${dir}" fetch --tags --depth 1 origin "${ref}" || git -C "${dir}" fetch --tags origin
    git -C "${dir}" checkout -f "${ref}"
    if [[ "$(git -C "${dir}" rev-parse --abbrev-ref HEAD)" != "HEAD" ]]; then
      git -C "${dir}" reset --hard "origin/$(git -C "${dir}" rev-parse --abbrev-ref HEAD)" || true
    fi
  elif [[ -d "${dir}" ]]; then
    log "Directory exists without .git, recreating: ${dir}"
    rm -rf "${dir}"
    git clone --branch "${ref}" --depth 1 "${url}" "${dir}"
  else
    log "Cloning ${url} -> ${dir} (${ref})"
    git clone --branch "${ref}" --depth 1 "${url}" "${dir}"
  fi
}

mkdir -p "${TP_DIR}"

clone_or_update "https://github.com/espressif/esp-idf.git" "${IDF_DIR}" "${IDF_TAG}"
clone_or_update "https://github.com/micropython/micropython.git" "${MPY_DIR}" "${MPY_TAG}"

log "Syncing MicroPython submodules (shallow)"
git -C "${MPY_DIR}" submodule sync --recursive
git -C "${MPY_DIR}" submodule update --init --recursive --depth 1

log "Applying uzigbee vendor overrides"
bash "${ROOT_DIR}/tools/apply_vendor_overrides.sh"

log "Bootstrap complete"
log "ESP-IDF: ${IDF_DIR} (${IDF_TAG})"
log "MicroPython: ${MPY_DIR} (${MPY_TAG})"
