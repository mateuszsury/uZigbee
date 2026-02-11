#!/usr/bin/env python3
"""Robust HIL batch runner for mpremote on COM3/COM5 (or custom ports)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

try:
    import serial
    import serial.tools.list_ports
except Exception as exc:  # pragma: no cover
    raise SystemExit("pyserial is required for tools/hil_runner.py") from exc


def available_ports() -> set[str]:
    return {p.device.upper() for p in serial.tools.list_ports.comports()}


def resolve_tests(test_args: list[str], root: Path) -> list[Path]:
    if test_args:
        out = []
        for item in test_args:
            p = Path(item)
            if not p.is_absolute():
                p = root / item
            out.append(p.resolve())
        return out
    return sorted((root / "tests").glob("hil_*_smoke.py"))


def pulse_reset(port: str) -> None:
    ser = serial.Serial(port=port, baudrate=115200, timeout=1)
    try:
        ser.dtr = False
        ser.rts = True
        time.sleep(0.12)
        ser.rts = False
        time.sleep(0.05)
    finally:
        ser.close()


def run_mpremote(
    port: str,
    test_path: Path,
    soft_reset: bool,
    timeout_s: int,
    mount_path: str | None = None,
) -> tuple[int, str, str]:
    cmd = [sys.executable, "-m", "mpremote", "connect", port]
    if mount_path:
        cmd.extend(["mount", mount_path])
    cmd.append("resume")
    if soft_reset:
        cmd.extend(["soft-reset", "run", str(test_path)])
    else:
        cmd.extend(["run", str(test_path)])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        err = (err + f"\nTIMEOUT: mpremote exceeded {timeout_s}s").strip()
        return 124, out, err


def try_test_on_port(
    port: str,
    test_path: Path,
    retries: int,
    timeout_s: int,
    mount_path: str | None = None,
) -> tuple[bool, str]:
    last_error = ""
    for attempt in range(1, retries + 1):
        if not mount_path:
            try:
                pulse_reset(port)
            except Exception as exc:
                last_error = f"reset failed: {exc}"
                time.sleep(0.3)
                continue

        soft_reset_modes = (False, True)
        if mount_path:
            # mpremote soft-reset can drop /remote hook mid-command.
            soft_reset_modes = (False,)
        for soft_reset in soft_reset_modes:
            mode = "resume run" if not soft_reset else "resume soft-reset run"
            code, out, err = run_mpremote(
                port,
                test_path,
                soft_reset=soft_reset,
                timeout_s=timeout_s,
                mount_path=mount_path,
            )
            if code == 0:
                return True, out
            last_error = f"{mode} failed (attempt {attempt}/{retries}):\n{out}\n{err}".strip()
            time.sleep(0.25)
    return False, last_error


def main() -> int:
    parser = argparse.ArgumentParser(description="Run HIL tests with reset/retry and COM fallback.")
    parser.add_argument(
        "--ports",
        nargs="+",
        default=["COM3", "COM5"],
        help="Preferred serial ports in priority order (default: COM3 COM5).",
    )
    parser.add_argument(
        "--tests",
        nargs="*",
        default=[],
        help="Test files to run (default: all tests/hil_*_smoke.py).",
    )
    parser.add_argument("--retries", type=int, default=3, help="Retries per port and test.")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per mpremote command in seconds.")
    parser.add_argument(
        "--mount",
        default=None,
        help="Optional local path to mount on device as /remote (for using host Python sources).",
    )
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop after first failed test.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    tests = resolve_tests(args.tests, root)
    if not tests:
        print("No HIL tests found.")
        return 2

    ports_present = available_ports()
    selected_ports = [p.upper() for p in args.ports if p.upper() in ports_present]
    if not selected_ports:
        print(f"No requested ports available. requested={args.ports} available={sorted(ports_present)}")
        return 2

    print(f"HIL ports: {selected_ports}")
    print(f"HIL tests: {[str(t.relative_to(root)) for t in tests]}")

    failures: list[tuple[Path, str]] = []
    for test_path in tests:
        rel = str(test_path.relative_to(root))
        print(f"\n=== RUN {rel} ===")
        test_ok = False
        for port in selected_ports:
            print(f"[{rel}] trying port {port}")
            ok, details = try_test_on_port(
                port,
                test_path,
                retries=args.retries,
                timeout_s=args.timeout,
                mount_path=args.mount,
            )
            if ok:
                print(f"[{rel}] PASS on {port}")
                print(details.strip())
                test_ok = True
                break
            print(f"[{rel}] port {port} failed")
            if details:
                print(details)

        if not test_ok:
            failures.append((test_path, "all ports failed"))
            if args.stop_on_fail:
                break

    print("\n=== SUMMARY ===")
    if failures:
        for test_path, reason in failures:
            print(f"FAIL {test_path.name}: {reason}")
        return 1
    print(f"PASS {len(tests)} tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
