from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program_with_stdlib
from flavent.lower import lower_resolved
from flavent.typecheck import check_program


def _check(src: str):
    prog = parse_program(lex("test.flv", src))
    res = resolve_program_with_stdlib(prog, use_stdlib=True)
    hir = lower_resolved(res)
    check_program(hir, res)


def test_stdlib_datetime_module_typechecks():
    src = """use datetime

fn f() -> Int = do:
  let d = makeDate(2024, 2, 29)
  let t = makeTime(12, 34, 56, 789)
  let dt = makeDateTime(d, t)
  let s1 = formatDate(d)
  let s2 = formatTime(t)
  let s3 = formatDateTime(dt)
  let p1 = parseDate(s1)
  let p2 = parseTime(s2)
  let p3 = parseDateTime(s3)
  return 0

run()
"""
    _check(src)
