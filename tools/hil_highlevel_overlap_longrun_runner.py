"""Host runner: high-level dual-switch overlap + long-run stability matrix."""

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path


def _tail_text(path, max_chars=12000):
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace")
    if len(data) <= max_chars:
        return data
    return data[-max_chars:]


def _count_router_ep_hits(text):
    counts = {}
    for line in text.splitlines():
        if not line.startswith("attr src="):
            continue
        if "cluster=0x0006" not in line or "attr=0x0000" not in line:
            continue
        marker = " ep="
        idx = line.find(marker)
        if idx < 0:
            continue
        tail = line[idx + len(marker):]
        end = tail.find(" ")
        if end <= 0:
            continue
        try:
            endpoint_id = int(tail[:end])
        except Exception:
            continue
        counts[endpoint_id] = int(counts.get(endpoint_id, 0)) + 1
    return counts


_COORD_STARTED = re.compile(r"^\[coord-dual \d+\] coordinator_started$")
_COORD_PASS = re.compile(r"^\[coord-dual \d+\] TEST_PASS\b")
_COORD_FAIL = re.compile(r"^\[coord-dual \d+\] TEST_FAIL\b")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coord-port", default="COM6")
    parser.add_argument("--router-port", default="COM3")
    parser.add_argument("--timeout-s", type=int, default=520)
    args = parser.parse_args()

    cwd = Path(__file__).resolve().parents[1]
    py = cwd / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)

    coord_script = "tests/hil_highlevel_coordinator_dual_switch_longrun.py"
    router_script = "tests/hil_highlevel_router_dual_switch_overlap.py"
    coord_out = cwd / "tmp_hil_overlap_coord.out"
    coord_err = cwd / "tmp_hil_overlap_coord.err"
    router_out = cwd / "tmp_hil_overlap_router.out"
    router_err = cwd / "tmp_hil_overlap_router.err"

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
            ep_hits = _count_router_ep_hits(router_text)

            if (not started_router) and _coord_has_started(coord_text):
                print("runner: coordinator ready, start router on", args.router_port)
                router_proc = _start_launcher(py, cwd, args.router_port, router_script, router_out, router_err)
                started_router = True

            if _coord_has_fail(coord_text):
                print("runner: TEST_FAIL (coordinator)")
                print(_tail_text(coord_out, max_chars=4000))
                print(_tail_text(router_out, max_chars=4000))
                return 1
            if _has_traceback(coord_text):
                print("runner: TEST_FAIL (coordinator traceback)")
                print(_tail_text(coord_out, max_chars=4000))
                print(_tail_text(router_out, max_chars=4000))
                return 1
            if _router_has_fail(router_text):
                print("runner: TEST_FAIL (router)")
                print(_tail_text(coord_out, max_chars=4000))
                print(_tail_text(router_out, max_chars=4000))
                return 1
            if _has_traceback(router_text):
                print("runner: TEST_FAIL (router traceback)")
                print(_tail_text(coord_out, max_chars=4000))
                print(_tail_text(router_out, max_chars=4000))
                return 1

            if _coord_has_pass(coord_text):
                active_eps = []
                for endpoint_id, hit_count in sorted(ep_hits.items()):
                    if int(hit_count) >= 20:
                        active_eps.append(int(endpoint_id))
                if len(active_eps) < 2:
                    print("runner: TEST_FAIL router endpoint hit coverage too low counts=%s" % ep_hits)
                    print(_tail_text(coord_out, max_chars=4000))
                    print(_tail_text(router_out, max_chars=4000))
                    return 1
                print("runner: TEST_PASS endpoint_hits=%s" % ep_hits)
                print(_tail_text(coord_out, max_chars=3500))
                print(_tail_text(router_out, max_chars=3500))
                return 0

        print("runner: TIMEOUT")
        print(_tail_text(coord_out, max_chars=4000))
        print(_tail_text(router_out, max_chars=4000))
        return 1
    finally:
        if router_proc is not None:
            router_proc.kill()
        coord_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
