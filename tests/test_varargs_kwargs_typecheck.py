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


def test_varargs_kwargs_typecheck():
    src = """use collections.list
use collections.map

fn f[T](a: T, *xs: List[T], **kw: Map[Str, T]) -> T = a

fn g() -> Int = do:
  let m = mapPut(mapEmpty(), \"k\", 1)
  let x = f(1)
  let y = f(1, 2, 3)
  let z = f(1, x=2)
  let w = f(1, *Cons(2, Cons(3, Nil)))
  let u = f(1, **m)
  return x + y + z + w + u

run()
"""
    _check(src)
