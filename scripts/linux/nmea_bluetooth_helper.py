#!/usr/bin/python3
"""Restricted privileged operations for the NMEA Bluetooth GPS connection."""

import os
import re
import subprocess
import sys


_MAC_ADDRESS = re.compile(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\Z")
_SYSTEM_PATHS = ("/usr/bin", "/usr/sbin", "/bin", "/sbin")


def _find_binary(name):
    for directory in _SYSTEM_PATHS:
        path = os.path.join(directory, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise FileNotFoundError(f"Required Bluetooth command not found: {name}")


def build_command(arguments):
    if arguments == ["adapter-up"]:
        return [_find_binary("hciconfig"), "hci0", "up"], 5

    if len(arguments) == 4 and arguments[0] == "bind":
        _, device, mac_address, channel_text = arguments
        if device != "0":
            raise ValueError("Only rfcomm device 0 is allowed")
        if not _MAC_ADDRESS.fullmatch(mac_address):
            raise ValueError("Invalid Bluetooth MAC address")
        if not channel_text.isdecimal() or not 1 <= int(channel_text) <= 30:
            raise ValueError("SPP channel must be between 1 and 30")
        return [
            _find_binary("rfcomm"),
            "bind",
            "0",
            mac_address.upper(),
            str(int(channel_text)),
        ], 8

    if arguments == ["release", "0"]:
        return [_find_binary("rfcomm"), "release", "0"], 5

    raise ValueError(
        "Usage: nmea-bluetooth-helper adapter-up | "
        "bind 0 MAC_ADDRESS CHANNEL | release 0"
    )


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if os.geteuid() != 0:
        print("This helper must be run through its restricted sudoers rule.", file=sys.stderr)
        return 1

    try:
        command, timeout = build_command(arguments)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
