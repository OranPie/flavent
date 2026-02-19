from __future__ import annotations

from dataclasses import dataclass

from .diagnostics import LexError
from .span import Span
from .token import KEYWORDS, Token, TokenKind


@dataclass(slots=True)
class _State:
    file: str
    src: str
    i: int = 0
    line: int = 1
    col: int = 1

    def eof(self) -> bool:
        return self.i >= len(self.src)

    def peek(self, n: int = 0) -> str:
        j = self.i + n
        if j < 0 or j >= len(self.src):
            return ""
        return self.src[j]

    def advance(self, n: int = 1) -> str:
        s = self.src[self.i : self.i + n]
        for ch in s:
            self.i += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        return s

    def span_at(self, start_i: int, start_line: int, start_col: int) -> Span:
        return Span(file=self.file, start=start_i, end=self.i, line=start_line, col=start_col)


def lex(file: str, src: str) -> list[Token]:
    if not src.endswith("\n"):
        src = src + "\n"

    st = _State(file=file, src=src)
    tokens: list[Token] = []

    indent_stack: list[int] = [0]
    bracket_depth = 0

    at_line_start = True
    expects_indent = False
    line_ends_with_colon = False

    def err(msg: str, start_i: int | None = None, start_line: int | None = None, start_col: int | None = None) -> None:
        if start_i is None:
            start_i = st.i
            start_line = st.line
            start_col = st.col
        raise LexError(msg, Span(file=file, start=start_i, end=max(start_i + 1, st.i), line=start_line or 1, col=start_col or 1))

    def emit(kind: TokenKind, text: str, start_i: int, start_line: int, start_col: int) -> None:
        nonlocal line_ends_with_colon
        tok = Token(kind=kind, text=text, span=Span(file=file, start=start_i, end=st.i, line=start_line, col=start_col))
        tokens.append(tok)
        if kind not in (TokenKind.NL, TokenKind.INDENT, TokenKind.DEDENT):
            line_ends_with_colon = kind == TokenKind.COLON

    def skip_line_comment() -> None:
        while not st.eof() and st.peek() != "\n":
            if st.peek() == "\t":
                err("Tab is not allowed")
            st.advance(1)

    def skip_block_comment() -> None:
        depth = 0
        while True:
            if st.peek() == "/" and st.peek(1) == "*":
                depth += 1
                st.advance(2)
                continue
            if st.peek() == "*" and st.peek(1) == "/":
                depth -= 1
                st.advance(2)
                if depth == 0:
                    return
                continue
            if st.eof():
                err("Unterminated block comment")
            if st.peek() == "\t":
                err("Tab is not allowed")
            st.advance(1)

    def handle_line_start() -> bool:
        nonlocal at_line_start, expects_indent

        if not (at_line_start and bracket_depth == 0):
            return False

        start_i = st.i
        k = 0
        while st.peek() == " ":
            st.advance(1)
            k += 1
        if st.peek() == "\t":
            err("Tab is not allowed")

        # Comment-only / blank lines do not affect indentation stack (REF2#1.2).
        while True:
            if st.peek() == "/" and st.peek(1) == "/":
                skip_line_comment()
                break
            if st.peek() == "/" and st.peek(1) == "*":
                skip_block_comment()
                continue
            break

        if st.peek() == "\n":
            st.advance(1)
            at_line_start = True
            return True

        if expects_indent:
            if k <= indent_stack[-1]:
                err("IndentationError: expected indent", start_i, st.line, 1)
            indent_stack.append(k)
            tokens.append(Token(TokenKind.INDENT, "", Span(file=file, start=start_i, end=start_i, line=st.line, col=1)))
            expects_indent = False
        else:
            if k == indent_stack[-1]:
                pass
            elif k > indent_stack[-1]:
                err("IndentationError: unexpected indent", start_i, st.line, 1)
            else:
                while indent_stack and k < indent_stack[-1]:
                    indent_stack.pop()
                    tokens.append(Token(TokenKind.DEDENT, "", Span(file=file, start=start_i, end=start_i, line=st.line, col=1)))
                if not indent_stack or k != indent_stack[-1]:
                    err("IndentationError: unaligned dedent", start_i, st.line, 1)

        at_line_start = False
        return False

    while not st.eof():
        if st.peek() == "\t":
            err("Tab is not allowed")

        if handle_line_start():
            continue

        ch = st.peek()
        if ch in " \r":
            st.advance(1)
            continue

        if ch == "\n":
            start_i, start_line, start_col = st.i, st.line, st.col
            st.advance(1)
            if bracket_depth == 0:
                emit(TokenKind.NL, "\n", start_i, start_line, start_col)
                if line_ends_with_colon:
                    expects_indent = True
                at_line_start = True
            continue

        if ch == "/" and st.peek(1) == "/":
            skip_line_comment()
            continue

        if ch == "/" and st.peek(1) == "*":
            skip_block_comment()
            continue

        start_i, start_line, start_col = st.i, st.line, st.col

        if ch == "b" and st.peek(1) == '"':
            st.advance(1)
            _lex_string(st, emit, start_i, start_line, start_col, bytes_prefix=True)
            continue

        if ch.isalpha() or ch == "_":
            ident = ""
            while True:
                c = st.peek()
                if c.isalnum() or c == "_":
                    ident += st.advance(1)
                else:
                    break
            kind = KEYWORDS.get(ident, TokenKind.IDENT)
            if kind == TokenKind.BOOL:
                emit(TokenKind.BOOL, ident, start_i, start_line, start_col)
            else:
                emit(kind, ident, start_i, start_line, start_col)
            continue

        if ch.isdigit():
            def read_digits_with_underscores(*, allowed: str) -> str:
                s = ""
                prev_us = False
                while True:
                    c = st.peek()
                    if c == "_":
                        if not s or prev_us:
                            err("Invalid numeric literal", start_i, start_line, start_col)
                        prev_us = True
                        s += st.advance(1)
                        continue
                    if c and c in allowed:
                        prev_us = False
                        s += st.advance(1)
                        continue
                    break
                if s.endswith("_"):
                    err("Invalid numeric literal", start_i, start_line, start_col)
                return s

            # Base-prefixed int: 0x / 0o / 0b
            if st.peek() == "0" and st.peek(1) in ("x", "o", "b"):
                st.advance(2)
                base_ch = src[start_i + 1] if start_i + 1 < len(src) else ""
                if base_ch == "x":
                    digs = read_digits_with_underscores(allowed="0123456789abcdefABCDEF")
                    if not digs:
                        err("Invalid numeric literal", start_i, start_line, start_col)
                    val = int(digs.replace("_", ""), 16)
                    emit(TokenKind.INT, str(val), start_i, start_line, start_col)
                    continue
                if base_ch == "o":
                    digs = read_digits_with_underscores(allowed="01234567")
                    if not digs:
                        err("Invalid numeric literal", start_i, start_line, start_col)
                    val = int(digs.replace("_", ""), 8)
                    emit(TokenKind.INT, str(val), start_i, start_line, start_col)
                    continue
                if base_ch == "b":
                    digs = read_digits_with_underscores(allowed="01")
                    if not digs:
                        err("Invalid numeric literal", start_i, start_line, start_col)
                    val = int(digs.replace("_", ""), 2)
                    emit(TokenKind.INT, str(val), start_i, start_line, start_col)
                    continue

            # Decimal int/float with underscores
            int_part = read_digits_with_underscores(allowed="0123456789")
            if st.peek() == "." and st.peek(1).isdigit():
                st.advance(1)
                frac_part = read_digits_with_underscores(allowed="0123456789")
                emit(TokenKind.FLOAT, f"{int_part.replace('_','')}.{frac_part.replace('_','')}", start_i, start_line, start_col)
            else:
                emit(TokenKind.INT, int_part.replace("_", ""), start_i, start_line, start_col)
            continue

        if ch == '"':
            _lex_string(st, emit, start_i, start_line, start_col, bytes_prefix=False)
            continue

        two = ch + st.peek(1)
        if two == "->":
            st.advance(2)
            emit(TokenKind.ARROW, "->", start_i, start_line, start_col)
            continue
        if two == "+=":
            st.advance(2)
            emit(TokenKind.PLUSEQ, "+=", start_i, start_line, start_col)
            continue
        if two == "-=":
            st.advance(2)
            emit(TokenKind.MINUSEQ, "-=", start_i, start_line, start_col)
            continue
        if two == "*=":
            st.advance(2)
            emit(TokenKind.STAREQ, "*=", start_i, start_line, start_col)
            continue
        if two == "**":
            st.advance(2)
            emit(TokenKind.STARSTAR, "**", start_i, start_line, start_col)
            continue
        if two == "/=":
            st.advance(2)
            emit(TokenKind.SLASHEQ, "/=", start_i, start_line, start_col)
            continue
        if two == "==":
            st.advance(2)
            emit(TokenKind.EQEQ, "==", start_i, start_line, start_col)
            continue
        if two == "!=":
            st.advance(2)
            emit(TokenKind.NEQ, "!=", start_i, start_line, start_col)
            continue
        if two == "<=":
            st.advance(2)
            emit(TokenKind.LTE, "<=", start_i, start_line, start_col)
            continue
        if two == ">=":
            st.advance(2)
            emit(TokenKind.GTE, ">=", start_i, start_line, start_col)
            continue
        if two == "|>":
            st.advance(2)
            emit(TokenKind.PIPE, "|>", start_i, start_line, start_col)
            continue

        if ch == "(":
            st.advance(1)
            bracket_depth += 1
            emit(TokenKind.LPAREN, "(", start_i, start_line, start_col)
            continue
        if ch == ")":
            st.advance(1)
            bracket_depth = max(0, bracket_depth - 1)
            emit(TokenKind.RPAREN, ")", start_i, start_line, start_col)
            continue
        if ch == "[":
            st.advance(1)
            bracket_depth += 1
            emit(TokenKind.LBRACKET, "[", start_i, start_line, start_col)
            continue
        if ch == "]":
            st.advance(1)
            bracket_depth = max(0, bracket_depth - 1)
            emit(TokenKind.RBRACKET, "]", start_i, start_line, start_col)
            continue
        if ch == "{":
            st.advance(1)
            bracket_depth += 1
            emit(TokenKind.LBRACE, "{", start_i, start_line, start_col)
            continue
        if ch == "}":
            st.advance(1)
            bracket_depth = max(0, bracket_depth - 1)
            emit(TokenKind.RBRACE, "}", start_i, start_line, start_col)
            continue

        if ch == ",":
            st.advance(1)
            emit(TokenKind.COMMA, ",", start_i, start_line, start_col)
            continue
        if ch == ".":
            st.advance(1)
            emit(TokenKind.DOT, ".", start_i, start_line, start_col)
            continue
        if ch == ":":
            st.advance(1)
            emit(TokenKind.COLON, ":", start_i, start_line, start_col)
            continue
        if ch == "@":
            st.advance(1)
            emit(TokenKind.AT, "@", start_i, start_line, start_col)
            continue
        if ch == "|":
            st.advance(1)
            emit(TokenKind.BAR, "|", start_i, start_line, start_col)
            continue
        if ch == "=":
            st.advance(1)
            emit(TokenKind.EQ, "=", start_i, start_line, start_col)
            continue
        if ch == "+":
            st.advance(1)
            emit(TokenKind.PLUS, "+", start_i, start_line, start_col)
            continue
        if ch == "-":
            st.advance(1)
            emit(TokenKind.MINUS, "-", start_i, start_line, start_col)
            continue
        if ch == "*":
            st.advance(1)
            emit(TokenKind.STAR, "*", start_i, start_line, start_col)
            continue
        if ch == "/":
            st.advance(1)
            emit(TokenKind.SLASH, "/", start_i, start_line, start_col)
            continue
        if ch == "<":
            st.advance(1)
            emit(TokenKind.LT, "<", start_i, start_line, start_col)
            continue
        if ch == ">":
            st.advance(1)
            emit(TokenKind.GT, ">", start_i, start_line, start_col)
            continue
        if ch == "?":
            st.advance(1)
            emit(TokenKind.QMARK, "?", start_i, start_line, start_col)
            continue

        err(f"Unexpected character: {ch!r}", start_i, start_line, start_col)

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token(TokenKind.DEDENT, "", Span(file=file, start=st.i, end=st.i, line=st.line, col=st.col)))

    tokens.append(Token(TokenKind.EOF, "", Span(file=file, start=st.i, end=st.i, line=st.line, col=st.col)))
    return tokens


def _lex_string(
    st: _State,
    emit,
    start_i: int,
    start_line: int,
    start_col: int,
    *,
    bytes_prefix: bool,
) -> None:
    literal_kind = "bytes" if bytes_prefix else "string"

    def _err_here(msg: str) -> None:
        raise LexError(msg, Span(file=st.file, start=start_i, end=max(start_i + 1, st.i), line=start_line, col=start_col))

    def _err_at_current(msg: str, width: int = 1) -> None:
        raise LexError(
            msg,
            Span(
                file=st.file,
                start=st.i,
                end=max(st.i + width, st.i + 1),
                line=st.line,
                col=st.col,
            ),
        )

    def _append_char(out: str, ch: str) -> str:
        if bytes_prefix and ord(ch) > 255:
            _err_here("Bytes literal supports only byte-range characters")
        return out + ch

    def _read_hex_byte() -> str:
        h1 = st.peek()
        h2 = st.peek(1)
        hex_digits = "0123456789abcdefABCDEF"
        if not h1 or not h2 or h1 not in hex_digits or h2 not in hex_digits:
            _err_at_current(
                f"Invalid hex escape in {literal_kind} literal: expected two hex digits after \\x",
                width=2,
            )
        st.advance(2)
        return chr(int(h1 + h2, 16))

    st.advance(1)  # opening quote
    out = ""
    esc_map = {
        '"': '"',
        "\\": "\\",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "0": "\0",
        "a": "\a",
        "b": "\b",
        "f": "\f",
        "v": "\v",
    }
    while True:
        if st.eof():
            raise LexError(
                f"Unterminated {literal_kind} literal",
                Span(file=st.file, start=start_i, end=st.i, line=start_line, col=start_col),
            )
        ch = st.peek()
        if ch == "\n":
            raise LexError(
                f"Unterminated {literal_kind} literal",
                Span(file=st.file, start=start_i, end=st.i, line=start_line, col=start_col),
            )
        if ch == '"':
            st.advance(1)
            break
        if ch == "\\":
            st.advance(1)
            esc = st.peek()
            if esc == "" or esc == "\n":
                raise LexError(
                    f"Unterminated {literal_kind} literal",
                    Span(file=st.file, start=start_i, end=st.i, line=start_line, col=start_col),
                )
            if esc == "x":
                st.advance(1)
                out = _append_char(out, _read_hex_byte())
            elif esc in esc_map:
                st.advance(1)
                out = _append_char(out, esc_map[esc])
            else:
                # Keep unknown escapes as-is for compatibility (e.g. regex "\\d").
                out = _append_char(out, "\\")
                out = _append_char(out, st.advance(1))
            continue
        out = _append_char(out, st.advance(1))

    kind = TokenKind.BYTES if bytes_prefix else TokenKind.STR
    emit(kind, out, start_i, start_line, start_col)
