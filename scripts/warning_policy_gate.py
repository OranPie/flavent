from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flavent.reporting import ReportIssue, build_report

_NEW_WARNING_ERROR_CODE = "EWARNBASE001"
_STALE_BASELINE_WARNING_CODE = "WWARNBASE001"


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected object JSON at {path}")
    return raw


def _warning_counts_from_report(report: dict[str, Any]) -> tuple[str, Counter[str]]:
    tool = str(report.get("tool", "unknown"))
    counts: Counter[str] = Counter()
    issues = report.get("issues", [])
    if not isinstance(issues, list):
        return tool, counts

    for item in issues:
        if not isinstance(item, dict):
            continue
        if str(item.get("severity", "")).lower() != "warning":
            continue
        if bool(item.get("suppressed", False)):
            continue
        code = str(item.get("code", "WARN")).upper()
        counts[code] += 1
    return tool, counts


def _collect_current(reports: list[Path]) -> dict[str, Any]:
    by_tool: dict[str, Counter[str]] = defaultdict(Counter)
    total: Counter[str] = Counter()

    for path in reports:
        data = _load_json(path)
        tool, counts = _warning_counts_from_report(data)
        by_tool[tool].update(counts)
        total.update(counts)

    return {
        "codes": dict(sorted(total.items())),
        "tools": {
            tool: {
                "codes": dict(sorted(counts.items())),
                "warning_count": int(sum(counts.values())),
            }
            for tool, counts in sorted(by_tool.items())
        },
        "warning_count": int(sum(total.values())),
    }


def _load_baseline(path: Path) -> dict[str, Any]:
    raw = _load_json(path)
    return {
        "schema_version": str(raw.get("schema_version", "1.0")),
        "kind": str(raw.get("kind", "warning_baseline")),
        "codes": dict(raw.get("codes", {})) if isinstance(raw.get("codes", {}), dict) else {},
        "tools": dict(raw.get("tools", {})) if isinstance(raw.get("tools", {}), dict) else {},
    }


def _write_baseline(path: Path, current: dict[str, Any]) -> None:
    payload = {
        "schema_version": "1.0",
        "kind": "warning_baseline",
        "codes": current["codes"],
        "tools": current["tools"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _diff(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    baseline_codes = {str(k).upper(): int(v) for k, v in dict(baseline.get("codes", {})).items()}
    current_codes = {str(k).upper(): int(v) for k, v in dict(current.get("codes", {})).items()}

    new_codes: list[dict[str, Any]] = []
    stale_codes: list[dict[str, Any]] = []

    all_codes = sorted(set(baseline_codes) | set(current_codes))
    for code in all_codes:
        b = baseline_codes.get(code, 0)
        c = current_codes.get(code, 0)
        if c > b:
            new_codes.append({"code": code, "baseline": b, "current": c, "delta": c - b})
        if b > c:
            stale_codes.append({"code": code, "baseline": b, "current": c, "delta": b - c})

    return {
        "new_warning_count": int(sum(i["delta"] for i in new_codes)),
        "new_codes": new_codes,
        "stale_warning_count": int(sum(i["delta"] for i in stale_codes)),
        "stale_codes": stale_codes,
    }


def _issues_from_diff(diff: dict[str, Any]) -> list[ReportIssue]:
    issues: list[ReportIssue] = []
    for item in diff["new_codes"]:
        issues.append(
            ReportIssue(
                severity="error",
                code=_NEW_WARNING_ERROR_CODE,
                message=(
                    f"new warning code `{item['code']}` exceeded baseline "
                    f"({item['baseline']} -> {item['current']})"
                ),
                stage="warning_policy_gate",
                metadata=item,
            )
        )
    for item in diff["stale_codes"]:
        issues.append(
            ReportIssue(
                severity="warning",
                code=_STALE_BASELINE_WARNING_CODE,
                message=(
                    f"baseline warning code `{item['code']}` is stale "
                    f"({item['baseline']} -> {item['current']})"
                ),
                stage="warning_policy_gate",
                metadata=item,
            )
        )
    return issues


def _format_markdown(artifact: dict[str, Any], status: str) -> str:
    lines: list[str] = []
    lines.append("# Warning Policy Gate Report")
    lines.append("")
    lines.append(f"- Baseline: `{artifact['baseline_path']}`")
    lines.append(f"- Inputs: `{len(artifact['report_files'])}` report(s)")
    lines.append(f"- Status: `{status}`")
    lines.append(f"- Current warnings: `{artifact['current']['warning_count']}`")
    lines.append(f"- New warning delta: `{artifact['diff']['new_warning_count']}`")
    lines.append(f"- Stale baseline delta: `{artifact['diff']['stale_warning_count']}`")
    lines.append("")
    lines.append("## Current Warning Codes")
    current_codes = artifact["current"]["codes"]
    if current_codes:
        for code, count in current_codes.items():
            lines.append(f"- `{code}`: `{count}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## New Warning Deltas")
    if artifact["diff"]["new_codes"]:
        for row in artifact["diff"]["new_codes"]:
            lines.append(f"- `{row['code']}`: `{row['baseline']}` -> `{row['current']}` (+`{row['delta']}`)")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Stale Baseline Deltas")
    if artifact["diff"]["stale_codes"]:
        for row in artifact["diff"]["stale_codes"]:
            lines.append(f"- `{row['code']}`: `{row['baseline']}` -> `{row['current']}` (-`{row['delta']}`)")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Enforce warning baseline policy on structured report JSON files")
    ap.add_argument("--baseline", default="docs/warning_baseline.json", help="Baseline JSON path")
    ap.add_argument("--reports", nargs="+", required=True, help="Structured report JSON files")
    ap.add_argument("--write-baseline", action="store_true", help="Write/update baseline from current reports")
    ap.add_argument("--fail-on-new", action="store_true", help="Exit 1 when new warnings exceed baseline")
    ap.add_argument("--fail-on-stale", action="store_true", help="Exit 1 when baseline has stale entries")
    ap.add_argument("--json-out", default="", help="Write structured JSON report to this path")
    ap.add_argument("--md-out", default="", help="Write markdown report to this path")
    args = ap.parse_args()

    baseline_path = Path(args.baseline)
    reports = [Path(p) for p in args.reports]
    current = _collect_current(reports)

    if args.write_baseline:
        _write_baseline(baseline_path, current)
        print(f"Updated baseline: {baseline_path}")
        return 0

    baseline = _load_baseline(baseline_path)
    diff = _diff(baseline, current)
    exit_code = 0
    if args.fail_on_new and diff["new_warning_count"] > 0:
        exit_code = 1
    if args.fail_on_stale and diff["stale_warning_count"] > 0:
        exit_code = 1

    status = "ok" if exit_code == 0 else "failed"
    artifact = {
        "baseline_path": baseline_path.as_posix(),
        "report_files": [p.as_posix() for p in reports],
        "current": current,
        "baseline": baseline,
        "diff": diff,
    }
    issues = _issues_from_diff(diff)
    report = build_report(
        tool="warning_policy_gate",
        source=baseline_path.as_posix(),
        status=status,
        exit_code=exit_code,
        issues=issues,
        metrics={
            "warnings": {
                "current": current["warning_count"],
                "new_delta": diff["new_warning_count"],
                "stale_delta": diff["stale_warning_count"],
            }
        },
        artifacts={"warning_policy_gate": artifact},
    )
    markdown = _format_markdown(artifact, status)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.md_out:
        out = Path(args.md_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8")

    print(markdown, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
