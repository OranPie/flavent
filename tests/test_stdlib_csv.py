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


def test_stdlib_csv_module_typechecks():
    src = """use csv
use collections.list

fn f() -> Int = do:
  let opts = { delimiter = ";", quote = "'" }
  let row = csvParseLineWith("a;'b;c';d", opts)
  let out = csvStringifyLineWith(Cons("a", Cons("b;c", Cons("d", Nil))), opts)
  let all = csvParse("a,b\\n1,2")
  let txt = csvStringify(Cons(Cons("x", Cons("y", Nil)), Nil))
  return 0

run()
"""
    _check(src)


def test_stdlib_csv_error_typechecks():
    src = """use csv
use collections.list

fn f() -> Result[List[Str], Str] = csvParseLine("\\\"oops")

run()
"""
    _check(src)
