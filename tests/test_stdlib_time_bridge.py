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


def test_stdlib_time_monotonic_api_typechecks():
    src = """use time

type Event.X = {}

sector s:
  on Event.X -> do:
    let a = rpc time.nowNanos()
    let b = rpc time.monoMillis()
    let c = rpc time.monoNanos()
    call time.sleepMillis(1)
    stop()

run()
"""
    _check(src)
