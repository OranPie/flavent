from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from flavent.cli import main


def _write_program(path: Path) -> None:
    path.write_text(
        """type Event.Start = {}

sector main:
  on Event.Start -> do:
    stop()

run()
""",
        encoding="utf-8",
    )


@pytest.mark.integration
def test_check_report_junit_success(tmp_path: Path):
    src = tmp_path / "ok.flv"
    junit = tmp_path / "reports" / "ok.xml"
    _write_program(src)

    rc = main(["check", str(src), "--report-junit", str(junit)])
    assert rc == 0
    assert junit.exists()

    suite = ET.parse(junit).getroot()
    assert suite.attrib["tests"] == "1"
    assert suite.attrib["failures"] == "0"
    assert suite.find("./testcase/failure") is None


@pytest.mark.integration
def test_check_report_junit_failure(tmp_path: Path):
    src = tmp_path / "bad.flv"
    junit = tmp_path / "reports" / "bad.xml"
    src.write_text("fn broken( -> Int = 1\n", encoding="utf-8")

    rc = main(["check", str(src), "--report-junit", str(junit)])
    assert rc == 2
    assert junit.exists()

    suite = ET.parse(junit).getroot()
    assert suite.attrib["failures"] == "1"
    failure = suite.find("./testcase/failure")
    assert failure is not None
    assert failure.attrib["message"] == "ParseError"
    assert failure.text is not None and "ParseError:" in failure.text


@pytest.mark.integration
def test_check_strict_fails_when_warnings_exist(tmp_path: Path, monkeypatch, capsys):
    src = tmp_path / "warn.flv"
    junit = tmp_path / "reports" / "strict.xml"
    _write_program(src)

    monkeypatch.setattr(
        "flavent.cli.bridge_warning_issues",
        lambda _report: [
            {
                "severity": "warning",
                "code": "WBR001",
                "message": "deprecated bridge shim used: _pyBase64Encode (count=1)",
                "stage": "bridge_audit",
                "location": None,
                "hint": "",
                "metadata": {"symbol": "_pyBase64Encode", "count": 1},
            }
        ],
    )

    rc = main(["check", str(src), "--strict", "--report-junit", str(junit)])
    out = capsys.readouterr().out

    assert rc == 2
    assert "BridgeWarning:" in out
    assert "StrictCheckError:" in out
    assert junit.exists()

    suite = ET.parse(junit).getroot()
    failure = suite.find("./testcase/failure")
    assert failure is not None
    assert failure.attrib["message"].startswith("StrictCheckError:")


@pytest.mark.integration
def test_check_report_json_schema_and_warning_metadata(tmp_path: Path, monkeypatch):
    src = tmp_path / "warn-json.flv"
    out = tmp_path / "reports" / "check.json"
    _write_program(src)

    monkeypatch.setattr(
        "flavent.cli.bridge_warning_issues",
        lambda _report: [
            {
                "severity": "warning",
                "code": "WBR001",
                "message": "deprecated bridge shim used: _pyBase64Encode (count=1)",
                "stage": "bridge_audit",
                "location": {"file": str(src), "line": 1, "col": 1},
                "hint": "use stdlib wrapper",
                "metadata": {"symbol": "_pyBase64Encode", "count": 1},
            }
        ],
    )

    rc = main(["check", str(src), "--bridge-warn", "--report-json", str(out)])
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1.0"
    assert report["status"] == "ok"
    assert report["summary"]["warnings"] == 1
    assert report["summary"]["errors"] == 0
    assert report["issues"][0]["code"] == "WBR001"
    assert report["issues"][0]["stage"] == "bridge_audit"


@pytest.mark.integration
def test_check_warning_controls_escalate_and_suppress(tmp_path: Path, monkeypatch):
    src = tmp_path / "warn-controls.flv"
    fail_json = tmp_path / "reports" / "warn-fail.json"
    ok_json = tmp_path / "reports" / "warn-ok.json"
    _write_program(src)

    monkeypatch.setattr(
        "flavent.cli.bridge_warning_issues",
        lambda _report: [
            {
                "severity": "warning",
                "code": "WBR001",
                "message": "deprecated bridge shim used: _pyBase64Encode (count=1)",
                "stage": "bridge_audit",
                "location": None,
                "hint": "",
                "metadata": {"symbol": "_pyBase64Encode", "count": 1},
            }
        ],
    )

    rc_fail = main(
        [
            "check",
            str(src),
            "--warn-code-as-error",
            "WBR001",
            "--report-json",
            str(fail_json),
        ]
    )
    assert rc_fail == 2
    fail_report = json.loads(fail_json.read_text(encoding="utf-8"))
    assert fail_report["status"] == "failed"
    assert any(i["code"] == "ECHECKWARN" for i in fail_report["issues"])

    rc_ok = main(
        [
            "check",
            str(src),
            "--warn-code-as-error",
            "WBR001",
            "--suppress-warning",
            "WBR001",
            "--report-json",
            str(ok_json),
        ]
    )
    assert rc_ok == 0
    ok_report = json.loads(ok_json.read_text(encoding="utf-8"))
    assert ok_report["status"] == "ok"
    assert ok_report["summary"]["suppressed"] == 1


@pytest.mark.integration
def test_check_report_json_includes_mixin_hook_plan(tmp_path: Path):
    src = tmp_path / "mixin-plan.flv"
    out = tmp_path / "reports" / "mixin-plan.json"
    src.write_text(
        """type Event.Start = {}

sector S:
  fn foo(x: Int) -> Int = x

mixin M v1 into sector S:
  hook invoke fn foo(x: Int) -> Int with(id="H", priority=3) = do:
    return proceed(x)

use mixin M v1

sector main:
  on Event.Start -> do:
    rpc S.foo(1)
    stop()

run()
""",
        encoding="utf-8",
    )
    rc = main(["check", str(src), "--report-json", str(out)])
    assert rc == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    mixin_plan = report["artifacts"].get("mixin_hook_plan")
    assert isinstance(mixin_plan, list) and mixin_plan
    assert mixin_plan[0]["target"] == "S.foo"
    assert mixin_plan[0]["hook_id"] == "H"
    assert mixin_plan[0]["conflict_policy"] == "error"
    assert mixin_plan[0]["status"] == "active"
