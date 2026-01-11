import pytest

from flavent.lexer import lex
from flavent.token import TokenKind


def _ints(src: str):
    toks = lex("test.flv", src)
    return [t for t in toks if t.kind in (TokenKind.INT, TokenKind.FLOAT)]


def test_lexer_int_bases_and_underscores():
    toks = _ints("0xff 0b1010 0o77 1_000 12_34\n")
    assert [t.kind for t in toks] == [TokenKind.INT] * 5
    assert [t.text for t in toks] == ["255", "10", "63", "1000", "1234"]


def test_lexer_float_underscores():
    toks = _ints("1_000.5_0\n")
    assert len(toks) == 1
    assert toks[0].kind == TokenKind.FLOAT
    assert toks[0].text == "1000.50"


def test_lexer_reject_bad_underscores():
    with pytest.raises(Exception):
        lex("test.flv", "1__2\n")
    with pytest.raises(Exception):
        lex("test.flv", "1_\n")
    with pytest.raises(Exception):
        lex("test.flv", "0x_1\n")
    with pytest.raises(Exception):
        lex("test.flv", "0x\n")
