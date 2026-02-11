import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import hil_stability_suite_runner as suite  # noqa: E402


def test_analyze_runner_output_detects_markers_and_compat_drop():
    sample = "\n".join(
        (
            "runner: TEST_PASS",
            "Traceback (most recent call last):",
            '[7] coordinator compat: drop unsupported kwarg network_mode',
            "router compat: drop unsupported kwarg commissioning_mode",
            '                self._log("coordinator compat: drop unsupported kwarg %s" % key)',
            "runner: TIMEOUT",
            "runner: TEST_FAIL",
        )
    )
    analysis = suite._analyze_runner_output(sample)
    assert analysis["test_pass_marker"] is True
    assert analysis["test_fail_marker"] is True
    assert analysis["timeout_marker"] is True
    assert analysis["traceback_marker"] is True
    assert analysis["compat_drop_count"] == 2


def test_write_report_creates_json_file(tmp_path):
    payload = {"overall_pass": True, "completed_cycles": 3}
    target = tmp_path / "reports" / "hil_stability_report.json"
    suite._write_report(target, payload)
    assert target.exists()
    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded == payload
