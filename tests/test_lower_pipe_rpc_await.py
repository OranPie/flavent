from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.resolve import resolve_program
from flavent.lower import lower_resolved
from flavent import ast


def test_lower_pipe_to_calls():
    src = """fn f(x: Int) -> Int = x
fn g(x: Int, y: Int) -> Int = x
fn h(x: Int) -> Int = x
fn t(x: Int) -> Int = x |> f |> g(1) |> h
"""
    res = resolve_program(parse_program(lex("test.flv", src)))
    hir = lower_resolved(res)

    # Find fn t
    t_decl = next(it for it in res.program.items if isinstance(it, ast.FnDecl) and it.name.name == "t")
    t_sym = res.ident_to_symbol[id(t_decl.name)]
    t_fn = [f for f in hir.fns if f.sym == t_sym][0]
    # Should have ReturnStmt(Call(Call(Call(...)))) and no pipe node exists in HIR.
    from flavent.hir import CallExpr, ReturnStmt

    ret = [s for s in t_fn.body.stmts if isinstance(s, ReturnStmt)][0]
    assert isinstance(ret.expr, CallExpr)


def test_lower_rpc_call_await():
    src = """type Event.X = {}
sector s:
  fn ping() -> Unit = 0
  on Event.X -> do:
    let a = await Event.X
    let b = rpc s.ping()
    call s.ping()
    stop()

run()
"""
    res = resolve_program(parse_program(lex("test.flv", src)))
    hir = lower_resolved(res)

    from flavent.hir import AwaitEventExpr, RpcCallExpr, LetStmt

    sec = hir.sectors[0]
    h = sec.handlers[0]
    lets = [st for st in h.body.stmts if isinstance(st, LetStmt)]
    assert any(isinstance(ls.expr, AwaitEventExpr) for ls in lets)
    assert any(isinstance(ls.expr, RpcCallExpr) and ls.expr.awaitResult for ls in lets)
