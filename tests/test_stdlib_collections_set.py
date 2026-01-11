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


def test_stdlib_collections_set_basic():
    src = """use collections.set

fn f() -> Int = do:
  let s0 = setEmpty()
  let s1 = setAdd(s0, "a")
  let s2 = setAdd(s1, "b")
  let s3 = setAdd(s2, "a")
  return match setHas(s3, "a"):
    true -> match setHas(setRemove(s3, "a"), "a"):
      true -> 0
      false -> setSize(s3)
    false -> 0

run()
"""
    _check(src)
