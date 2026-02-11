#!/usr/bin/env python3
"""Validate Home Assistant compatibility via Zigbee2MQTT converter mapping."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Sequence


@dataclass(frozen=True)
class ModelExpectation:
    model: str
    expected_domain: str
    expected_features: tuple[str, ...] = ()


EXPECTED_MODELS: tuple[ModelExpectation, ...] = (
    ModelExpectation("uzb_Light", "light"),
    ModelExpectation("uzb_DimmableLight", "light"),
    ModelExpectation("uzb_ColorLight", "light"),
    ModelExpectation("uzb_Switch", "action"),
    ModelExpectation("uzb_DimmableSwitch", "action"),
    ModelExpectation(
        "uzb_PowerOutlet",
        "switch",
        expected_features=("power:W", "voltage:V", "current:A"),
    ),
    ModelExpectation("uzb_TemperatureSensor", "sensor", expected_features=("temperature:C",)),
    ModelExpectation("uzb_HumiditySensor", "sensor", expected_features=("humidity:%",)),
    ModelExpectation("uzb_PressureSensor", "sensor", expected_features=("pressure:hPa",)),
    ModelExpectation(
        "uzb_ClimateSensor",
        "sensor",
        expected_features=("temperature:C", "humidity:%", "pressure:hPa"),
    ),
    ModelExpectation("uzb_DoorLock", "lock"),
    ModelExpectation("uzb_DoorLockController", "action"),
    ModelExpectation("uzb_Thermostat", "climate", expected_features=("temperature:C",)),
    ModelExpectation("uzb_OccupancySensor", "binary_sensor", expected_features=("occupancy",)),
    ModelExpectation("uzb_IASZone", "binary_sensor"),
    ModelExpectation("uzb_ContactSensor", "binary_sensor", expected_features=("door",)),
    ModelExpectation("uzb_MotionSensor", "binary_sensor", expected_features=("motion",)),
    ModelExpectation("uzb_WindowCovering", "cover"),
)


EXTEND_TO_HA_DOMAIN: Dict[str, tuple[str, ...]] = {
    "onOff": ("switch",),
    "light": ("light",),
    "electricityMeter": ("sensor", "switch"),
    "temperature": ("sensor",),
    "humidity": ("sensor",),
    "pressure": ("sensor",),
    "lock": ("lock",),
    "thermostat": ("climate",),
    "occupancy": ("binary_sensor",),
    "iasZoneAlarm": ("binary_sensor",),
    "windowCovering": ("cover",),
    # command-oriented entities exposed as actions/buttons in HA via Z2M
    "commandsOnOff": ("action",),
    "commandsLevelCtrl": ("action",),
    "identify": ("action",),
}

# Model-specific compatibility hints for dashboards that classify entities
# by naming/use-case in addition to raw modernExtend families.
MODEL_DOMAIN_OVERRIDES: Dict[str, tuple[str, ...]] = {
    "uzb_Light": ("light",),
}


def parse_converter_definitions(converter_text: str) -> list[dict]:
    blocks = re.findall(r"\{[\s\S]*?\}\s*,?", converter_text)
    out: list[dict] = []
    for block in blocks:
        model_match = re.search(r'model\s*:\s*"([^"]+)"', block)
        if not model_match:
            continue
        model = model_match.group(1).strip()
        extends = re.findall(r"m\.([A-Za-z0-9_]+)\(", block)
        zone_type_match = re.search(r'zoneType\s*:\s*"([^"]+)"', block)
        out.append(
            {
                "model": model,
                "extends": tuple(extends),
                "zone_type": zone_type_match.group(1).strip() if zone_type_match else "",
            }
        )
    return out


def derive_domains(extends: Sequence[str], model: str = "") -> tuple[str, ...]:
    domains: list[str] = []
    for name in extends:
        for domain in EXTEND_TO_HA_DOMAIN.get(name, ()):
            if domain not in domains:
                domains.append(domain)
    for domain in MODEL_DOMAIN_OVERRIDES.get(str(model), ()):
        if domain not in domains:
            domains.append(domain)
    return tuple(domains)


def derive_features(extends: Sequence[str], zone_type: str = "") -> tuple[str, ...]:
    out: list[str] = []

    def add(token: str) -> None:
        if token and token not in out:
            out.append(token)

    for name in extends:
        if name == "temperature":
            add("temperature:C")
        elif name == "humidity":
            add("humidity:%")
        elif name == "pressure":
            add("pressure:hPa")
        elif name == "electricityMeter":
            add("power:W")
            add("voltage:V")
            add("current:A")
        elif name == "occupancy":
            add("occupancy")
        elif name == "thermostat":
            add("temperature:C")
        elif name == "iasZoneAlarm":
            zone = str(zone_type).strip().lower()
            if zone == "contact":
                add("door")
            elif zone == "occupancy":
                add("motion")
            else:
                add("zone")

    return tuple(out)


def run_validation(converter_path: Path) -> dict:
    text = converter_path.read_text(encoding="utf-8")
    parsed = parse_converter_definitions(text)
    by_model = {entry["model"]: entry for entry in parsed}

    missing_models: list[str] = []
    missing_domain: list[dict] = []
    missing_features: list[dict] = []
    unknown_extend: list[dict] = []

    case_rows: list[dict] = []
    for expected in EXPECTED_MODELS:
        row = {
            "model": expected.model,
            "expected_domain": expected.expected_domain,
            "converter_present": False,
            "extends": (),
            "derived_domains": (),
            "derived_features": (),
            "ok": False,
        }
        entry = by_model.get(expected.model)
        if entry is None:
            missing_models.append(expected.model)
            case_rows.append(row)
            continue

        extends = tuple(entry.get("extends", ()))
        zone_type = str(entry.get("zone_type", ""))
        domains = derive_domains(extends, model=expected.model)
        features = derive_features(extends, zone_type=zone_type)
        row["converter_present"] = True
        row["extends"] = extends
        row["derived_domains"] = domains
        row["derived_features"] = features
        domain_ok = expected.expected_domain in domains
        feature_missing = [
            item for item in expected.expected_features if item not in features
        ]
        row["ok"] = domain_ok and not feature_missing
        if not domain_ok:
            missing_domain.append(
                {
                    "model": expected.model,
                    "expected_domain": expected.expected_domain,
                    "derived_domains": domains,
                }
            )
        if feature_missing:
            missing_features.append(
                {
                    "model": expected.model,
                    "expected_features": expected.expected_features,
                    "derived_features": features,
                    "missing": tuple(feature_missing),
                }
            )
        for name in extends:
            if name not in EXTEND_TO_HA_DOMAIN:
                unknown_extend.append({"model": expected.model, "extend": name})
        case_rows.append(row)

    unknown_extend = sorted(
        {f"{item['model']}::{item['extend']}" for item in unknown_extend}
    )
    unknown_extend_rows = [
        {"model": item.split("::", 1)[0], "extend": item.split("::", 1)[1]}
        for item in unknown_extend
    ]

    return {
        "converter_path": str(converter_path),
        "cases": case_rows,
        "missing_models": sorted(missing_models),
        "missing_domain": missing_domain,
        "missing_features": missing_features,
        "unknown_extend": unknown_extend_rows,
        "ok": not missing_models and not missing_domain and not missing_features,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Home Assistant compatibility from Zigbee2MQTT converter."
    )
    parser.add_argument(
        "--converter",
        default="z2m_converters/uzigbee.js",
        help="Path to Zigbee2MQTT external converter file.",
    )
    parser.add_argument(
        "--report-json",
        default="docs/ha_discovery_report.json",
        help="Write validation report JSON to this path.",
    )
    parser.add_argument(
        "--strict-extends",
        action="store_true",
        help="Fail when unknown modernExtend names are encountered.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    converter_path = (root / args.converter).resolve()
    if not converter_path.exists():
        print(f"Missing converter file: {converter_path}")
        return 2

    result = run_validation(converter_path)
    result["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    result["strict_extends"] = bool(args.strict_extends)

    report_path = (root / args.report_json).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"HA discovery report written: {report_path}")
    print(
        "cases=%d missing_models=%d missing_domain=%d missing_features=%d unknown_extend=%d"
        % (
            len(result["cases"]),
            len(result["missing_models"]),
            len(result["missing_domain"]),
            len(result["missing_features"]),
            len(result["unknown_extend"]),
        )
    )

    if result["missing_models"] or result["missing_domain"] or result["missing_features"]:
        return 1
    if args.strict_extends and result["unknown_extend"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
