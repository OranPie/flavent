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


def test_stdlib_cliargs_module_typechecks():
    src = """use cliargs
use collections.list

fn f() -> Int = do:
  let argv = Cons("--verbose", Cons("--port=8080", Cons("--name", Cons("alice", Cons("-xz", Cons("file", Nil))))))
  let parsed = cliParse(argv)
  let e = cliEmpty()
  return 0

run()
"""
    _check(src)
