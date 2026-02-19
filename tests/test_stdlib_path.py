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


def test_stdlib_path_module_typechecks():
    src = """use path
use collections.list

fn f() -> Int = do:
  let n = pathNormalize("./a/../b//c")
  let j = pathJoin("a/b", "c.txt")
  let ja = pathJoinAll(Cons("a", Cons("b", Cons("c.txt", Nil))))
  let b = pathBase("/tmp/x.txt")
  let d = pathDir("/tmp/x.txt")
  let e = pathExt("/tmp/x.txt")
  let s = pathStem("/tmp/x.txt")
  return 0

run()
"""
    _check(src)
