"""Host runner: dual-device high-level HIL (coordinator toggle loop + router LED pin8)."""

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path


def _tail_text(path, max_chars=8000):
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace")
    if len(data) <= max_chars:
        return data
    return data[-max_chars:]


def _start_launcher(py, cwd, port, script, out_path, err_path):
    return subprocess.Popen(
        [
            str(py),
            "tools/run_web_demo_serial.py",
            "--port",
            str(port),
            "--script",
            str(script),
            "--reset",
        ],
        cwd=str(cwd),
        stdout=open(out_path, "w", encoding="utf-8"),
        stderr=open(err_path, "w", encoding="utf-8"),
    )


_COORD_STARTED = re.compile(r"^\[coord \d+\] coordinator_started$")
_COORD_PASS = re.compile(r"^\[coord \d+\] TEST_PASS\b")
_COORD_FAIL = re.compile(r"^\[coord \d+\] TEST_FAIL\b")
_ROUTER_FAIL = re.compile(r"^TEST_FAIL\b")


def _coord_has_started(text):
    for line in text.splitlines():
        if _COORD_STARTED.match(line):
            return True
    return False


def _coord_has_pass(text):
    for line in text.splitlines():
        if _COORD_PASS.match(line):
            return True
    return False


def _coord_has_fail(text):
    for line in text.splitlines():
        if _COORD_FAIL.match(line):
            return True
    return False


def _router_has_fail(text):
    for line in text.splitlines():
        if _ROUTER_FAIL.match(line):
            return True
    return False


def _has_traceback(text):
    return "Traceback (most recent call last):" in text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coord-port", default="COM3")
    parser.add_argument("--router-port", default="COM6")
    parser.add_argument("--timeout-s", type=int, default=220)
    args = parser.parse_args()

    cwd = Path(__file__).resolve().parents[1]
    py = cwd / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)

    coord_script = "tests/hil_highlevel_coordinator_toggle_loop.py"
    router_script = "tests/hil_highlevel_router_led_pin8.py"
    coord_out = cwd / "tmp_hil_dual_coord.out"
    coord_err = cwd / "tmp_hil_dual_coord.err"
    router_out = cwd / "tmp_hil_dual_router.out"
    router_err = cwd / "tmp_hil_dual_router.err"

    for path in (coord_out, coord_err, router_out, router_err):
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    print("runner: start coordinator on", args.coord_port)
    coord_proc = _start_launcher(py, cwd, args.coord_port, coord_script, coord_out, coord_err)
    router_proc = None
    started_router = False
    t0 = time.time()

    try:
        while time.time() - t0 < float(args.timeout_s):
            time.sleep(1.0)
            coord_text = _tail_text(coord_out)
            router_text = _tail_text(router_out)

            if (not started_router) and _coord_has_started(coord_text):
                print("runner: coordinator ready, start router on", args.router_port)
                router_proc = _start_launcher(py, cwd, args.router_port, router_script, router_out, router_err)
                started_router = True

            if _coord_has_pass(coord_text):
                print("runner: TEST_PASS")
                print(_tail_text(coord_out, max_chars=2200))
                print(_tail_text(router_out, max_chars=2200))
                return 0

            if _coord_has_fail(coord_text):
                print("runner: TEST_FAIL (coordinator)")
                print(_tail_text(coord_out, max_chars=2600))
                print(_tail_text(router_out, max_chars=2600))
                return 1
            if _has_traceback(coord_text):
                print("runner: TEST_FAIL (coordinator traceback)")
                print(_tail_text(coord_out, max_chars=2600))
                print(_tail_text(router_out, max_chars=2600))
                return 1

            if _router_has_fail(router_text):
                print("runner: TEST_FAIL (router)")
                print(_tail_text(coord_out, max_chars=2600))
                print(_tail_text(router_out, max_chars=2600))
                return 1
            if _has_traceback(router_text):
                print("runner: TEST_FAIL (router traceback)")
                print(_tail_text(coord_out, max_chars=2600))
                print(_tail_text(router_out, max_chars=2600))
                return 1

        print("runner: TIMEOUT")
        print(_tail_text(coord_out, max_chars=2600))
        print(_tail_text(router_out, max_chars=2600))
        return 1
    finally:
        if router_proc is not None:
            router_proc.kill()
        coord_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
