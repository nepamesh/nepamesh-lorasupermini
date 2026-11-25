#!/usr/bin/env bash
# Flash NEPAMesh LoraSupermini firmware over the nice!nano bootloader's serial DFU.
#
# Usage:
#   ./flash.sh                      # Meshtastic (default)
#   ./flash.sh meshcore <role>      # role: companion_radio_ble | companion_radio_usb | repeater | room_server
#   ./flash.sh <file.zip>           # any DFU .zip
#   PORT=/dev/ttyACM1 ./flash.sh    # force a serial port
#
# Put the board in the bootloader first: double-tap RST to GND (the NICENANO drive appears).
# The 1200-baud trick does not work with the firmware this board was running.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NRFUTIL="${NRFUTIL:-$HOME/.venvs/nrfutil/bin/adafruit-nrfutil}"

die() { echo "error: $*" >&2; exit 1; }

# --- pick the package
case "${1:-meshtastic}" in
  meshtastic)
    PKG=$(ls -t "$HERE"/meshtastic/build/firmware-nepamesh_lorasupermini-*.zip 2>/dev/null | head -1) ;;
  meshcore)
    ROLE="${2:-}"
    [[ -n "$ROLE" ]] || die "meshcore needs a role: companion_radio_ble | companion_radio_usb | repeater | room_server"
    PKG=$(ls -t "$HERE"/meshcore/build/meshcore-nepamesh_lorasupermini-"$ROLE"-*.zip 2>/dev/null | head -1) ;;
  *.zip)
    PKG="$1" ;;
  -h|--help)
    sed -n 2,11p "$0"; exit 0 ;;
  *)
    die "unknown target '$1' (try --help)" ;;
esac
[[ -n "${PKG:-}" && -f "$PKG" ]] || die "firmware package not found"
echo "package: $PKG"

# --- nrfutil (installed into a venv on first run)
if [[ ! -x "$NRFUTIL" ]]; then
  echo "installing adafruit-nrfutil into ~/.venvs/nrfutil ..."
  python3 -m venv "$HOME/.venvs/nrfutil"
  "$HOME/.venvs/nrfutil/bin/pip" -q install adafruit-nrfutil
fi

# --- find the bootloader's serial port
if [[ -z "${PORT:-}" ]]; then
  echo "waiting for the nice!nano bootloader (double-tap RST to GND) ..."
  for _ in $(seq 1 60); do
    BL=$(ls /dev/serial/by-id/ 2>/dev/null | grep -i 'nice_nano' | head -1 || true)
    [[ -n "$BL" ]] && break
    sleep 1
  done
  [[ -n "${BL:-}" ]] || die "no bootloader found after 60 s. Is the board in bootloader mode?"
  PORT=$(readlink -f "/dev/serial/by-id/$BL")
fi
[[ -e "$PORT" ]] || die "$PORT does not exist"
echo "port:    $PORT"

# --- flash
"$NRFUTIL" --verbose dfu serial --package "$PKG" -p "$PORT" -b 115200 --singlebank

echo
echo "done. The board reboots into the new firmware."
case "$PKG" in
  *firmware-nepamesh_lorasupermini*) echo "next: meshtastic --set lora.region <REGION>   (no TX until a region is set)";;
  *repeater*|*room_server*)     echo "next: change the admin password (default 'password')";;
esac
