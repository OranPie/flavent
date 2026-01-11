from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program
from flavent.lower import lower_resolved


def test_lower_try_suffix_result():
    src = """fn foo() -> Result[Int, Str] = Ok(1)
fn bar() -> Result[Int, Str] = foo()?
"""
    res = resolve_program(parse_program(lex("test.flv", src)))
    hir = lower_resolved(res)

    from flavent.hir import MatchStmt

    # bar should contain a MatchStmt due to ? lowering
    bar_fn = [f for f in hir.fns if any(s.name == "bar" for s in res.symbols if s.id == f.sym)][0]
    assert any(isinstance(st, MatchStmt) for st in bar_fn.body.stmts)


def test_lower_try_suffix_handler_abort():
    src = """type Event.X = {}
fn foo() -> Result[Int, Str] = Ok(1)

on Event.X -> do:
  let x = foo()?
  stop()

run()
"""
    res = resolve_program(parse_program(lex("test.flv", src)))
    hir = lower_resolved(res)

    from flavent.hir import AbortHandlerStmt, MatchStmt

    sec = [s for s in hir.sectors if True][0]
    h = sec.handlers[0]
    match = next(st for st in h.body.stmts if isinstance(st, MatchStmt))
    assert any(isinstance(st, AbortHandlerStmt) for st in match.arms[1].body.stmts)
