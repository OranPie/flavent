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


def test_stdlib_env_module_typechecks():
    src = """use env
use collections.list

fn f() -> Int = do:
  let e0 = envEmpty()
  let _a = envSet(e0, "A", "1")
  let _b = envGet(e0, "A")
  let _c = envGetOr(e0, "B", "x")
  let _d = envHas(e0, "A")
  let _e = envList(e0)
  let _f = envUnset(e0, "A")
  let _g = envClear(e0)
  return 0

run()
"""
    _check(src)
