#!/usr/bin/env bash
# Isolated ESP-IDF environment for uzigbee builds.
# Usage (must be sourced): . tools/wsl-env.sh
set -euo pipefail

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "Please source this script: . tools/wsl-env.sh" >&2
  exit 2
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Guard against Windows HOME being injected into WSL.
if [[ "${HOME:-}" != /home/* ]]; then
  export HOME="/home/$(whoami)"
fi

# Repo-local ESP-IDF (pinned v5.3.2)
export IDF_PATH="${REPO_DIR}/third_party/esp-idf"

# Dedicated tools cache to avoid conflicts with other ESP-IDF users.
export IDF_TOOLS_PATH="${HOME}/.espressif-uzigbee"

if [ ! -f "${IDF_PATH}/export.sh" ]; then
  echo "Missing ESP-IDF at ${IDF_PATH}" >&2
  echo "Run: bash tools/bootstrap_third_party.sh" >&2
  return 1
fi

# Load ESP-IDF environment
. "${IDF_PATH}/export.sh"

# Some ESP-IDF export paths can clobber IDF_PATH in nested setups.
# Re-export the pinned repo-local path for downstream scripts.
export IDF_PATH="${REPO_DIR}/third_party/esp-idf"
