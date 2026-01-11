from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.ast import PipeExpr


def test_pipe_parses_as_pipeexpr():
    src = """fn f(x: Int) = x\nfn g(x: Int) = x\nfn h(x: Int) = x\nfn t(x: Int) = x |> f |> g(x) |> h\n"""
    prog = parse_program(lex("test.flv", src))
    fn_t = [it for it in prog.items if getattr(it, "__class__", None).__name__ == "FnDecl" and it.name.name == "t"][0]
    body_expr = fn_t.body.expr
    assert isinstance(body_expr, PipeExpr)
    assert len(body_expr.stages) == 3
