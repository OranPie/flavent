from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .span import Span


class TokenKind(Enum):
    EOF = auto()
    NL = auto()
    INDENT = auto()
    DEDENT = auto()

    IDENT = auto()
    INT = auto()
    FLOAT = auto()
    STR = auto()
    BYTES = auto()
    BOOL = auto()

    KW_TYPE = auto()
    KW_CONST = auto()
    KW_LET = auto()
    KW_NEED = auto()
    KW_FN = auto()
    KW_MIXIN = auto()
    KW_USE = auto()
    KW_RESOLVE = auto()
    KW_PATTERN = auto()
    KW_PREFER = auto()
    KW_OVER = auto()
    KW_INTO = auto()
    KW_SECTOR = auto()
    KW_ON = auto()
    KW_WHEN = auto()
    KW_DO = auto()
    KW_MATCH = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_FOR = auto()
    KW_IN = auto()
    KW_RETURN = auto()
    KW_EMIT = auto()
    KW_AWAIT = auto()
    KW_CALL = auto()
    KW_RPC = auto()
    KW_PROCEED = auto()
    KW_AROUND = auto()
    KW_OK = auto()
    KW_ERR = auto()
    KW_SOME = auto()
    KW_NONE = auto()
    KW_RUN = auto()
    KW_STOP = auto()
    KW_YIELD = auto()
    KW_AND = auto()
    KW_OR = auto()
    KW_NOT = auto()
    KW_AS = auto()

    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    COMMA = auto()
    DOT = auto()
    COLON = auto()
    ARROW = auto()  # ->
    AT = auto()  # @

    BAR = auto()  # |

    EQ = auto()  # =
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    STARSTAR = auto()
    SLASH = auto()

    EQEQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()

    PLUSEQ = auto()
    MINUSEQ = auto()
    STAREQ = auto()
    SLASHEQ = auto()

    PIPE = auto()  # |>
    QMARK = auto()  # ?


KEYWORDS: dict[str, TokenKind] = {
    "type": TokenKind.KW_TYPE,
    "const": TokenKind.KW_CONST,
    "let": TokenKind.KW_LET,
    "need": TokenKind.KW_NEED,
    "fn": TokenKind.KW_FN,
    "mixin": TokenKind.KW_MIXIN,
    "use": TokenKind.KW_USE,
    "resolve": TokenKind.KW_RESOLVE,
    "pattern": TokenKind.KW_PATTERN,
    "prefer": TokenKind.KW_PREFER,
    "over": TokenKind.KW_OVER,
    "into": TokenKind.KW_INTO,
    "sector": TokenKind.KW_SECTOR,
    "on": TokenKind.KW_ON,
    "when": TokenKind.KW_WHEN,
    "do": TokenKind.KW_DO,
    "match": TokenKind.KW_MATCH,
    "if": TokenKind.KW_IF,
    "else": TokenKind.KW_ELSE,
    "for": TokenKind.KW_FOR,
    "in": TokenKind.KW_IN,
    "return": TokenKind.KW_RETURN,
    "emit": TokenKind.KW_EMIT,
    "await": TokenKind.KW_AWAIT,
    "call": TokenKind.KW_CALL,
    "rpc": TokenKind.KW_RPC,
    "proceed": TokenKind.KW_PROCEED,
    "around": TokenKind.KW_AROUND,
    "Ok": TokenKind.KW_OK,
    "Err": TokenKind.KW_ERR,
    "Some": TokenKind.KW_SOME,
    "None": TokenKind.KW_NONE,
    "run": TokenKind.KW_RUN,
    "stop": TokenKind.KW_STOP,
    "yield": TokenKind.KW_YIELD,
    "and": TokenKind.KW_AND,
    "or": TokenKind.KW_OR,
    "not": TokenKind.KW_NOT,
    "as": TokenKind.KW_AS,
    "true": TokenKind.BOOL,
    "false": TokenKind.BOOL,
}


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    text: str
    span: Span
