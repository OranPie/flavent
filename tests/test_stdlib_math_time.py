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


def test_stdlib_math_and_time_api():
    src = """use math
use time

type Event.X = {}

sector s:
  on Event.X -> do:
    let a = minInt(1, 2)
    let b = maxInt(1, 2)
    let c = absInt(0 - 3)
    let _clamp = clampInt(5, 0, 3)

    let d0 = durationSeconds(1)
    let d1 = durationMillis(500)
    let d2 = durationAdd(d0, d1)

    let t0 = rpc time.nowInstant()
    let _elapsed = rpc time.elapsedSince(t0)
    call time.sleepDuration(d2)

    stop()

run()
"""
    _check(src)
