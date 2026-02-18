from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flavent.bridge_audit import audit_bridge_usage
from flavent.lexer import lex
from flavent.lower import lower_resolved
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.token import TokenKind
from flavent.typecheck import check_program
from flvtest.runner import _rewrite_case, discover_cases


def _collect_bridge_surface(bridge_file: Path) -> tuple[list[str], list[str]]:
    pure: list[str] = []
    effectful: list[str] = []
    in_sector = False

    for raw in bridge_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("sector _bridge_python:"):
            in_sector = True
            continue
        if not line.startswith("fn "):
            continue
        name = line.split("fn ", 1)[1].split("(", 1)[0].strip()
        if in_sector:
            effectful.append(name)
        else:
            pure.append(name)

    return sorted(pure), sorted(effectful)


def _scan_stdlib_symbol_references(stdlib_root: Path, bridge_symbols: set[str]) -> dict[str, Any]:
    per_symbol: Counter[str] = Counter()
    per_module: Counter[str] = Counter()
    symbol_to_modules: dict[str, set[str]] = defaultdict(set)

    for path in sorted(stdlib_root.rglob("*.flv")):
        if path.name == "_bridge_python.flv":
            continue

        rel = path.relative_to(REPO_ROOT).as_posix()
        module = path.relative_to(stdlib_root).as_posix().removesuffix(".flv")
        src = path.read_text(encoding="utf-8")
        toks = lex(rel, src)

        counts = Counter(
            tok.text
            for tok in toks
            if tok.kind == TokenKind.IDENT and tok.text in bridge_symbols
        )
        if not counts:
            continue

        for sym, n in counts.items():
            per_symbol[sym] += n
            per_module[module] += n
            symbol_to_modules[sym].add(module)

    return {
        "total_references": int(sum(per_symbol.values())),
        "distinct_symbols_referenced": int(len(per_symbol)),
        "distinct_modules_referencing": int(len(per_module)),
        "per_symbol": dict(sorted(per_symbol.items(), key=lambda kv: (-kv[1], kv[0]))),
        "per_module": dict(sorted(per_module.items(), key=lambda kv: (-kv[1], kv[0]))),
        "symbol_to_modules": {
            sym: sorted(mods)
            for sym, mods in sorted(symbol_to_modules.items(), key=lambda kv: kv[0])
        },
    }


def _collect_runtime_test_bridge_usage(tests_flv_root: Path) -> dict[str, Any]:
    total_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    file_counts: dict[str, Counter[str]] = {}
    programs_analyzed = 0
    failures: list[dict[str, str]] = []

    def _audit_program(label: str, src: str, source_file: str) -> None:
        nonlocal programs_analyzed
        try:
            prog = parse_program(lex(label, src))
            res = resolve_program_with_stdlib(prog, use_stdlib=True)
            hir = lower_resolved(res)
            check_program(hir, res)
            report = audit_bridge_usage(hir, res)
            counts = Counter(report.get("counts", {}))
        except Exception as exc:  # pragma: no cover - snapshot should continue
            failures.append({"file": label, "error": str(exc)})
            return

        programs_analyzed += 1
        dst = file_counts.setdefault(source_file, Counter())
        dst.update(counts)
        total_counts.update(counts)
        for key, n in counts.items():
            kind_counts[key.split(":", 1)[0]] += n

    for path in sorted(tests_flv_root.glob("*.flv")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        raw = path.read_text(encoding="utf-8")
        cases = discover_cases(raw)
        if not cases:
            _audit_program(rel, raw, rel)
            continue
        for case in cases:
            rewritten = _rewrite_case(raw, case)
            _audit_program(f"{rel}::{case}", rewritten, rel)

    files: list[dict[str, Any]] = []
    for file_name, counts in file_counts.items():
        files.append(
            {
                "file": file_name,
                "bridge_calls": int(sum(counts.values())),
                "counts": dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))),
            }
        )
    files.sort(key=lambda row: (-row["bridge_calls"], row["file"]))

    return {
        "programs_analyzed": programs_analyzed,
        "files_analyzed": len(files),
        "files_failed": len(failures),
        "total_bridge_calls": int(sum(total_counts.values())),
        "kind_counts": dict(sorted(kind_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "counts": dict(sorted(total_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "files": files,
        "failures": failures,
    }


def build_report() -> dict[str, Any]:
    stdlib_root = REPO_ROOT / "stdlib"
    bridge_file = stdlib_root / "_bridge_python.flv"
    tests_flv_root = REPO_ROOT / "tests_flv"

    pure, effectful = _collect_bridge_surface(bridge_file)
    bridge_symbols = set(pure) | set(effectful)

    return {
        "date": time.strftime("%Y-%m-%d"),
        "bridge_surface": {
            "pure_count": len(pure),
            "effectful_count": len(effectful),
            "total_count": len(pure) + len(effectful),
            "pure_symbols": pure,
            "effectful_symbols": effectful,
        },
        "stdlib_references": _scan_stdlib_symbol_references(stdlib_root, bridge_symbols),
        "tests_flv_runtime_baseline": _collect_runtime_test_bridge_usage(tests_flv_root),
        "notes": [
            "stdlib_references are static token counts from stdlib/*.flv (excluding _bridge_python.flv).",
            "tests_flv_runtime_baseline uses compiler bridge audit counts after resolve/lower/typecheck.",
        ],
    }


def _fmt_top_rows(data: dict[str, int], top_n: int) -> list[str]:
    rows: list[str] = []
    for i, (name, n) in enumerate(data.items()):
        if i >= top_n:
            break
        rows.append(f"- `{name}`: `{n}`")
    return rows


def format_markdown(report: dict[str, Any]) -> str:
    surface = report["bridge_surface"]
    stdlib = report["stdlib_references"]
    tests = report["tests_flv_runtime_baseline"]

    lines: list[str] = []
    lines.append("# Bridge Usage Baseline")
    lines.append("")
    lines.append(f"Date: {report['date']}")
    lines.append("")
    lines.append("## Bridge Surface")
    lines.append(f"- Pure bridge primitives: `{surface['pure_count']}`")
    lines.append(f"- Effectful bridge primitives: `{surface['effectful_count']}`")
    lines.append(f"- Total bridge symbols: `{surface['total_count']}`")
    lines.append("")
    lines.append("## Stdlib Bridge Symbol References (Static)")
    lines.append(f"- Total symbol references: `{stdlib['total_references']}`")
    lines.append(f"- Distinct bridge symbols referenced: `{stdlib['distinct_symbols_referenced']}`")
    lines.append(f"- Distinct stdlib modules referencing bridge symbols: `{stdlib['distinct_modules_referencing']}`")
    lines.append("- Top referenced bridge symbols:")
    lines.extend(_fmt_top_rows(stdlib["per_symbol"], top_n=8))
    lines.append("- Top stdlib modules by bridge references:")
    lines.extend(_fmt_top_rows(stdlib["per_module"], top_n=8))
    lines.append("")
    lines.append("## tests_flv Bridge Call Baseline")
    lines.append(f"- Programs analyzed (expanded test cases): `{tests['programs_analyzed']}`")
    lines.append(f"- Files analyzed: `{tests['files_analyzed']}`")
    lines.append(f"- Files failed to analyze: `{tests['files_failed']}`")
    lines.append(f"- Total audited bridge calls: `{tests['total_bridge_calls']}`")
    lines.append("- Bridge call kinds:")
    lines.extend(_fmt_top_rows(tests["kind_counts"], top_n=6))
    lines.append("- Top audited calls:")
    lines.extend(_fmt_top_rows(tests["counts"], top_n=10))
    lines.append("")
    lines.append("## Notes")
    for note in report["notes"]:
        lines.append(f"- {note}")

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Capture bridge usage baseline snapshot")
    ap.add_argument("--json-out", default="", help="Write JSON report to this path")
    ap.add_argument("--md-out", default="", help="Write markdown report to this path")
    args = ap.parse_args()

    report = build_report()
    markdown = format_markdown(report)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(markdown, encoding="utf-8")

    print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
