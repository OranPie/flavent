from __future__ import annotations

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
        "flavent.cli.format_bridge_warnings",
        lambda _report: ["BridgeWarning: deprecated bridge shim used: _pyBase64Encode (count=1)"],
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
