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


def test_stdlib_process_module_typechecks():
    src = """use process
use collections.list

fn f() -> Int = do:
  let s0 = processSpec("echo", Cons("hello", Nil))
  let s1 = processWithCwd(s0, "/tmp")
  let s2 = processWithEnv(s1, "A", "1")
  let s3 = processWithExitCode(s2, 0)
  let s4 = processWithStdout(s3, "ok")
  let s5 = processWithStderr(s4, "")
  let _vr = processValidate(s5)
  let _sp = processSpawn(s5)
  let _rn = processRun(s5)
  return 0

run()
"""
    _check(src)
