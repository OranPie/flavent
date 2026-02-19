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


def test_stdlib_url_module_typechecks():
    src = """use url
use collections.list

fn f() -> Int = do:
  let q = queryBuild(Cons({ key = "a b", value = "x+y" }, Cons({ key = "k", value = "v" }, Nil)))
  let p = queryParse(q)
  let e = encodeComponent("a b+c")
  let d = decodeComponent(e)
  let q2 = queryEncode("a b")
  let d2 = queryDecode(q2)
  return 0

run()
"""
    _check(src)


def test_stdlib_url_invalid_decode_typechecks():
    src = """use url

fn f() -> Result[Str, Str] = decodeComponent("%GG")

run()
"""
    _check(src)
