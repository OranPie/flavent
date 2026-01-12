from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.lower import lower_resolved
from flavent.typecheck import check_program
from flavent.runtime import Bridge, run_hir_program


@dataclass(frozen=True)
class RunResult:
    ok: bool
    error: str | None = None


def discover_cases(src: str) -> list[str]:
    out: list[str] = []
    for line in src.splitlines():
        s = line.strip()
        if s.startswith('test "') and s.endswith('-> do:'):
            # test "NAME" -> do:
            try:
                name = s[len('test "') : s.index('"', len('test "'))]
                out.append(name)
            except Exception:
                continue
    return out


def _rewrite_case(src: str, case_name: str) -> str:
    lines = src.splitlines(keepends=True)
    hdr = f'test "{case_name}" -> do:'

    # Find header line.
    start = None
    for i, line in enumerate(lines):
        if line.strip() == hdr:
            start = i
            break
    if start is None:
        raise RuntimeError(f"flvtest case not found: {case_name}")

    # Preamble = everything before first test header.
    first_test = None
    for i, line in enumerate(lines):
        if line.strip().startswith('test "') and line.strip().endswith('-> do:'):
            first_test = i
            break
    if first_test is None:
        raise RuntimeError("no test cases found")
    preamble = "".join(lines[:first_test])

    # Extract block until next header.
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].strip().startswith('test "') and lines[j].strip().endswith('-> do:'):
            end = j
            break

    block_lines = lines[start + 1 : end]
    # Determine indentation of the block.
    base_indent = None
    for bl in block_lines:
        if bl.strip() == "":
            continue
        base_indent = len(bl) - len(bl.lstrip(" "))
        break
    if base_indent is None:
        base_indent = 0

    stripped: list[str] = []
    for bl in block_lines:
        if bl.strip() == "":
            stripped.append("\n" if bl.endswith("\n") else "")
        else:
            stripped.append(bl[base_indent:])
    body = "".join(("    " + l if l.strip() != "" else l) for l in stripped)

    return (
        preamble
        + "\n"
        + "type Event.Test = {}\n\n"
        + "sector main:\n"
        + "  on Event.Test -> do:\n"
        + body
        + ("\n" if not body.endswith("\n") else "")
        + "    stop()\n\n"
        + "run()\n"
    )


def run_file(
    path: str | Path,
    *,
    entry_event_type: str = "Event.Test",
    bridge: Bridge | None = None,
    case: str | None = None,
) -> RunResult:
    p = Path(path)
    src = p.read_text(encoding="utf-8")
    if case is not None:
        src = _rewrite_case(src, case)

    try:
        prog = parse_program(lex(str(p), src))
        res = resolve_program_with_stdlib(prog, use_stdlib=True)
        hir = lower_resolved(res)
        check_program(hir, res)
        run_hir_program(hir, res, entry_event_type=entry_event_type, bridge=bridge)
        return RunResult(ok=True)
    except Exception as e:
        return RunResult(ok=False, error=str(e))
