from flavent.lexer import lex
from flavent.token import TokenKind


def test_indent_dedent_basic():
    src = """sector main:\n  on Event.Start -> do:\n    stop()\n\nrun()\n"""
    toks = lex("test.flv", src)
    kinds = [t.kind for t in toks]

    assert TokenKind.INDENT in kinds
    assert TokenKind.DEDENT in kinds


def test_nested_block_comment_ignored():
    src = """sector main:\n  /* a /* nested */ b */\n  on Event.Start -> do:\n    stop()\n\nrun()\n"""
    toks = lex("test.flv", src)
    assert toks[-1].kind == TokenKind.EOF
