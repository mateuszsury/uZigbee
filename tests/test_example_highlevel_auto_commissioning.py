from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_color_coordinator_example_has_no_hardcoded_network_identity():
    src = _source("examples/coordinator_web_portal_color_highlevel.py")
    assert "ZIGBEE_CHANNEL" not in src
    assert "ZIGBEE_PAN_ID" not in src
    assert "ZIGBEE_EXTENDED_PAN_ID" not in src


def test_color_coordinator_example_defaults_to_guided_with_optional_fixed_override():
    src = _source("examples/coordinator_web_portal_color_highlevel.py")
    assert '"network_mode": "guided"' in src
    assert "FIXED_NETWORK_PROFILE = None" in src
    assert 'kwargs["network_mode"] = "fixed"' in src


def test_color_router_example_has_no_hardcoded_network_identity():
    src = _source("examples/router_neopixel_color_light_highlevel.py")
    assert "ZIGBEE_CHANNEL" not in src
    assert "ZIGBEE_PAN_ID" not in src
    assert "ZIGBEE_EXTENDED_PAN_ID" not in src


def test_color_router_example_defaults_to_guided_with_optional_fixed_override():
    src = _source("examples/router_neopixel_color_light_highlevel.py")
    assert '"commissioning_mode": "guided"' in src
    assert "AUTO_JOIN_CHANNEL_MASK" in src
    assert "FIXED_NETWORK_PROFILE = None" in src
    assert 'kwargs["commissioning_mode"] = "fixed"' in src
