from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


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


def _module_name_for_flv(stdlib_root: Path, flv_path: Path) -> str:
    rel = flv_path.relative_to(stdlib_root)
    if rel.name == "__init__.flv":
        rel = rel.parent
    else:
        rel = rel.with_suffix("")
    return ".".join(rel.parts)


def _collect_decls(stdlib_root: Path, *, include_private: bool) -> list[Decl]:
    out: list[Decl] = []
    for path in sorted(stdlib_root.rglob("*.flv")):
        if "/vendor/" in path.as_posix():
            continue
        module = _module_name_for_flv(stdlib_root, path)
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


def _duplicate_report(decls: list[Decl]) -> dict[str, object]:
    by_key: dict[tuple[str, str], list[Decl]] = {}
    for d in decls:
        by_key.setdefault((d.kind, d.name), []).append(d)

    duplicates: list[dict[str, object]] = []
    for (kind, name), vals in sorted(by_key.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        modules = sorted({v.module for v in vals})
        if len(modules) <= 1:
            continue
        locations = [
            {
                "module": v.module,
                "file": v.file,
                "line": v.line,
                "sig": v.sig,
            }
            for v in vals
        ]
        duplicates.append(
            {
                "kind": kind,
                "name": name,
                "module_count": len(modules),
                "modules": modules,
                "locations": locations,
            }
        )

    return {
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
    }


def _to_markdown(report: dict[str, object], *, include_private: bool) -> str:
    rows: list[str] = []
    rows.append("# Stdlib Duplicate Definitions Report")
    rows.append("")
    rows.append(f"Scope: {'public+private' if include_private else 'public-only'} symbols")
    rows.append(f"Duplicate symbols across modules: `{report['duplicate_count']}`")
    rows.append("")
    dups = report["duplicates"]
    if not isinstance(dups, list) or not dups:
        rows.append("No duplicates found.")
        rows.append("")
        return "\n".join(rows)

    for d in dups:
        kind = d["kind"]
        name = d["name"]
        module_count = d["module_count"]
        rows.append(f"## `{kind} {name}` ({module_count} modules)")
        locs = d["locations"]
        if isinstance(locs, list):
            for loc in locs:
                rows.append(f"- `{loc['module']}` (`{loc['file']}:{loc['line']}`)")
        rows.append("")

    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect duplicate stdlib definitions across modules")
    ap.add_argument("--stdlib-root", default="stdlib", help="Path to stdlib root")
    ap.add_argument("--include-private", action="store_true", help="Include private names that start with _")
    ap.add_argument("--json-out", default="", help="Write JSON report to this path")
    ap.add_argument("--md-out", default="", help="Write markdown report to this path")
    ap.add_argument("--fail-on-duplicates", action="store_true", help="Exit non-zero when duplicates are found")
    args = ap.parse_args()

    stdlib_root = Path(args.stdlib_root).resolve()
    decls = _collect_decls(stdlib_root, include_private=bool(args.include_private))
    report = _duplicate_report(decls)
    markdown = _to_markdown(report, include_private=bool(args.include_private))

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(markdown, encoding="utf-8")

    print(markdown)
    if args.fail_on_duplicates and int(report["duplicate_count"]) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
