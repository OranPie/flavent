from flavent import ast
from flavent.lexer import lex
from flavent.parser import parse_program
from flavent.token import TokenKind


def test_parse_accepts_fullwidth_block_and_call_punctuation():
    src = """type Event.Start = {}
sector main：
  on Event.Start －＞ do：
    stop（）
run（）
"""
    prog = parse_program(lex("test.flv", src))
    assert prog.run is not None
    sec = next(it for it in prog.items if isinstance(it, ast.SectorDecl))
    assert sec.name.name == "main"


def test_parse_accepts_fullwidth_comma_in_call():
    src = """fn add(x: Int, y: Int) -> Int = x + y
fn g() = add(1，2)
run()
"""
    prog = parse_program(lex("test.flv", src))
    fn = next(it for it in prog.items if isinstance(it, ast.FnDecl) and it.name.name == "g")
    assert isinstance(fn.body, ast.BodyExpr)
    assert isinstance(fn.body.expr, ast.CallExpr)
    assert len(fn.body.expr.args) == 2


def test_lexer_slasheq_tokenization_stays_stable():
    toks = [t for t in lex("test.flv", "x /= 2\n") if t.kind not in (TokenKind.NL, TokenKind.EOF)]
    assert [t.kind for t in toks] == [TokenKind.IDENT, TokenKind.SLASHEQ, TokenKind.INT]
