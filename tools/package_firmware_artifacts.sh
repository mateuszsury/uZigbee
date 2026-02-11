#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: tools/package_firmware_artifacts.sh <build_dir> [output_dir]

Examples:
  tools/package_firmware_artifacts.sh third_party/micropython-esp32/ports/esp32/build-ESP32_GENERIC_C6-uzigbee-ci
  tools/package_firmware_artifacts.sh third_party/micropython-esp32/ports/esp32/build-ESP32_GENERIC_C6-uzigbee-ci dist/firmware
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

BUILD_DIR="$1"
OUT_DIR="${2:-dist/firmware}"

if [[ ! -d "$BUILD_DIR" ]]; then
  echo "[ERROR] Build dir not found: $BUILD_DIR" >&2
  exit 1
fi

BOOTLOADER_BIN="$BUILD_DIR/bootloader/bootloader.bin"
PARTITION_BIN="$BUILD_DIR/partition_table/partition-table.bin"
APP_BIN="$BUILD_DIR/micropython.bin"
FLASH_ARGS="$BUILD_DIR/flash_args"
SDKCONFIG="$BUILD_DIR/sdkconfig"

required=(
  "$BOOTLOADER_BIN"
  "$PARTITION_BIN"
  "$APP_BIN"
  "$FLASH_ARGS"
)

for file in "${required[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "[ERROR] Required file missing: $file" >&2
    exit 1
  fi
done

mkdir -p "$OUT_DIR"

cp -f "$BOOTLOADER_BIN" "$OUT_DIR/bootloader.bin"
cp -f "$PARTITION_BIN" "$OUT_DIR/partition-table.bin"
cp -f "$APP_BIN" "$OUT_DIR/micropython.bin"
cp -f "$FLASH_ARGS" "$OUT_DIR/flash_args"
if [[ -f "$SDKCONFIG" ]]; then
  cp -f "$SDKCONFIG" "$OUT_DIR/sdkconfig"
fi

APP_SIZE_BYTES="$(stat -c%s "$APP_BIN")"
PART_SIZE_HEX="$(awk -F, '$1 ~ /^factory$/ {gsub(/[ \t]/, "", $5); print $5}' firmware/partitions.csv 2>/dev/null || true)"

cat >"$OUT_DIR/metadata.txt" <<EOF
board=ESP32_GENERIC_C6
build_dir=$BUILD_DIR
app_size_bytes=$APP_SIZE_BYTES
app_size_hex=$(printf '0x%x' "$APP_SIZE_BYTES")
factory_partition_size=${PART_SIZE_HEX:-unknown}
created_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

echo "[OK] Firmware artifacts packaged in: $OUT_DIR"
echo "[OK] Files:"
ls -1 "$OUT_DIR"
