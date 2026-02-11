"""Run examples/coordinator_web_demo.py on device over serial and keep COM open.

This avoids mpremote raw-REPL instability and prevents accidental reset on
serial close while demo is running.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import serial


def _read_available(ser):
    n = ser.in_waiting
    if not n:
        return ""
    data = ser.read(n)
    return data.decode("utf-8", "replace")


def _read_for(ser, seconds):
    end = time.time() + seconds
    out = []
    while time.time() < end:
        chunk = _read_available(ser)
        if chunk:
            out.append(chunk)
        time.sleep(0.02)
    return "".join(out)


def _reset_to_run_mode(port):
    subprocess.run(
        [sys.executable, "-m", "esptool", "--port", port, "run"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _write_chunked(ser, payload, chunk_size=64, delay_s=0.010):
    data = payload if isinstance(payload, (bytes, bytearray)) else bytes(payload)
    total = len(data)
    idx = 0
    while idx < total:
        end = idx + int(chunk_size)
        ser.write(data[idx:end])
        idx = end
        if delay_s > 0:
            time.sleep(float(delay_s))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--script",
        default="examples/coordinator_web_demo.py",
        help="MicroPython script to send via paste mode.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset device to run mode before sending script.",
    )
    args = parser.parse_args()

    code = Path(args.script).read_text(encoding="utf-8")

    if args.reset:
        _reset_to_run_mode(args.port)

    ser = serial.Serial(
        args.port,
        args.baud,
        timeout=0.2,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False,
    )
    ser.dtr = False
    ser.rts = False
    time.sleep(1.0)

    # Interrupt current code and enter paste mode.
    ser.write(b"\x03\x03\r\n")
    _read_for(ser, 1.0)
    ser.write(b"\x05")
    _read_for(ser, 0.3)

    # Paste and execute script.
    # Chunked send prevents dropped bytes on longer scripts in paste mode.
    _write_chunked(ser, code.encode("utf-8"))
    ser.write(b"\x04")

    print("launcher: script sent, keeping COM open")
    sys.stdout.flush()

    try:
        while True:
            chunk = _read_available(ser)
            if chunk:
                sys.stdout.write(chunk)
                sys.stdout.flush()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
