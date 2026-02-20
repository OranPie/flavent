from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write_report(path: Path, *, tool: str, issues: list[dict[str, object]]) -> None:
    payload = {
        "schema_version": "1.0",
        "tool": tool,
        "source": "test",
        "status": "ok",
        "exit_code": 0,
        "summary": {
            "errors": 0,
            "warnings": sum(1 for i in issues if i.get("severity") == "warning"),
            "infos": 0,
            "suppressed": sum(1 for i in issues if i.get("suppressed")),
            "issue_count": len(issues),
        },
        "issues": issues,
        "metrics": {},
        "artifacts": {},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_warning_policy_gate_write_baseline_and_pass(tmp_path: Path):
    r1 = tmp_path / "r1.json"
    r2 = tmp_path / "r2.json"
    baseline = tmp_path / "warning-baseline.json"
    out = tmp_path / "gate.json"

    _write_report(
        r1,
        tool="stdlib_duplicate_defs",
        issues=[{"severity": "warning", "code": "WAAA001", "suppressed": False}],
    )
    _write_report(
        r2,
        tool="stdlib_bridge_boundary",
        issues=[{"severity": "warning", "code": "WAAA001", "suppressed": False}],
    )

    subprocess.run(
        [
            "python3",
            "scripts/warning_policy_gate.py",
            "--baseline",
            str(baseline),
            "--reports",
            str(r1),
            str(r2),
            "--write-baseline",
        ],
        check=True,
    )
    baseline_data = json.loads(baseline.read_text(encoding="utf-8"))
    assert baseline_data["codes"]["WAAA001"] == 2

    subprocess.run(
        [
            "python3",
            "scripts/warning_policy_gate.py",
            "--baseline",
            str(baseline),
            "--reports",
            str(r1),
            str(r2),
            "--fail-on-new",
            "--json-out",
            str(out),
        ],
        check=True,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["status"] == "ok"
    artifact = data["artifacts"]["warning_policy_gate"]
    assert artifact["diff"]["new_warning_count"] == 0


def test_warning_policy_gate_fails_on_new_warnings(tmp_path: Path):
    r1 = tmp_path / "r1.json"
    baseline = tmp_path / "warning-baseline.json"
    out = tmp_path / "gate.json"
    baseline.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "warning_baseline",
                "codes": {"WAAA001": 1},
                "tools": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_report(
        r1,
        tool="stdlib_duplicate_defs",
        issues=[
            {"severity": "warning", "code": "WAAA001", "suppressed": False},
            {"severity": "warning", "code": "WAAA001", "suppressed": False},
            {"severity": "warning", "code": "WBBB001", "suppressed": False},
        ],
    )

    cp = subprocess.run(
        [
            "python3",
            "scripts/warning_policy_gate.py",
            "--baseline",
            str(baseline),
            "--reports",
            str(r1),
            "--fail-on-new",
            "--json-out",
            str(out),
        ],
        check=False,
    )
    assert cp.returncode == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["status"] == "failed"
    assert data["summary"]["errors"] == 2
    artifact = data["artifacts"]["warning_policy_gate"]
    assert artifact["diff"]["new_warning_count"] == 2
    assert {row["code"] for row in artifact["diff"]["new_codes"]} == {"WAAA001", "WBBB001"}


def test_warning_policy_gate_ignores_suppressed_and_can_fail_on_stale(tmp_path: Path):
    r1 = tmp_path / "r1.json"
    baseline = tmp_path / "warning-baseline.json"
    out = tmp_path / "gate.json"
    baseline.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "warning_baseline",
                "codes": {"WAAA001": 1},
                "tools": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_report(
        r1,
        tool="stdlib_duplicate_defs",
        issues=[{"severity": "warning", "code": "WAAA001", "suppressed": True}],
    )

    subprocess.run(
        [
            "python3",
            "scripts/warning_policy_gate.py",
            "--baseline",
            str(baseline),
            "--reports",
            str(r1),
            "--fail-on-new",
            "--json-out",
            str(out),
        ],
        check=True,
    )
    ok_data = json.loads(out.read_text(encoding="utf-8"))
    assert ok_data["status"] == "ok"
    assert ok_data["artifacts"]["warning_policy_gate"]["diff"]["new_warning_count"] == 0

    cp = subprocess.run(
        [
            "python3",
            "scripts/warning_policy_gate.py",
            "--baseline",
            str(baseline),
            "--reports",
            str(r1),
            "--fail-on-stale",
            "--json-out",
            str(out),
        ],
        check=False,
    )
    assert cp.returncode == 1
    fail_data = json.loads(out.read_text(encoding="utf-8"))
    assert fail_data["status"] == "failed"
    assert fail_data["artifacts"]["warning_policy_gate"]["diff"]["stale_warning_count"] == 1
