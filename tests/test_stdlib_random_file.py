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


def test_stdlib_random_typecheck():
    src = """use random
use collections.list

fn f() -> Int = do:
  let r0 = rngSeed(123)
  let o1 = rngNextU32(r0)
  let o2 = rngNextInt(o1.rng, 10, 20)
  let o3 = rngNextFloat01(o2.rng)
  let o4 = rngBool(o3.rng)
  let s = rngShuffle(o4.rng, Cons(1, Cons(2, Cons(3, Nil))))
  return o2.value + o1.value + length(s.value)

run()
"""
    _check(src)


def test_stdlib_file_typecheck():
    src = """use file

type Event.Test = {}

sector main:
  on Event.Test -> do:
    let _e = rpc file.exists("/tmp")
    let _l = rpc file.listDir("/tmp")
    stop()

run()
"""
    _check(src)
