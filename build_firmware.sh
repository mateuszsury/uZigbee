#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR="$SCRIPT_DIR"

BOARD_DEFAULT="ESP32_GENERIC_C6"
BUILD_DEFAULT="build-${BOARD_DEFAULT}-uzigbee"
MICROPY_DIR_DEFAULT="$ROOT_DIR/third_party/micropython-esp32"
USER_C_MODULES_DEFAULT="$ROOT_DIR/c_module/micropython.cmake"
FROZEN_MANIFEST_DEFAULT="$ROOT_DIR/firmware/manifest.py"
SDKCONFIG_DEFAULTS_DEFAULT="$ROOT_DIR/firmware/sdkconfig.defaults"
PROFILE_DEFAULT="esp32-c6-devkit"

BOARD_ENV="${BOARD:-}"
SDKCONFIG_DEFAULTS_ENV="${SDKCONFIG_DEFAULTS:-}"
BOARD="${BOARD_ENV:-$BOARD_DEFAULT}"
BUILD="${BUILD:-}"
MICROPY_DIR="${MICROPY_DIR:-$MICROPY_DIR_DEFAULT}"
USER_C_MODULES="${USER_C_MODULES:-$USER_C_MODULES_DEFAULT}"
FROZEN_MANIFEST="${FROZEN_MANIFEST:-$FROZEN_MANIFEST_DEFAULT}"
SDKCONFIG_DEFAULTS="${SDKCONFIG_DEFAULTS_ENV:-$SDKCONFIG_DEFAULTS_DEFAULT}"
PROFILE="${PROFILE:-$PROFILE_DEFAULT}"

RUN_SUBMODULES=0
RUN_MPYCROSS_MODE="auto" # auto|force|skip
RUN_CLEAN=0
USE_LOCK=1
LIST_PROFILES=0
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"
BOARD_EXPLICIT=0
SDKCONFIG_EXPLICIT=0
PROFILE_EXPLICIT=0
declare -a MAKE_EXTRA_ARGS=()

usage() {
  cat <<'EOF'
Usage: ./build_firmware.sh [options] [-- <extra make args>]

Options:
  --board <BOARD>             Target board (default: ESP32_GENERIC_C6)
  --profile <PROFILE>         Hardware profile from firmware/boards/*.env (default: esp32-c6-devkit)
  --list-profiles             List available hardware profiles and exit
  --sdkconfig-defaults <PATH> Override SDKCONFIG_DEFAULTS path
  --build <BUILD_DIR_NAME>    Build dir under ports/esp32 (default: build-ESP32_GENERIC_C6-uzigbee)
  --jobs <N>                  Parallel make jobs (default: nproc)
  --submodules                Force `make submodules` before build
  --skip-submodules           Skip `make submodules` (default)
  --skip-mpy-cross            Skip mpy-cross build
  --force-mpy-cross           Force mpy-cross rebuild
  --clean                     Run `make clean` for selected BOARD/BUILD before build
  --no-lock                   Disable anti-collision file locks
  --help                      Show help

Environment overrides:
  MICROPY_DIR, USER_C_MODULES, FROZEN_MANIFEST, SDKCONFIG_DEFAULTS, BOARD, BUILD, JOBS, PROFILE
EOF
}

list_profiles() {
  local profile_dir="$ROOT_DIR/firmware/boards"
  if [[ ! -d "$profile_dir" ]]; then
    echo "[ERROR] Missing profile directory: $profile_dir" >&2
    return 1
  fi
  find "$profile_dir" -maxdepth 1 -type f -name "*.env" -printf '%f\n' \
    | sed 's/\.env$//' \
    | sort
}

load_profile() {
  local profile_id="$1"
  local profile_dir="$ROOT_DIR/firmware/boards"
  local profile_file="$profile_dir/${profile_id}.env"
  local profile_sdkconfig=""

  if [[ "$profile_id" == "none" ]]; then
    PROFILE="none"
    return 0
  fi
  if [[ ! -f "$profile_file" ]]; then
    echo "[ERROR] Unknown profile '$profile_id'. Run --list-profiles." >&2
    return 1
  fi

  PROFILE_ID=""
  PROFILE_BOARD=""
  PROFILE_SDKCONFIG_DEFAULTS=""
  PROFILE_DESCRIPTION=""
  # shellcheck source=/dev/null
  . "$profile_file"

  if [[ -z "$PROFILE_ID" ]]; then
    PROFILE_ID="$profile_id"
  fi
  if [[ -n "$PROFILE_SDKCONFIG_DEFAULTS" ]]; then
    if [[ "$PROFILE_SDKCONFIG_DEFAULTS" = /* ]]; then
      profile_sdkconfig="$PROFILE_SDKCONFIG_DEFAULTS"
    else
      profile_sdkconfig="$ROOT_DIR/$PROFILE_SDKCONFIG_DEFAULTS"
    fi
  fi

  if [[ "$BOARD_EXPLICIT" -eq 0 && -n "$PROFILE_BOARD" ]]; then
    BOARD="$PROFILE_BOARD"
  fi
  if [[ "$SDKCONFIG_EXPLICIT" -eq 0 && -n "$profile_sdkconfig" ]]; then
    SDKCONFIG_DEFAULTS="$profile_sdkconfig"
  fi
  PROFILE="$PROFILE_ID"
}

if [[ -n "$BOARD_ENV" ]]; then
  BOARD_EXPLICIT=1
fi
if [[ -n "$SDKCONFIG_DEFAULTS_ENV" ]]; then
  SDKCONFIG_EXPLICIT=1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --board)
      BOARD="$2"
      BOARD_EXPLICIT=1
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      PROFILE_EXPLICIT=1
      shift 2
      ;;
    --list-profiles)
      LIST_PROFILES=1
      shift
      ;;
    --sdkconfig-defaults)
      SDKCONFIG_DEFAULTS="$2"
      SDKCONFIG_EXPLICIT=1
      shift 2
      ;;
    --build)
      BUILD="$2"
      shift 2
      ;;
    --jobs)
      JOBS="$2"
      shift 2
      ;;
    --submodules)
      RUN_SUBMODULES=1
      shift
      ;;
    --skip-submodules)
      RUN_SUBMODULES=0
      shift
      ;;
    --skip-mpy-cross)
      RUN_MPYCROSS_MODE="skip"
      shift
      ;;
    --force-mpy-cross)
      RUN_MPYCROSS_MODE="force"
      shift
      ;;
    --clean)
      RUN_CLEAN=1
      shift
      ;;
    --no-lock)
      USE_LOCK=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      MAKE_EXTRA_ARGS=("$@")
      break
      ;;
    *)
      echo "[ERROR] Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$LIST_PROFILES" -eq 1 ]]; then
  list_profiles
  exit 0
fi

load_profile "$PROFILE"

log() {
  printf '[%s] %s\n' "$(date +'%H:%M:%S')" "$*"
}

pick_default_build() {
  local esp32_port_dir="$MICROPY_DIR/ports/esp32"
  local candidate

  # Prefer the newest completed step build, because these are the validated
  # per-step workdirs used by this project and usually give the fastest
  # incremental rebuild times.
  while IFS= read -r candidate; do
    if [[ -f "$esp32_port_dir/$candidate/micropython.bin" && -f "$esp32_port_dir/$candidate/flash_args" ]]; then
      echo "$candidate"
      return 0
    fi
  done < <(find "$esp32_port_dir" -maxdepth 1 -mindepth 1 -type d -name "build-${BOARD}-uzigbee-step*" -printf '%f\n' | sort -V -r)

  candidate="build-${BOARD}-uzigbee"
  if [[ -f "$esp32_port_dir/$candidate/micropython.bin" && -f "$esp32_port_dir/$candidate/flash_args" ]]; then
    echo "$candidate"
    return 0
  fi

  echo "$candidate"
}

if [[ ! -f "$ROOT_DIR/tools/wsl-env.sh" ]]; then
  echo "[ERROR] Missing WSL env helper: $ROOT_DIR/tools/wsl-env.sh" >&2
  exit 1
fi

# shellcheck source=/dev/null
. "$ROOT_DIR/tools/wsl-env.sh" >/dev/null

if ! command -v idf.py >/dev/null 2>&1; then
  echo "[ERROR] idf.py not available after sourcing tools/wsl-env.sh" >&2
  exit 1
fi

IDF_VERSION_RAW="$(idf.py --version 2>&1 || true)"
if [[ "$IDF_VERSION_RAW" != *"v5.3.2"* ]]; then
  echo "[ERROR] Unsupported ESP-IDF version. Required: v5.3.2, got: ${IDF_VERSION_RAW}" >&2
  exit 1
fi

export IDF_TARGET="${IDF_TARGET:-esp32c6}"

if [[ ! -d "$MICROPY_DIR" ]]; then
  echo "[ERROR] MicroPython repo not found: $MICROPY_DIR" >&2
  echo "[HINT] Run: bash tools/bootstrap_third_party.sh" >&2
  exit 1
fi
if [[ ! -f "$USER_C_MODULES" ]]; then
  echo "[ERROR] USER_C_MODULES file not found: $USER_C_MODULES" >&2
  exit 1
fi
if [[ ! -f "$FROZEN_MANIFEST" ]]; then
  echo "[ERROR] FROZEN_MANIFEST file not found: $FROZEN_MANIFEST" >&2
  exit 1
fi
if [[ ! -f "$SDKCONFIG_DEFAULTS" ]]; then
  echo "[ERROR] SDKCONFIG_DEFAULTS file not found: $SDKCONFIG_DEFAULTS" >&2
  exit 1
fi

if ! [[ "$JOBS" =~ ^[0-9]+$ ]] || [[ "$JOBS" -lt 1 ]]; then
  echo "[ERROR] --jobs must be a positive integer, got: $JOBS" >&2
  exit 2
fi

if [[ -z "$BUILD" ]]; then
  BUILD="$(pick_default_build)"
fi

if command -v ccache >/dev/null 2>&1; then
  export IDF_CCACHE_ENABLE=1
fi

BUILD_ROOT="$MICROPY_DIR/ports/esp32/$BUILD"
if [[ "$USE_LOCK" -eq 1 ]] && command -v flock >/dev/null 2>&1; then
  LOCK_DIR="${HOME}/.cache/uzigbee-locks"
  mkdir -p "$LOCK_DIR"
  SAFE_BUILD_NAME="$(echo "$BUILD" | tr '/:' '__')"
  TOOL_LOCK_FILE="$LOCK_DIR/idf-tools.lock"
  BUILD_LOCK_FILE="$LOCK_DIR/${SAFE_BUILD_NAME}.lock"
  exec 9>"$TOOL_LOCK_FILE"
  if ! flock -n 9; then
    echo "[ERROR] Another build is using the shared ESP-IDF tools environment." >&2
    exit 1
  fi
  exec 8>"$BUILD_LOCK_FILE"
  if ! flock -n 8; then
    echo "[ERROR] Build directory '$BUILD' is already locked by another build." >&2
    exit 1
  fi
fi

MPYCROSS_BIN="$MICROPY_DIR/mpy-cross/build/mpy-cross"
if [[ "$RUN_MPYCROSS_MODE" == "force" ]] || [[ "$RUN_MPYCROSS_MODE" == "auto" && ! -x "$MPYCROSS_BIN" ]]; then
  log "Building mpy-cross (mode=$RUN_MPYCROSS_MODE)"
  make -C "$MICROPY_DIR/mpy-cross" -j "$JOBS"
fi
if [[ -x "$MPYCROSS_BIN" ]]; then
  export MICROPY_MPYCROSS="${MICROPY_MPYCROSS:-$MPYCROSS_BIN}"
fi

if [[ "$RUN_SUBMODULES" -eq 1 ]]; then
  log "Updating MicroPython submodules"
  make -C "$MICROPY_DIR/ports/esp32" submodules BOARD="$BOARD"
fi

if [[ "$RUN_CLEAN" -eq 1 ]]; then
  log "Cleaning build dir: $BUILD"
  make -C "$MICROPY_DIR/ports/esp32" BOARD="$BOARD" BUILD="$BUILD" clean
fi

log "Build start: profile=$PROFILE board=$BOARD build=$BUILD jobs=$JOBS submodules=$RUN_SUBMODULES mpy-cross=$RUN_MPYCROSS_MODE"
make -C "$MICROPY_DIR/ports/esp32" \
  -j "$JOBS" \
  BOARD="$BOARD" \
  BUILD="$BUILD" \
  USER_C_MODULES="$USER_C_MODULES" \
  FROZEN_MANIFEST="$FROZEN_MANIFEST" \
  SDKCONFIG_DEFAULTS="$SDKCONFIG_DEFAULTS" \
  "${MAKE_EXTRA_ARGS[@]}"

APP_BIN="$BUILD_ROOT/micropython.bin"
FLASH_ARGS="$BUILD_ROOT/flash_args"
if [[ -f "$APP_BIN" ]]; then
  APP_SIZE_BYTES="$(stat -c%s "$APP_BIN")"
  printf '[OK] Build complete: %s\n' "$BUILD_ROOT"
  printf '[OK] micropython.bin size: 0x%x (%s bytes)\n' "$APP_SIZE_BYTES" "$APP_SIZE_BYTES"
else
  echo "[WARN] Build finished but micropython.bin not found at $APP_BIN" >&2
fi
if [[ -f "$FLASH_ARGS" ]]; then
  printf '[OK] Flash args: %s\n' "$FLASH_ARGS"
fi
