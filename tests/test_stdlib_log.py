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


def test_stdlib_log_module_typechecks():
    src = """use log

fn f() -> Int = do:
  let d0 = logDefault()
  let d1 = logNamed("app")
  let d2 = logWithName(d1, "core")
  let d3 = logWithMinLevel(d2, logLevelDebug())
  let _e0 = logShouldEmit(d3, logLevelInfo())
  let r = logRecord(logLevelWarn(), d3, "warn")
  let _s = logFormat(r)
  let _p = logPrepare(d3, logLevelTrace(), "skip")
  return 0

run()
"""
    _check(src)
