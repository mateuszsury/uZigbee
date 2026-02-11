#!/usr/bin/env python3
"""Automated Zigbee2MQTT interview-oriented HIL suite for uzigbee devices."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class DeviceCase:
    name: str
    model: str
    dashboard_expose: str
    hil_test: str
    read_attr_ok: bool
    reports_ok: bool
    converter_expected: bool = True


DEVICE_CASES: tuple[DeviceCase, ...] = (
    DeviceCase("Light", "uzb_Light", "light", "tests/hil_light_device_smoke.py", True, True),
    DeviceCase("DimmableLight", "uzb_DimmableLight", "light", "tests/hil_dimmable_light_smoke.py", True, True),
    DeviceCase("ColorLight", "uzb_ColorLight", "light", "tests/hil_color_light_smoke.py", True, True),
    DeviceCase("Switch", "uzb_Switch", "action", "tests/hil_switch_smoke.py", True, True),
    DeviceCase("DimmableSwitch", "uzb_DimmableSwitch", "action", "tests/hil_dimmable_switch_smoke.py", True, True),
    DeviceCase("PowerOutlet", "uzb_PowerOutlet", "switch", "tests/hil_power_outlet_smoke.py", True, True),
    DeviceCase("TemperatureSensor", "uzb_TemperatureSensor", "sensor", "tests/hil_temperature_sensor_smoke.py", True, True),
    DeviceCase("HumiditySensor", "uzb_HumiditySensor", "sensor", "tests/hil_humidity_sensor_smoke.py", True, True),
    DeviceCase("PressureSensor", "uzb_PressureSensor", "sensor", "tests/hil_pressure_sensor_smoke.py", True, True),
    DeviceCase("ClimateSensor", "uzb_ClimateSensor", "sensor", "tests/hil_climate_sensor_smoke.py", True, True),
    DeviceCase("DoorLock", "uzb_DoorLock", "lock", "tests/hil_door_lock_smoke.py", True, True),
    DeviceCase("DoorLockController", "uzb_DoorLockController", "action", "tests/hil_door_lock_controller_smoke.py", True, True),
    DeviceCase("Thermostat", "uzb_Thermostat", "climate", "tests/hil_thermostat_smoke.py", True, True),
    DeviceCase("OccupancySensor", "uzb_OccupancySensor", "binary_sensor", "tests/hil_occupancy_sensor_smoke.py", True, True),
    DeviceCase("IASZone", "uzb_IASZone", "binary_sensor", "tests/hil_ias_zone_smoke.py", True, True),
    DeviceCase("ContactSensor", "uzb_ContactSensor", "binary_sensor", "tests/hil_contact_sensor_smoke.py", True, True),
    DeviceCase("MotionSensor", "uzb_MotionSensor", "binary_sensor", "tests/hil_motion_sensor_smoke.py", True, True),
    DeviceCase("WindowCovering", "uzb_WindowCovering", "cover", "tests/hil_window_covering_smoke.py", True, True),
)

BASE_HIL_TESTS: tuple[str, ...] = (
    "tests/hil_basic_identity_smoke.py",
    "tests/hil_z2m_validate_smoke.py",
    "tests/hil_z2m_setters_smoke.py",
    "tests/hil_zigbee_bridge_addr_smoke.py",
)


def build_hil_test_list() -> list[str]:
    out: list[str] = []
    for path in BASE_HIL_TESTS:
        if path not in out:
            out.append(path)
    for case in DEVICE_CASES:
        if case.hil_test not in out:
            out.append(case.hil_test)
    return out


def validate_test_files(root: Path) -> list[str]:
    missing: list[str] = []
    for rel in build_hil_test_list():
        if not (root / rel).exists():
            missing.append(rel)
    return missing


def parse_converter_models(converter_text: str) -> set[str]:
    return set(re.findall(r"model\s*:\s*['\"]([^'\"]+)['\"]", converter_text))


def expected_converter_models() -> set[str]:
    return {c.model for c in DEVICE_CASES if c.converter_expected}


def validate_converter_coverage(converter_path: Path) -> list[str]:
    text = converter_path.read_text(encoding="utf-8")
    present = parse_converter_models(text)
    missing = sorted(expected_converter_models() - present)
    return missing


def run_hil_suite(root: Path, python_exec: str, ports: list[str], retries: int, timeout: int) -> int:
    cmd = [
        python_exec,
        "tools/hil_runner.py",
        "--ports",
        *ports,
        "--tests",
        *build_hil_test_list(),
        "--retries",
        str(retries),
        "--timeout",
        str(timeout),
    ]
    return subprocess.run(cmd, cwd=str(root)).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full uzigbee Z2M interview-oriented suite.")
    parser.add_argument("--ports", nargs="+", default=["COM3", "COM5"], help="Serial ports priority order.")
    parser.add_argument("--retries", type=int, default=4, help="Retries per test and port.")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout per mpremote invocation in seconds.")
    parser.add_argument("--python", default=sys.executable, help="Python executable for child tools.")
    parser.add_argument("--converter", default="z2m_converters/uzigbee.js", help="Path to external converter file.")
    parser.add_argument("--skip-hil", action="store_true", help="Only validate suite metadata and converter coverage.")
    parser.add_argument("--report-json", default="", help="Optional JSON report output path.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    missing_tests = validate_test_files(root)

    converter_path = (root / args.converter).resolve()
    if not converter_path.exists():
        print(f"Missing converter file: {converter_path}")
        return 2

    missing_models = validate_converter_coverage(converter_path)

    print("Z2M interview suite matrix:")
    for case in DEVICE_CASES:
        print(
            f"- {case.name:18} model={case.model:22} expose={case.dashboard_expose:13} "
            f"read_attr={case.read_attr_ok} report={case.reports_ok} test={case.hil_test}"
        )

    if missing_tests:
        print("Missing HIL tests:")
        for rel in missing_tests:
            print(f"- {rel}")
        return 2

    if missing_models:
        print("Converter missing models:")
        for model in missing_models:
            print(f"- {model}")
        return 2

    rc = 0
    if not args.skip_hil:
        rc = run_hil_suite(root, args.python, args.ports, args.retries, args.timeout)

    if args.report_json:
        report_path = (root / args.report_json).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "ports": args.ports,
            "retries": args.retries,
            "timeout": args.timeout,
            "skip_hil": bool(args.skip_hil),
            "converter": str(converter_path),
            "missing_tests": missing_tests,
            "missing_models": missing_models,
            "hil_exit_code": rc,
            "cases": [asdict(c) for c in DEVICE_CASES],
            "hil_tests": build_hil_test_list(),
        }
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Report written: {report_path}")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
