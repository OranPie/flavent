from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flavent.reporting import ReportIssue, build_report


_RE_FN = re.compile(r"^fn\s+([^\s(]+)\s*\(")
_RE_TYPE = re.compile(r"^type\s+([^=\s]+)")


@dataclass(frozen=True)
class Decl:
    kind: str  # fn | type
    name: str
    module: str
    file: str
    line: int
    sig: str


@dataclass(frozen=True)
class AllowEntry:
    kind: str
    name: str
    modules: tuple[str, ...]
    canonical: str | None
    note: str | None


AllowKey = tuple[str, str, tuple[str, ...]]
_DUPLICATE_ERROR_CODE = "ESTDLIBDUP001"
_STALE_ALLOWLIST_WARNING_CODE = "WSTDLIBDUP001"


def _module_name_for_flv(stdlib_root: Path, flv_path: Path) -> str:
    rel = flv_path.relative_to(stdlib_root)
    if rel.name == "__init__.flv":
        rel = rel.parent
    else:
        rel = rel.with_suffix("")
    return ".".join(rel.parts)


def _is_internal_module(module: str) -> bool:
    head = module.split(".", 1)[0]
    return head.startswith("_") or head == "testns"


def _collect_decls(
    stdlib_root: Path,
    *,
    include_private: bool,
    include_internal_modules: bool,
) -> list[Decl]:
    out: list[Decl] = []
    for path in sorted(stdlib_root.rglob("*.flv")):
        if "/vendor/" in path.as_posix():
            continue
        module = _module_name_for_flv(stdlib_root, path)
        if not include_internal_modules and _is_internal_module(module):
            continue
        rel = path.relative_to(stdlib_root).as_posix()
        for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            m_fn = _RE_FN.match(line)
            if m_fn:
                name = m_fn.group(1)
                if include_private or not name.startswith("_"):
                    out.append(Decl(kind="fn", name=name, module=module, file=rel, line=i, sig=line))
                continue
            m_type = _RE_TYPE.match(line)
            if m_type:
                name = m_type.group(1).split("[", 1)[0]
                if include_private or not name.startswith("_"):
                    out.append(Decl(kind="type", name=name, module=module, file=rel, line=i, sig=line))
    return out


def _allow_key(kind: str, name: str, modules: list[str] | tuple[str, ...]) -> AllowKey:
    return kind, name, tuple(sorted(set(modules)))


def _load_allowlist(path: Path) -> dict[AllowKey, AllowEntry]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw.get("entries") if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        raise ValueError("allowlist JSON must be a list or an object with an 'entries' list")

    out: dict[AllowKey, AllowEntry] = {}
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            raise ValueError(f"allowlist entry #{idx} must be an object")
        kind = item.get("kind")
        name = item.get("name")
        modules = item.get("modules")
        if kind not in {"fn", "type"}:
            raise ValueError(f"allowlist entry #{idx} has invalid kind: {kind!r}")
        if not isinstance(name, str) or not name:
            raise ValueError(f"allowlist entry #{idx} has invalid name")
        if not isinstance(modules, list) or not modules or not all(isinstance(m, str) and m for m in modules):
            raise ValueError(f"allowlist entry #{idx} must define non-empty string 'modules'")

        canonical = item.get("canonical")
        note = item.get("note")
        if canonical is not None and not isinstance(canonical, str):
            raise ValueError(f"allowlist entry #{idx} has invalid canonical")
        if note is not None and not isinstance(note, str):
            raise ValueError(f"allowlist entry #{idx} has invalid note")

        key = _allow_key(kind, name, modules)
        out[key] = AllowEntry(
            kind=kind,
            name=name,
            modules=key[2],
            canonical=canonical,
            note=note,
        )
    return out


def _duplicate_report(
    decls: list[Decl],
    *,
    allowlist: dict[AllowKey, AllowEntry] | None,
) -> dict[str, Any]:
    by_key: dict[tuple[str, str], list[Decl]] = {}
    for d in decls:
        by_key.setdefault((d.kind, d.name), []).append(d)

    allow_map = allowlist or {}
    seen_allow_keys: set[AllowKey] = set()
    duplicates: list[dict[str, Any]] = []

    for (kind, name), vals in sorted(by_key.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        modules = sorted({v.module for v in vals})
        if len(modules) <= 1:
            continue
        key = _allow_key(kind, name, modules)
        allow = allow_map.get(key)
        approved = allow is not None
        if approved:
            seen_allow_keys.add(key)
        locations = [
            {
                "module": v.module,
                "file": v.file,
                "line": v.line,
                "sig": v.sig,
            }
            for v in vals
        ]
        item: dict[str, Any] = {
            "kind": kind,
            "name": name,
            "module_count": len(modules),
            "modules": modules,
            "locations": locations,
            "approved": approved,
        }
        if allow is not None:
            if allow.canonical:
                item["canonical"] = allow.canonical
            if allow.note:
                item["note"] = allow.note
        duplicates.append(item)

    stale_allowlist_entries: list[dict[str, Any]] = []
    for key, entry in sorted(allow_map.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        if key in seen_allow_keys:
            continue
        stale_allowlist_entries.append(
            {
                "kind": entry.kind,
                "name": entry.name,
                "modules": list(entry.modules),
                "canonical": entry.canonical,
                "note": entry.note,
            }
        )

    approved_count = sum(1 for d in duplicates if bool(d.get("approved")))
    unapproved_count = len(duplicates) - approved_count

    return {
        "duplicate_count": len(duplicates),
        "approved_count": approved_count,
        "unapproved_count": unapproved_count,
        "stale_allowlist_count": len(stale_allowlist_entries),
        "stale_allowlist_entries": stale_allowlist_entries,
        "duplicates": duplicates,
    }


def _to_markdown(
    report: dict[str, Any],
    *,
    include_private: bool,
    include_internal_modules: bool,
    allowlist_path: str,
) -> str:
    rows: list[str] = []
    rows.append("# Stdlib Duplicate Definitions Report")
    rows.append("")
    rows.append(f"Scope: {'public+private' if include_private else 'public-only'} symbols")
    scope = "all modules" if include_internal_modules else "public modules only (excludes `_...` and `testns.*`)"
    rows.append(f"Module scope: {scope}")
    rows.append(f"Allowlist: `{allowlist_path or '(none)'}`")
    rows.append(f"Duplicate symbols across modules: `{report['duplicate_count']}`")
    rows.append(f"Approved duplicates: `{report['approved_count']}`")
    rows.append(f"Unapproved duplicates: `{report['unapproved_count']}`")
    rows.append(f"Stale allowlist entries: `{report['stale_allowlist_count']}`")
    rows.append("")

    dups = report["duplicates"]
    if not isinstance(dups, list) or not dups:
        rows.append("No duplicates found.")
        rows.append("")
        return "\n".join(rows)

    unapproved = [d for d in dups if not bool(d.get("approved"))]
    approved = [d for d in dups if bool(d.get("approved"))]

    if unapproved:
        rows.append("## Unapproved Duplicates")
        rows.append("")
        for d in unapproved:
            rows.append(f"### `{d['kind']} {d['name']}` ({d['module_count']} modules)")
            locs = d["locations"]
            if isinstance(locs, list):
                for loc in locs:
                    rows.append(f"- `{loc['module']}` (`{loc['file']}:{loc['line']}`)")
            rows.append("")

    if approved:
        rows.append("## Approved Duplicates")
        rows.append("")
        for d in approved:
            rows.append(f"### `{d['kind']} {d['name']}` ({d['module_count']} modules)")
            if d.get("canonical"):
                rows.append(f"- canonical: `{d['canonical']}`")
            if d.get("note"):
                rows.append(f"- note: {d['note']}")
            locs = d["locations"]
            if isinstance(locs, list):
                for loc in locs:
                    rows.append(f"- `{loc['module']}` (`{loc['file']}:{loc['line']}`)")
            rows.append("")

    stale = report.get("stale_allowlist_entries")
    if isinstance(stale, list) and stale:
        rows.append("## Stale Allowlist Entries")
        rows.append("")
        for item in stale:
            rows.append(f"- `{item['kind']} {item['name']}` modules={item['modules']}")
        rows.append("")

    return "\n".join(rows)


def _issues_for_report(report: dict[str, Any]) -> list[ReportIssue]:
    issues: list[ReportIssue] = []

    for item in report.get("duplicates", []):
        if bool(item.get("approved")):
            continue
        locations = item.get("locations") if isinstance(item.get("locations"), list) else []
        first_location = locations[0] if locations else {}
        location: dict[str, Any] | None = None
        file = str(first_location.get("file", ""))
        line = int(first_location.get("line", 0) or 0)
        if file and line > 0:
            location = {"file": file, "line": line, "col": 1}

        modules = item.get("modules", [])
        msg = f"unapproved duplicate {item.get('kind')} `{item.get('name')}` across modules: {', '.join(modules)}"
        issues.append(
            ReportIssue(
                severity="error",
                code=_DUPLICATE_ERROR_CODE,
                message=msg,
                stage="stdlib_duplicate_defs",
                location=location,
                metadata={
                    "kind": item.get("kind"),
                    "name": item.get("name"),
                    "modules": modules,
                    "module_count": item.get("module_count"),
                },
            )
        )

    for item in report.get("stale_allowlist_entries", []):
        modules = item.get("modules", [])
        msg = f"stale duplicate allowlist entry for {item.get('kind')} `{item.get('name')}`"
        issues.append(
            ReportIssue(
                severity="warning",
                code=_STALE_ALLOWLIST_WARNING_CODE,
                message=msg,
                stage="stdlib_duplicate_defs",
                metadata={
                    "kind": item.get("kind"),
                    "name": item.get("name"),
                    "modules": modules,
                },
            )
        )

    return issues


def _structured_report(payload: dict[str, Any], *, stdlib_root: Path, exit_code: int) -> dict[str, Any]:
    issues = _issues_for_report(payload)
    status = "ok" if exit_code == 0 else "failed"
    metrics = {
        "duplicates": {
            "duplicate_count": payload.get("duplicate_count", 0),
            "approved_count": payload.get("approved_count", 0),
            "unapproved_count": payload.get("unapproved_count", 0),
            "stale_allowlist_count": payload.get("stale_allowlist_count", 0),
        }
    }
    return build_report(
        tool="stdlib_duplicate_defs",
        source=stdlib_root.as_posix(),
        status=status,
        exit_code=exit_code,
        issues=issues,
        metrics=metrics,
        artifacts={"stdlib_duplicate_defs": payload},
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect duplicate stdlib definitions across modules")
    ap.add_argument("--stdlib-root", default="stdlib", help="Path to stdlib root")
    ap.add_argument("--include-private", action="store_true", help="Include private names that start with _")
    ap.add_argument(
        "--include-internal-modules",
        action="store_true",
        help="Include internal stdlib modules (e.g. `_bridge_python` and `testns.*`) in duplicate checks",
    )
    ap.add_argument("--allowlist", default="", help="Optional JSON allowlist for approved duplicate definitions")
    ap.add_argument("--json-out", default="", help="Write JSON report to this path")
    ap.add_argument("--md-out", default="", help="Write markdown report to this path")
    ap.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="Exit non-zero when unapproved duplicates are found",
    )
    args = ap.parse_args()

    stdlib_root = Path(args.stdlib_root).resolve()
    allowlist: dict[AllowKey, AllowEntry] | None = None
    if args.allowlist:
        allowlist = _load_allowlist(Path(args.allowlist))

    decls = _collect_decls(
        stdlib_root,
        include_private=bool(args.include_private),
        include_internal_modules=bool(args.include_internal_modules),
    )
    payload = _duplicate_report(decls, allowlist=allowlist)
    markdown = _to_markdown(
        payload,
        include_private=bool(args.include_private),
        include_internal_modules=bool(args.include_internal_modules),
        allowlist_path=args.allowlist,
    )
    exit_code = 0
    if args.fail_on_duplicates and int(payload["unapproved_count"]) > 0:
        exit_code = 1
    report = _structured_report(payload, stdlib_root=stdlib_root, exit_code=exit_code)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(markdown, encoding="utf-8")

    print(markdown)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
