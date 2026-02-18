from __future__ import annotations

import pytest

from flavent.lexer import lex
from flavent.lower import lower_resolved
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.runtime import Bridge, run_hir_program
from flavent.typecheck import check_program


class _NoBridge(Bridge):
    def call(self, name: str, args: list[object]) -> object:
        raise RuntimeError(f"bridge call not allowed: {name}")


def _compile(src: str):
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)
    return hir, res


def _run_ok(body: str, *, uses: str) -> None:
    if not body.endswith("\n"):
        body += "\n"
    src = (
        "use flvtest\n"
        + uses
        + "\n"
        + "type Event.Test = {}\n\n"
        + "sector main:\n"
        + "  on Event.Test -> do:\n"
        + body
        + "    stop()\n\n"
        + "run()\n"
    )
    hir, res = _compile(src)
    run_hir_program(hir, res, entry_event_type="Event.Test", bridge=_NoBridge())


def _flv_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("a)", "unmatched )"),
        ("[ab", "unterminated class"),
        ("(ab", "unterminated group"),
    ],
)
def test_regex_compile_checked_error_messages(pattern: str, expected: str):
    body = (
        f"    let e = errOr(compileChecked({_flv_str(pattern)}), \"\")\n"
        f"    assertEq(e, {_flv_str(expected)})?\n"
    )
    _run_ok(body, uses="use regex\nuse std.result\n")


def test_regex_anchor_behavior_and_spans():
    body = """    let r = compile("^ab$")
    assertTrue(isMatch(r, "ab"))?
    assertTrue(not isMatch(r, "zab"))?
    assertEq(findFirstSpan(r, "ab"), Some({ start = 0, end = 2 }))?
    assertEq(findFirstSpan(r, "zab"), None)?
"""
    _run_ok(body, uses="use regex\n")


def test_regex_zero_length_progress_in_find_and_replace_all():
    body = """    let spans = findAllSpans(compile("a*"), "aa")
    assertEq(length(spans), 2)?
    assertEq(get(spans, 0), Some({ start = 0, end = 2 }))?
    assertEq(get(spans, 1), Some({ start = 2, end = 2 }))?
    assertEq(replaceAll(compile("a*"), "aa", "X"), "XX")?
    assertEq(replaceAll(compile("^"), "aa", "X"), "Xaa")?
"""
    _run_ok(body, uses="use regex\nuse collections.list\n")


def test_regex_replace_tokens_and_capture_order():
    body = """    assertEq(replace(compile("(ab)(cd)"), "zzabcdyy", "<$0,$1,$2,$$>"), "zz<abcd,ab,cd,$>yy")?
    assertEq(findFirstCaptures(compile("(ab)(cd)"), "zzabcdyy"), Some(Cons("abcd", Cons("ab", Cons("cd", Nil)))))?
"""
    _run_ok(body, uses="use regex\n")
