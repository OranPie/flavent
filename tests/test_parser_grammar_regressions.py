import pytest

from flavent import ast
from flavent.diagnostics import ParseError
from flavent.lexer import lex
from flavent.parser import parse_program


def _parse_fn_expr(expr_src: str):
    src = f"fn f() = {expr_src}\n"
    prog = parse_program(lex("test.flv", src))
    fn = next(it for it in prog.items if isinstance(it, ast.FnDecl))
    assert isinstance(fn.body, ast.BodyExpr)
    return fn.body.expr


def test_precedence_mul_over_add():
    expr = _parse_fn_expr("1 + 2 * 3")
    assert isinstance(expr, ast.BinaryExpr)
    assert expr.op == "+"
    assert isinstance(expr.right, ast.BinaryExpr)
    assert expr.right.op == "*"


def test_precedence_not_over_and():
    expr = _parse_fn_expr("not a and b")
    assert isinstance(expr, ast.BinaryExpr)
    assert expr.op == "and"
    assert isinstance(expr.left, ast.UnaryExpr)
    assert expr.left.op == "not"


def test_pipe_wraps_binary_head():
    expr = _parse_fn_expr("1 + 2 |> f")
    assert isinstance(expr, ast.PipeExpr)
    assert isinstance(expr.head, ast.BinaryExpr)
    assert expr.head.op == "+"
    assert len(expr.stages) == 1


def test_call_allows_trailing_comma():
    expr = _parse_fn_expr("f(1, 2,)")
    assert isinstance(expr, ast.CallExpr)
    assert len(expr.args) == 2


def test_tuple_allows_trailing_comma():
    expr = _parse_fn_expr("(1,)")
    assert isinstance(expr, ast.TupleLitExpr)
    assert len(expr.items) == 1

    expr2 = _parse_fn_expr("(1, 2,)")
    assert isinstance(expr2, ast.TupleLitExpr)
    assert len(expr2.items) == 2


def test_rpc_call_proceed_allow_trailing_comma():
    expr = _parse_fn_expr("rpc s.f(1,)")
    assert isinstance(expr, ast.RpcExpr)
    assert len(expr.args) == 1

    expr2 = _parse_fn_expr("call s.f(1,)")
    assert isinstance(expr2, ast.CallSectorExpr)
    assert len(expr2.args) == 1

    expr3 = _parse_fn_expr("proceed(1,)")
    assert isinstance(expr3, ast.ProceedExpr)
    assert len(expr3.args) == 1


def test_event_pattern_allows_trailing_comma():
    src = """sector main:
  on Event.X(1,) -> 0
run()
"""
    prog = parse_program(lex("test.flv", src))
    sec = next(it for it in prog.items if isinstance(it, ast.SectorDecl))
    handler = next(it for it in sec.items if isinstance(it, ast.OnHandler))
    assert isinstance(handler.event, ast.EventCall)
    assert len(handler.event.args) == 1


def test_parse_error_expected_token_hint():
    src = "fn f() = (1 + 2\n"
    with pytest.raises(ParseError, match="hint: missing"):
        parse_program(lex("test.flv", src))


def test_parse_error_hints_flvtest_top_level():
    src = 'test "case" -> do:\n  stop()\n'
    with pytest.raises(ParseError, match="flvtest syntax"):
        parse_program(lex("test.flv", src))
