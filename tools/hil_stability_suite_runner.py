"""Batch HIL stability runner for dual ESP32-C6 nodes.

Runs overlap + color portal scenarios in cycles with runtime-state reset.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


RUNTIME_ERASE_REGIONS = (
    ("0x9000", "0x6000"),   # nvs
    ("0x3FB000", "0x4000"), # zb_storage
    ("0x3FF000", "0x1000"), # zb_fct
)


_COMPAT_COORD_RE = re.compile(r"^\[\d+\]\s+coordinator compat: drop unsupported kwarg\b")
_COMPAT_ROUTER_RE = re.compile(r"^router compat: drop unsupported kwarg\b")


def _print_tail(text, max_chars=3000):
    data = text[-max_chars:] if len(text) > max_chars else text
    try:
        print(data)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        safe = data.encode(enc, "replace").decode(enc, "replace")
        print(safe)


def _run_cmd(cmd, timeout_s):
    started = time.time()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=max(1, int(timeout_s)),
    )
    elapsed = time.time() - started
    return proc.returncode, proc.stdout, elapsed


def _analyze_runner_output(output):
    text = str(output or "")
    compat_drop_count = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if _COMPAT_COORD_RE.match(line):
            compat_drop_count += 1
            continue
        if _COMPAT_ROUTER_RE.match(line):
            compat_drop_count += 1
    return {
        "test_pass_marker": "TEST_PASS" in text,
        "test_fail_marker": "TEST_FAIL" in text,
        "timeout_marker": "TIMEOUT" in text,
        "traceback_marker": "Traceback (most recent call last):" in text,
        "compat_drop_count": int(compat_drop_count),
    }


def _write_report(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _erase_runtime_state(py, port):
    for offset, size in RUNTIME_ERASE_REGIONS:
        cmd = [
            str(py),
            "-m",
            "esptool",
            "--chip",
            "esp32c6",
            "--port",
            str(port),
            "--baud",
            "460800",
            "--before",
            "default-reset",
            "--after",
            "hard-reset",
            "erase-region",
            str(offset),
            str(size),
        ]
        rc, out, _ = _run_cmd(cmd, timeout_s=90)
        if rc != 0:
            print(
                "stress: erase failed port=%s offset=%s size=%s rc=%d"
                % (port, offset, size, int(rc))
            )
            _print_tail(out)
            return False
    return True


def _pick_python(cwd):
    py = cwd / ".venv" / "Scripts" / "python.exe"
    if py.exists():
        return py
    return Path(sys.executable)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coord-port", default="COM6")
    parser.add_argument("--router-port", default="COM3")
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--overlap-timeout-s", type=int, default=620)
    parser.add_argument("--color-timeout-s", type=int, default=300)
    parser.add_argument("--skip-color", action="store_true")
    parser.add_argument("--report-json", default="docs/hil_stability_report.json")
    parser.add_argument(
        "--strict-api",
        dest="strict_api",
        action="store_true",
        default=True,
        help="Fail when runner output contains high-level API compatibility fallback markers.",
    )
    parser.add_argument(
        "--no-strict-api",
        dest="strict_api",
        action="store_false",
        help="Allow compatibility fallback markers (drop unsupported kwarg) in runner output.",
    )
    args = parser.parse_args()

    if args.cycles < 1:
        print("stress: --cycles must be >= 1")
        return 2

    cwd = Path(__file__).resolve().parents[1]
    py = _pick_python(cwd)
    started_all = time.time()
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "coord_port": str(args.coord_port),
        "router_port": str(args.router_port),
        "cycles_requested": int(args.cycles),
        "skip_color": bool(args.skip_color),
        "strict_api": bool(args.strict_api),
        "overall_pass": False,
        "total_elapsed_s": 0.0,
        "completed_cycles": 0,
        "entries": [],
    }

    def _append_entry(cycle, scenario, rc, elapsed, output, timeout_s):
        analysis = _analyze_runner_output(output)
        entry = {
            "cycle": int(cycle),
            "scenario": str(scenario),
            "rc": int(rc),
            "elapsed_s": round(float(elapsed), 3),
            "timeout_s": int(timeout_s),
        }
        entry.update(analysis)
        report["entries"].append(entry)
        return entry

    def _fail_with_report(message, output_tail=None):
        print(message)
        if output_tail:
            _print_tail(output_tail)
        report["overall_pass"] = False
        report["total_elapsed_s"] = round(float(time.time() - started_all), 3)
        _write_report(args.report_json, report)
        return 1

    for cycle in range(1, int(args.cycles) + 1):
        print("stress: cycle %d/%d start" % (cycle, int(args.cycles)))

        # Reset runtime Zigbee state before each cycle for deterministic join.
        if not _erase_runtime_state(py, args.coord_port):
            return 1
        if not _erase_runtime_state(py, args.router_port):
            return 1

        overlap_cmd = [
            str(py),
            "tools/hil_highlevel_overlap_longrun_runner.py",
            "--coord-port",
            str(args.coord_port),
            "--router-port",
            str(args.router_port),
            "--timeout-s",
            str(int(args.overlap_timeout_s)),
        ]
        rc, out, elapsed = _run_cmd(
            overlap_cmd, timeout_s=max(60, int(args.overlap_timeout_s) + 90)
        )
        print("stress: cycle %d overlap rc=%d elapsed=%.1fs" % (cycle, int(rc), elapsed))
        overlap_entry = _append_entry(
            cycle=cycle,
            scenario="overlap",
            rc=rc,
            elapsed=elapsed,
            output=out,
            timeout_s=max(60, int(args.overlap_timeout_s) + 90),
        )
        if rc != 0:
            return _fail_with_report("stress: overlap scenario failed", output_tail=out)
        if bool(args.strict_api) and int(overlap_entry.get("compat_drop_count", 0)) > 0:
            return _fail_with_report(
                "stress: strict-api violation in overlap scenario (drop unsupported kwarg detected)",
                output_tail=out,
            )
        if not bool(overlap_entry.get("test_pass_marker", False)):
            return _fail_with_report(
                "stress: overlap scenario missing TEST_PASS marker",
                output_tail=out,
            )

        if not args.skip_color:
            color_cmd = [
                str(py),
                "tools/hil_highlevel_color_portal_runner.py",
                "--coord-port",
                str(args.coord_port),
                "--router-port",
                str(args.router_port),
                "--timeout-s",
                str(int(args.color_timeout_s)),
            ]
            rc, out, elapsed = _run_cmd(
                color_cmd, timeout_s=max(60, int(args.color_timeout_s) + 90)
            )
            print("stress: cycle %d color rc=%d elapsed=%.1fs" % (cycle, int(rc), elapsed))
            color_entry = _append_entry(
                cycle=cycle,
                scenario="color",
                rc=rc,
                elapsed=elapsed,
                output=out,
                timeout_s=max(60, int(args.color_timeout_s) + 90),
            )
            if rc != 0:
                return _fail_with_report("stress: color scenario failed", output_tail=out)
            if bool(args.strict_api) and int(color_entry.get("compat_drop_count", 0)) > 0:
                return _fail_with_report(
                    "stress: strict-api violation in color scenario (drop unsupported kwarg detected)",
                    output_tail=out,
                )
            if not bool(color_entry.get("test_pass_marker", False)):
                return _fail_with_report(
                    "stress: color scenario missing TEST_PASS marker",
                    output_tail=out,
                )

        report["completed_cycles"] = int(cycle)

    print(
        "stress: TEST_PASS cycles=%d total_elapsed=%.1fs"
        % (int(args.cycles), (time.time() - started_all))
    )
    report["overall_pass"] = True
    report["total_elapsed_s"] = round(float(time.time() - started_all), 3)
    _write_report(args.report_json, report)
    print("stress: report %s" % str(args.report_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
