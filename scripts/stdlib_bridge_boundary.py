from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flavent.reporting import ReportIssue, build_report as build_structured_report

_VIOLATION_ERROR_CODE = "ESTDLIBBRIDGE001"
_STALE_ALLOWLIST_WARNING_CODE = "WSTDLIBBRIDGE001"


def _module_name(path: Path, stdlib_root: Path) -> str:
    return path.relative_to(stdlib_root).as_posix().removesuffix(".flv")


def _uses_bridge_python(path: Path) -> bool:
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("use _bridge_python"):
            return True
    return False


def _load_allowlist(path: Path) -> tuple[set[str], dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("entries", [])
    modules: set[str] = set()
    notes: dict[str, str] = {}
    for e in entries:
        module = str(e.get("module", "")).strip()
        if not module:
            continue
        modules.add(module)
        note = str(e.get("note", "")).strip()
        if note:
            notes[module] = note
    return modules, notes


def build_report(stdlib_root: Path, allowlist_path: Path) -> dict[str, Any]:
    allow_modules, notes = _load_allowlist(allowlist_path)
    importing: list[str] = []

    for path in sorted(stdlib_root.rglob("*.flv")):
        if path.name == "_bridge_python.flv":
            continue
        if _uses_bridge_python(path):
            importing.append(_module_name(path, stdlib_root))

    importing_set = set(importing)
    violations = sorted(importing_set - allow_modules)
    stale = sorted(allow_modules - importing_set)

    return {
        "stdlib_root": stdlib_root.as_posix(),
        "allowlist": allowlist_path.as_posix(),
        "importing_modules": sorted(importing),
        "importing_count": len(importing),
        "allowlist_count": len(allow_modules),
        "approved_count": len(importing_set & allow_modules),
        "violation_count": len(violations),
        "stale_count": len(stale),
        "violations": [{"module": m, "note": notes.get(m, "")} for m in violations],
        "stale_allowlist": [{"module": m, "note": notes.get(m, "")} for m in stale],
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Stdlib Bridge Boundary Report")
    lines.append("")
    lines.append(f"- Stdlib root: `{report['stdlib_root']}`")
    lines.append(f"- Allowlist: `{report['allowlist']}`")
    lines.append(f"- Modules importing `_bridge_python`: `{report['importing_count']}`")
    lines.append(f"- Allowed modules: `{report['allowlist_count']}`")
    lines.append(f"- Unapproved modules: `{report['violation_count']}`")
    lines.append(f"- Stale allowlist entries: `{report['stale_count']}`")

    lines.append("")
    lines.append("## Modules importing `_bridge_python`")
    for m in report["importing_modules"]:
        lines.append(f"- `{m}`")

    lines.append("")
    lines.append("## Unapproved Modules")
    if report["violations"]:
        for row in report["violations"]:
            note = row["note"]
            if note:
                lines.append(f"- `{row['module']}` — {note}")
            else:
                lines.append(f"- `{row['module']}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Stale Allowlist Entries")
    if report["stale_allowlist"]:
        for row in report["stale_allowlist"]:
            note = row["note"]
            if note:
                lines.append(f"- `{row['module']}` — {note}")
            else:
                lines.append(f"- `{row['module']}`")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def _issues_for_report(report: dict[str, Any]) -> list[ReportIssue]:
    issues: list[ReportIssue] = []
    for row in report.get("violations", []):
        module = str(row.get("module", ""))
        note = str(row.get("note", ""))
        msg = f"unapproved _bridge_python import in stdlib module `{module}`"
        issues.append(
            ReportIssue(
                severity="error",
                code=_VIOLATION_ERROR_CODE,
                message=msg,
                stage="stdlib_bridge_boundary",
                metadata={"module": module, "note": note},
            )
        )
    for row in report.get("stale_allowlist", []):
        module = str(row.get("module", ""))
        note = str(row.get("note", ""))
        msg = f"stale bridge-boundary allowlist entry for module `{module}`"
        issues.append(
            ReportIssue(
                severity="warning",
                code=_STALE_ALLOWLIST_WARNING_CODE,
                message=msg,
                stage="stdlib_bridge_boundary",
                metadata={"module": module, "note": note},
            )
        )
    return issues


def _structured_report(payload: dict[str, Any], *, stdlib_root: Path, exit_code: int) -> dict[str, Any]:
    status = "ok" if exit_code == 0 else "failed"
    metrics = {
        "bridge_boundary": {
            "importing_count": payload.get("importing_count", 0),
            "allowlist_count": payload.get("allowlist_count", 0),
            "approved_count": payload.get("approved_count", 0),
            "violation_count": payload.get("violation_count", 0),
            "stale_count": payload.get("stale_count", 0),
        }
    }
    return build_structured_report(
        tool="stdlib_bridge_boundary",
        source=stdlib_root.as_posix(),
        status=status,
        exit_code=exit_code,
        issues=_issues_for_report(payload),
        metrics=metrics,
        artifacts={"stdlib_bridge_boundary": payload},
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Check stdlib direct _bridge_python import boundaries")
    ap.add_argument("--stdlib-root", default="stdlib", help="Path to stdlib root")
    ap.add_argument(
        "--allowlist",
        default="docs/stdlib_bridge_boundary_allowlist.json",
        help="JSON allowlist path",
    )
    ap.add_argument("--json-out", default="", help="Write JSON report to this path")
    ap.add_argument("--md-out", default="", help="Write markdown report to this path")
    ap.add_argument(
        "--fail-on-violations",
        action="store_true",
        help="Exit 1 if unapproved bridge imports are found",
    )
    ap.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit 1 if allowlist contains stale entries",
    )
    args = ap.parse_args()

    stdlib_root = Path(args.stdlib_root).resolve()
    allowlist = Path(args.allowlist).resolve()
    payload = build_report(stdlib_root, allowlist)
    markdown = format_markdown(payload)
    exit_code = 0
    if args.fail_on_violations and payload["violation_count"] > 0:
        exit_code = 1
    if args.fail_on_stale and payload["stale_count"] > 0:
        exit_code = 1
    report = _structured_report(payload, stdlib_root=stdlib_root, exit_code=exit_code)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if args.md_out:
        Path(args.md_out).write_text(markdown, encoding="utf-8")

    print(markdown, end="")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
