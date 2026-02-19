import pytest

from flavent.diagnostics import LexError
from flavent.lexer import lex
from flavent.token import TokenKind


def _single_token(src: str, kind: TokenKind):
    toks = [t for t in lex("test.flv", src) if t.kind == kind]
    assert len(toks) == 1
    return toks[0]


def test_lexer_string_ascii_escapes():
    tok = _single_token(r'"\"\\\n\r\t\0\a\b\f\v"' + "\n", TokenKind.STR)
    assert tok.text == '"\\\n\r\t\0\a\b\f\v'


def test_lexer_hex_escapes_for_string_and_bytes():
    s_tok = _single_token(r'"\x41\x42\x43"' + "\n", TokenKind.STR)
    b_tok = _single_token(r'b"\x41\x80\x0a"' + "\n", TokenKind.BYTES)
    assert s_tok.text == "ABC"
    assert b_tok.text == "A" + chr(128) + "\n"


def test_lexer_rejects_invalid_hex_escape():
    with pytest.raises(LexError, match="Invalid hex escape"):
        lex("test.flv", r'"\x4"' + "\n")
    with pytest.raises(LexError, match="Invalid hex escape"):
        lex("test.flv", r'b"\xzz"' + "\n")


def test_lexer_invalid_hex_escape_diagnostic_has_hint():
    with pytest.raises(LexError, match=r"expected two hex digits after \\x"):
        lex("test.flv", r'"\x"' + "\n")
    with pytest.raises(LexError, match=r"bytes literal"):
        lex("test.flv", r'b"\xg1"' + "\n")


def test_lexer_rejects_non_byte_chars_in_bytes_literal():
    with pytest.raises(LexError, match="byte-range"):
        lex("test.flv", 'b"😀"\n')


def test_lexer_reports_unterminated_literal_kind():
    with pytest.raises(LexError, match="Unterminated string literal"):
        lex("test.flv", '"abc\n')
    with pytest.raises(LexError, match="Unterminated bytes literal"):
        lex("test.flv", 'b"abc\n')


def test_lexer_unknown_escapes_remain_compatible():
    tok = _single_token(r'"\q\d"' + "\n", TokenKind.STR)
    assert tok.text == r"\q\d"
