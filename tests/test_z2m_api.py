import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))


class _FakeStack:
    def get_basic_identity(self, endpoint_id=1):
        return {
            "manufacturer_name": "uzigbee",
            "model_identifier": "uzb_light_01",
            "date_code": "20260206",
            "sw_build_id": "1.0.0",
            "power_source": 1,
        }


class _ConfigStack:
    def __init__(self, attrs=None):
        self.attrs = attrs
        self.calls = []

    def get_basic_identity(self, endpoint_id=1):
        if self.attrs is None:
            raise OSError(259)
        return dict(self.attrs)

    def set_basic_identity(self, endpoint_id=1, manufacturer="uzigbee", model="uzb_device", date_code=None, sw_build_id=None, power_source=1):
        self.calls.append((endpoint_id, manufacturer, model, date_code, sw_build_id, power_source))
        self.attrs = {
            "manufacturer_name": manufacturer,
            "model_identifier": model,
            "date_code": date_code,
            "sw_build_id": sw_build_id,
            "power_source": power_source,
        }


def test_z2m_validate_ok():
    z2m = importlib.import_module("uzigbee.z2m")
    z2m._PENDING.clear()
    result = z2m.validate(stack=_FakeStack(), endpoint_id=1)
    assert result["ok"] is True
    assert result["errors"] == []
    assert result["attrs"]["manufacturer_name"] == "uzigbee"


def test_z2m_validate_missing_fields():
    z2m = importlib.import_module("uzigbee.z2m")
    z2m._PENDING.clear()

    class _MissingStack:
        def get_basic_identity(self, endpoint_id=1):
            return {
                "manufacturer_name": None,
                "model_identifier": None,
                "date_code": None,
                "sw_build_id": None,
                "power_source": None,
            }

    result = z2m.validate(stack=_MissingStack(), endpoint_id=1)
    assert result["ok"] is False
    assert "missing manufacturer_name" in result["errors"]
    assert "missing model_identifier" in result["errors"]
    assert "missing power_source" in result["errors"]


def test_z2m_setters_preserve_identity():
    z2m = importlib.import_module("uzigbee.z2m")
    z2m._PENDING.clear()
    stack = _ConfigStack(attrs=None)

    out1 = z2m.set_model_id("uzb_light_set", stack=stack, endpoint_id=1)
    out2 = z2m.set_manufacturer("MyVendor", stack=stack, endpoint_id=1)

    assert out1["model_identifier"] == "uzb_light_set"
    assert out2["manufacturer_name"] == "MyVendor"
    assert out2["model_identifier"] == "uzb_light_set"
    assert stack.calls[-1][1] == "MyVendor"
    assert stack.calls[-1][2] == "uzb_light_set"


def test_z2m_set_identity_uses_live_values():
    z2m = importlib.import_module("uzigbee.z2m")
    z2m._PENDING.clear()
    stack = _ConfigStack(
        attrs={
            "manufacturer_name": "live_vendor",
            "model_identifier": "live_model",
            "date_code": "20260206",
            "sw_build_id": "1.0.0",
            "power_source": 1,
        }
    )

    out = z2m.set_model_id("override_model", stack=stack, endpoint_id=1)
    assert out["manufacturer_name"] == "live_vendor"
    assert out["model_identifier"] == "override_model"
    assert out["date_code"] == "20260206"
