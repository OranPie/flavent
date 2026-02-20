from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReportIssue:
    severity: str
    code: str
    message: str
    stage: str
    location: dict[str, Any] | None = None
    hint: str = ""
    suppressed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "stage": self.stage,
            "suppressed": self.suppressed,
        }
        if self.location:
            out["location"] = self.location
        if self.hint:
            out["hint"] = self.hint
        if self.metadata:
            out["metadata"] = self.metadata
        return out


def build_report(
    *,
    tool: str,
    source: str,
    status: str,
    exit_code: int,
    issues: list[ReportIssue],
    metrics: dict[str, Any] | None = None,
    artifacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors = 0
    warnings = 0
    infos = 0
    suppressed = 0
    for i in issues:
        if i.suppressed:
            suppressed += 1
        if i.severity == "error":
            errors += 1
        elif i.severity == "warning":
            warnings += 1
        elif i.severity == "info":
            infos += 1

    return {
        "schema_version": "1.0",
        "tool": tool,
        "source": source,
        "status": status,
        "exit_code": exit_code,
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "suppressed": suppressed,
            "issue_count": len(issues),
        },
        "issues": [i.to_dict() for i in issues],
        "metrics": metrics or {},
        "artifacts": artifacts or {},
    }
