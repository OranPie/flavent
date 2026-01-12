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
  let ch = rngChoice(s.rng, s.value)
  let bs = rngBytes(ch.rng, 16)
  let u = rngUniform(bs.rng, 0.0, 1.0)
  let smp = rngSample(u.rng, s.value, 2)
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
    let _rl = rpc file.readLines("/tmp/x")
    let _wl = rpc file.writeLines("/tmp/x", Cons("a", Cons("b", Nil)))
    let _al = rpc file.appendLines("/tmp/x", Cons("c", Nil))
    stop()

run()
"""
    _check(src)
