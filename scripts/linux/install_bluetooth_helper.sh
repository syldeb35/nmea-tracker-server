#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this installer with sudo: sudo $0" >&2
    exit 1
fi

if [ -z "${SUDO_USER:-}" ] || [ "$SUDO_USER" = "root" ]; then
    echo "Run this installer with sudo from the account that will use the tray app." >&2
    exit 1
fi

case "$SUDO_USER" in
    *[!A-Za-z0-9_.-]*)
        echo "Unsupported account name: $SUDO_USER" >&2
        exit 1
        ;;
esac

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HELPER_SOURCE="$SCRIPT_DIR/nmea_bluetooth_helper.py"
HELPER_PATH=/usr/local/sbin/nmea-bluetooth-helper
SUDOERS_PATH=/etc/sudoers.d/nmea-bluetooth-helper

if [ ! -r "$HELPER_SOURCE" ]; then
    echo "Helper source not found: $HELPER_SOURCE" >&2
    exit 1
fi

if ! command -v visudo >/dev/null 2>&1; then
    echo "visudo is required to validate the sudoers rule." >&2
    exit 1
fi

sudoers_tmp=$(mktemp)
trap 'rm -f "$sudoers_tmp"' EXIT HUP INT TERM
printf '%s ALL=(root) NOPASSWD: %s\n' "$SUDO_USER" "$HELPER_PATH" > "$sudoers_tmp"

if ! visudo -c -f "$sudoers_tmp"; then
    echo "Generated sudoers rule is invalid; nothing was installed." >&2
    exit 1
fi

install -o root -g root -m 0755 "$HELPER_SOURCE" "$HELPER_PATH"
install -o root -g root -m 0440 "$sudoers_tmp" "$SUDOERS_PATH"
visudo -c -f "$SUDOERS_PATH"

echo "Installed restricted Bluetooth helper for $SUDO_USER."
