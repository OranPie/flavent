from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import ast
from .diagnostics import ParseError
from .span import Span
from .token import Token, TokenKind


_TOKEN_SYMBOLS: dict[TokenKind, str] = {
    TokenKind.LPAREN: "(",
    TokenKind.RPAREN: ")",
    TokenKind.LBRACE: "{",
    TokenKind.RBRACE: "}",
    TokenKind.LBRACKET: "[",
    TokenKind.RBRACKET: "]",
    TokenKind.COMMA: ",",
    TokenKind.DOT: ".",
    TokenKind.COLON: ":",
    TokenKind.ARROW: "->",
    TokenKind.AT: "@",
    TokenKind.BAR: "|",
    TokenKind.EQ: "=",
    TokenKind.PLUS: "+",
    TokenKind.MINUS: "-",
    TokenKind.STAR: "*",
    TokenKind.STARSTAR: "**",
    TokenKind.SLASH: "/",
    TokenKind.EQEQ: "==",
    TokenKind.NEQ: "!=",
    TokenKind.LT: "<",
    TokenKind.LTE: "<=",
    TokenKind.GT: ">",
    TokenKind.GTE: ">=",
    TokenKind.PIPE: "|>",
    TokenKind.QMARK: "?",
}


def _expected_token_label(kind: TokenKind) -> str:
    if kind == TokenKind.NL:
        return "newline"
    if kind == TokenKind.INDENT:
        return "indentation"
    if kind == TokenKind.DEDENT:
        return "dedentation"
    if kind == TokenKind.EOF:
        return "end of file"
    sym = _TOKEN_SYMBOLS.get(kind)
    if sym is not None:
        return repr(sym)
    if kind.name.startswith("KW_"):
        return f"keyword {kind.name[3:].lower()!r}"
    return kind.name


def _describe_token(tok: Token) -> str:
    if tok.kind == TokenKind.NL:
        return "newline"
    if tok.kind == TokenKind.EOF:
        return "end of file"
    if tok.kind == TokenKind.INDENT:
        return "indentation"
    if tok.kind == TokenKind.DEDENT:
        return "dedentation"
    sym = _TOKEN_SYMBOLS.get(tok.kind)
    if sym is not None:
        return f"{sym!r}"
    if tok.kind == TokenKind.IDENT:
        return f"identifier {tok.text!r}"
    if tok.kind in (TokenKind.INT, TokenKind.FLOAT, TokenKind.STR, TokenKind.BYTES, TokenKind.BOOL):
        return f"{tok.kind.name.lower()} {tok.text!r}"
    if tok.kind.name.startswith("KW_"):
        return f"keyword {tok.text!r}"
    if tok.text:
        return f"{tok.kind.name}({tok.text!r})"
    return tok.kind.name


@dataclass(slots=True)
class _Cursor:
    tokens: list[Token]
    i: int = 0

    def peek(self, n: int = 0) -> Token:
        j = self.i + n
        if j < 0:
            j = 0
        if j >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[j]

    def at(self, kind: TokenKind) -> bool:
        return self.peek().kind == kind

    def advance(self) -> Token:
        t = self.peek()
        if self.i < len(self.tokens) - 1:
            self.i += 1
        return t

    def expect(self, kind: TokenKind, msg: str | None = None) -> Token:
        t = self.peek()
        if t.kind != kind:
            got = _describe_token(t)
            base = msg or f"Expected {_expected_token_label(kind)}"
            hints: list[str] = []
            if kind == TokenKind.COLON:
                hints.append("missing ':' before an indented block")
            elif kind == TokenKind.RPAREN:
                hints.append("missing ')' to close grouped expression or call")
            elif kind == TokenKind.RBRACKET:
                hints.append("missing ']' to close index or type arguments")
            elif kind == TokenKind.ARROW:
                hints.append("expected '->' before handler or match arm body")
            if t.kind == TokenKind.EOF and kind in (TokenKind.RPAREN, TokenKind.RBRACKET, TokenKind.RBRACE):
                hints.append("reached end of file while closing delimiters")
            if t.kind == TokenKind.NL and kind in (TokenKind.RPAREN, TokenKind.RBRACKET, TokenKind.RBRACE):
                hints.append("a closing delimiter may be missing before newline")
            full = f"{base}, got {got}"
            if hints:
                full = f"{full}; hint: {'; '.join(hints)}"
            raise ParseError(full, t.span)
        return self.advance()

    def match(self, kind: TokenKind) -> Optional[Token]:
        if self.at(kind):
            return self.advance()
        return None


def parse_program(tokens: list[Token]) -> ast.Program:
    cur = _Cursor(tokens)
    items: list[ast.TopItem] = []
    run: ast.RunStmt | None = None

    start_span = cur.peek().span

    while not cur.at(TokenKind.EOF):
        if cur.at(TokenKind.NL):
            cur.advance()
            continue
        if cur.at(TokenKind.DEDENT):
            cur.advance()
            continue
        if cur.at(TokenKind.KW_RUN):
            run = _parse_run(cur)
            while cur.at(TokenKind.NL):
                cur.advance()
            cur.expect(TokenKind.EOF, "run() must be last in Phase 1 parser")
            break
        items.append(_parse_top_item(cur))

    end_span = cur.peek().span
    span = start_span.merge(end_span)
    return ast.Program(items=items, run=run, span=span)


def _parse_run(cur: _Cursor) -> ast.RunStmt:
    kw = cur.expect(TokenKind.KW_RUN)
    cur.expect(TokenKind.LPAREN)
    cur.expect(TokenKind.RPAREN)
    return ast.RunStmt(span=kw.span.merge(cur.peek(-1).span))


def _parse_top_item(cur: _Cursor) -> ast.TopItem:
    if cur.at(TokenKind.KW_TYPE):
        return _parse_type_decl(cur)
    if cur.at(TokenKind.KW_CONST):
        return _parse_const_decl(cur)
    if cur.at(TokenKind.KW_LET):
        return _parse_let_decl(cur)
    if cur.at(TokenKind.KW_NEED):
        return _parse_need_decl(cur)
    if cur.at(TokenKind.KW_FN):
        return _parse_fn_decl(cur)
    if cur.at(TokenKind.KW_PATTERN):
        return _parse_pattern_decl(cur)
    if cur.at(TokenKind.KW_MIXIN):
        return _parse_mixin_decl(cur)
    if cur.at(TokenKind.KW_USE):
        # `use mixin Foo v1` (mixin system) vs `use std.option` (module system).
        if cur.peek(1).kind == TokenKind.KW_MIXIN:
            return _parse_use_mixin(cur)
        return _parse_use(cur)
    if cur.at(TokenKind.KW_RESOLVE):
        return _parse_resolve_mixin(cur)
    if cur.at(TokenKind.KW_SECTOR):
        return _parse_sector_decl(cur)
    if cur.at(TokenKind.KW_ON):
        return _parse_on_handler(cur)

    t = cur.peek()
    if t.kind == TokenKind.IDENT and t.text == "test":
        raise ParseError(
            "Unexpected top-level token: IDENT; hint: `test \"name\" -> do:` is flvtest syntax and must run via flvtest/pytest",
            t.span,
        )
    raise ParseError(f"Unexpected top-level token: {t.kind.name}", t.span)


def _parse_ident(cur: _Cursor) -> ast.Ident:
    t = cur.peek()
    if t.kind in (TokenKind.IDENT, TokenKind.KW_OK, TokenKind.KW_ERR, TokenKind.KW_SOME, TokenKind.KW_NONE):
        cur.advance()
        return ast.Ident(name=t.text, span=t.span)
    raise ParseError(f"Expected identifier, got {t.kind.name}", t.span)


def _parse_version_token(cur: _Cursor) -> int:
    t = cur.expect(TokenKind.IDENT, "Expected version like v1")
    if not t.text.startswith("v") or not t.text[1:].isdigit():
        raise ParseError("Expected version like v1", t.span)
    return int(t.text[1:])


def _parse_qualified_name(cur: _Cursor) -> ast.QualifiedName:
    first = _parse_ident(cur)
    parts = [first]
    while cur.match(TokenKind.DOT):
        parts.append(_parse_ident(cur))
    span = parts[0].span.merge(parts[-1].span)
    return ast.QualifiedName(parts=parts, span=span)


def _parse_type_ref(cur: _Cursor) -> ast.TypeRef:
    if cur.match(TokenKind.LPAREN):
        inner = _parse_type_ref(cur)
        r = cur.expect(TokenKind.RPAREN)
        span = inner.span.merge(r.span)
        return ast.TypeParen(inner=inner, span=span)
    name = _parse_qualified_name(cur)
    args: list[ast.TypeRef] | None = None
    if cur.match(TokenKind.LBRACKET):
        args = []
        args.append(_parse_type_ref(cur))
        while cur.match(TokenKind.COMMA):
            args.append(_parse_type_ref(cur))
        rb = cur.expect(TokenKind.RBRACKET)
        span = name.span.merge(rb.span)
        return ast.TypeName(name=name, args=args, span=span)
    return ast.TypeName(name=name, args=None, span=name.span)


def _parse_type_decl(cur: _Cursor) -> ast.TypeDecl:
    kw = cur.expect(TokenKind.KW_TYPE)
    name = _parse_qualified_name(cur)
    params: list[ast.Ident] | None = None
    if cur.match(TokenKind.LBRACKET):
        params = []
        params.append(_parse_ident(cur))
        while cur.match(TokenKind.COMMA):
            params.append(_parse_ident(cur))
        cur.expect(TokenKind.RBRACKET)
    cur.expect(TokenKind.EQ, "Expected '=' after type declaration")

    if cur.at(TokenKind.LBRACE):
        rhs = _parse_record_type(cur)
    else:
        # Sum type uses | ; alias falls back to TypeRef.
        rhs = _parse_sum_or_alias(cur)

    span = kw.span.merge(rhs.span)
    return ast.TypeDecl(name=name, params=params, rhs=rhs, span=span)


def _parse_record_type(cur: _Cursor) -> ast.RecordType:
    l = cur.expect(TokenKind.LBRACE)
    fields: list[ast.FieldDecl] = []
    if not cur.at(TokenKind.RBRACE):
        fields.append(_parse_field_decl(cur))
        while cur.match(TokenKind.COMMA):
            if cur.at(TokenKind.RBRACE):
                break
            fields.append(_parse_field_decl(cur))
    r = cur.expect(TokenKind.RBRACE)
    span = l.span.merge(r.span)
    return ast.RecordType(fields=fields, span=span)


def _parse_field_decl(cur: _Cursor) -> ast.FieldDecl:
    name = _parse_ident(cur)
    cur.expect(TokenKind.COLON)
    ty = _parse_type_ref(cur)
    span = name.span.merge(ty.span)
    return ast.FieldDecl(name=name, ty=ty, span=span)


def _parse_sum_or_alias(cur: _Cursor) -> ast.TypeRhs:
    # Alias looks like a TypeRef. Sum type uses `|` between variants.
    # We try to parse as Variant first, but fall back to alias if it doesn't match.
    save = cur.i
    try:
        v0 = _parse_variant_decl(cur)
        if cur.match(TokenKind.BAR):
            variants = [v0]
            while True:
                variants.append(_parse_variant_decl(cur))
                if not cur.match(TokenKind.BAR):
                    break
            span = variants[0].span.merge(variants[-1].span)
            return ast.SumType(variants=variants, span=span)
        # single variant without BAR is not a valid sum type rhs; treat as alias.
        raise Exception("not_sum")
    except Exception:
        cur.i = save
        alias = _parse_type_ref(cur)
        return ast.TypeAlias(target=alias, span=alias.span)


def _parse_variant_decl(cur: _Cursor) -> ast.VariantDecl:
    name = _parse_ident(cur)
    payload: list[ast.TypeRef] | None = None
    if cur.match(TokenKind.LPAREN):
        payload = []
        if not cur.at(TokenKind.RPAREN):
            payload.append(_parse_type_ref(cur))
            while cur.match(TokenKind.COMMA):
                payload.append(_parse_type_ref(cur))
        rp = cur.expect(TokenKind.RPAREN)
        span = name.span.merge(rp.span)
        return ast.VariantDecl(name=name, payload=payload, span=span)
    return ast.VariantDecl(name=name, payload=None, span=name.span)


def _parse_const_decl(cur: _Cursor) -> ast.ConstDecl:
    kw = cur.expect(TokenKind.KW_CONST)
    name = _parse_ident(cur)
    cur.expect(TokenKind.EQ, "Expected '=' after const name")
    value = _parse_expr(cur)
    span = kw.span.merge(value.span)
    return ast.ConstDecl(name=name, value=value, span=span)


def _parse_let_decl(cur: _Cursor) -> ast.LetDecl:
    kw = cur.expect(TokenKind.KW_LET)
    name = _parse_ident(cur)
    cur.expect(TokenKind.EQ, "Expected '=' after let name")
    value = _parse_expr(cur)
    span = kw.span.merge(value.span)
    return ast.LetDecl(name=name, value=value, span=span)


def _parse_need_decl(cur: _Cursor) -> ast.NeedDecl:
    kw = cur.expect(TokenKind.KW_NEED)
    attrs: ast.NeedAttr | None = None
    if cur.match(TokenKind.LPAREN):
        cache = None
        cache_fail = None
        while not cur.at(TokenKind.RPAREN):
            key = _parse_ident(cur)
            cur.expect(TokenKind.EQ)
            val = cur.expect(TokenKind.STR)
            if key.name == "cache":
                cache = val.text
            if key.name == "cacheFail":
                cache_fail = val.text
            if not cur.match(TokenKind.COMMA):
                break
        rp = cur.expect(TokenKind.RPAREN)
        attrs = ast.NeedAttr(cache=cache, cacheFail=cache_fail, span=kw.span.merge(rp.span))
    name = _parse_ident(cur)
    cur.expect(TokenKind.EQ, "Expected '=' after need name")
    value = _parse_expr(cur)
    span = kw.span.merge(value.span)
    return ast.NeedDecl(name=name, attrs=attrs, value=value, span=span)


def _parse_param(cur: _Cursor) -> ast.ParamDecl:
    kind = "normal"
    if cur.match(TokenKind.STAR):
        kind = "varargs"
    elif cur.match(TokenKind.STARSTAR):
        kind = "varkw"
    name = _parse_ident(cur)
    cur.expect(TokenKind.COLON)
    ty = _parse_type_ref(cur)
    return ast.ParamDecl(name=name, ty=ty, kind=kind, span=name.span.merge(ty.span))


def _parse_fn_decl(cur: _Cursor) -> ast.FnDecl:
    kw = cur.expect(TokenKind.KW_FN)
    sector_qual: ast.Ident | None = None
    if cur.match(TokenKind.AT):
        sector_qual = _parse_ident(cur)
    name = _parse_ident(cur)
    type_params: list[ast.Ident] | None = None
    if cur.match(TokenKind.LBRACKET):
        type_params = []
        type_params.append(_parse_ident(cur))
        while cur.match(TokenKind.COMMA):
            type_params.append(_parse_ident(cur))
        cur.expect(TokenKind.RBRACKET)
    cur.expect(TokenKind.LPAREN)
    params: list[ast.ParamDecl] = []
    if not cur.at(TokenKind.RPAREN):
        params.append(_parse_param(cur))
        while cur.match(TokenKind.COMMA):
            params.append(_parse_param(cur))
    rp = cur.expect(TokenKind.RPAREN)

    ret_ty: ast.TypeRef | None = None
    if cur.match(TokenKind.ARROW):
        ret_ty = _parse_type_ref(cur)

    cur.expect(TokenKind.EQ, "Expected '=' after function signature (use '= expr' or '= do:')")
    body = _parse_fn_body(cur)
    span = kw.span.merge(body.span)
    return ast.FnDecl(name=name, sectorQual=sector_qual, typeParams=type_params, params=params, retType=ret_ty, body=body, span=span)


def _parse_fn_body(cur: _Cursor) -> ast.FnBody:
    if cur.at(TokenKind.KW_DO):
        kw = cur.advance()
        block = _parse_block_after_colon(cur, kw.span)
        return ast.BodyDo(block=block, span=kw.span.merge(block.span))
    expr = _parse_expr(cur)
    return ast.BodyExpr(expr=expr, span=expr.span)


def _parse_block_after_colon(cur: _Cursor, start_span: Span) -> ast.Block:
    cur.expect(TokenKind.COLON, "Expected ':' before block body")
    cur.expect(TokenKind.NL, "Expected newline after ':' before block body (single-line blocks are not supported)")
    cur.expect(TokenKind.INDENT, "Expected indented block body")
    stmts: list[ast.Stmt] = []
    while not cur.at(TokenKind.DEDENT) and not cur.at(TokenKind.EOF):
        if cur.at(TokenKind.NL):
            cur.advance()
            continue
        stmts.append(_parse_stmt(cur))
        if cur.at(TokenKind.NL):
            cur.advance()
    ded = cur.expect(TokenKind.DEDENT)
    span = start_span.merge(ded.span)
    return ast.Block(stmts=stmts, span=span)


def _parse_sector_decl(cur: _Cursor) -> ast.SectorDecl:
    kw = cur.expect(TokenKind.KW_SECTOR)
    name = _parse_ident(cur)
    cur.expect(TokenKind.COLON, "Expected ':' after sector name")
    cur.expect(TokenKind.NL, "Expected newline after sector header")
    cur.expect(TokenKind.INDENT, "Expected indented sector body")
    items: list[ast.TopItem] = []
    while not cur.at(TokenKind.DEDENT) and not cur.at(TokenKind.EOF):
        if cur.at(TokenKind.NL):
            cur.advance()
            continue
        if cur.at(TokenKind.KW_LET):
            items.append(_parse_let_decl(cur))
        elif cur.at(TokenKind.KW_NEED):
            items.append(_parse_need_decl(cur))
        elif cur.at(TokenKind.KW_FN):
            items.append(_parse_fn_decl(cur))
        elif cur.at(TokenKind.KW_ON):
            items.append(_parse_on_handler(cur))
        else:
            bad = cur.peek()
            if bad.kind == TokenKind.IDENT and cur.peek(1).kind == TokenKind.EQ:
                raise ParseError(
                    "Unexpected sector item: assignment at sector scope; hint: use `let name = ...` (assignments belong in handler/fn bodies)",
                    bad.span,
                )
            raise ParseError(
                "Unexpected sector item; expected one of: let, need, fn, on",
                bad.span,
            )
        if cur.at(TokenKind.NL):
            cur.advance()
    ded = cur.expect(TokenKind.DEDENT)
    span = kw.span.merge(ded.span)
    return ast.SectorDecl(name=name, supervisor=None, items=items, span=span)


def _parse_event_pattern(cur: _Cursor) -> ast.EventPattern:
    name = _parse_qualified_name(cur)
    if cur.match(TokenKind.LPAREN):
        args: list[ast.Expr] = []
        if not cur.at(TokenKind.RPAREN):
            args.append(_parse_expr(cur))
            while cur.match(TokenKind.COMMA):
                if cur.at(TokenKind.RPAREN):
                    break
                args.append(_parse_expr(cur))
        rp = cur.expect(TokenKind.RPAREN)
        span = name.span.merge(rp.span)
        return ast.EventCall(name=name, args=args, span=span)
    return ast.EventType(name=name, span=name.span)


def _parse_on_handler(cur: _Cursor) -> ast.OnHandler:
    kw = cur.expect(TokenKind.KW_ON)
    event = _parse_event_pattern(cur)
    binder: ast.Ident | None = None
    when: ast.Expr | None = None
    if cur.match(TokenKind.KW_AS):
        binder = _parse_ident(cur)
    if cur.match(TokenKind.KW_WHEN):
        when = _parse_expr(cur)
    cur.expect(TokenKind.ARROW)
    if cur.at(TokenKind.KW_DO):
        kw_do = cur.advance()
        block = _parse_block_after_colon(cur, kw_do.span)
        body = ast.HandlerDo(block=block, span=kw_do.span.merge(block.span))
    else:
        expr = _parse_expr(cur)
        body = ast.HandlerExpr(expr=expr, span=expr.span)

    span = kw.span.merge(body.span)
    return ast.OnHandler(event=event, binder=binder, when=when, body=body, span=span)


def _parse_mixin_decl(cur: _Cursor) -> ast.MixinDecl:
    kw = cur.expect(TokenKind.KW_MIXIN)
    name = _parse_qualified_name(cur)
    version = _parse_version_token(cur)
    cur.expect(TokenKind.KW_INTO)
    if cur.match(TokenKind.KW_SECTOR):
        target_name = _parse_ident(cur)
        target = ast.MixinTargetSector(name=target_name, span=target_name.span)
    else:
        # Allow explicit `into type T`.
        cur.match(TokenKind.KW_TYPE)
        ty = _parse_qualified_name(cur)
        target = ast.MixinTargetType(name=ty, span=ty.span)

    cur.expect(TokenKind.COLON, "Expected ':' after mixin header")
    cur.expect(TokenKind.NL, "Expected newline after mixin header")
    cur.expect(TokenKind.INDENT, "Expected indented mixin body")
    items: list[ast.MixinItem] = []
    while not cur.at(TokenKind.DEDENT) and not cur.at(TokenKind.EOF):
        if cur.at(TokenKind.NL):
            cur.advance()
            continue
        if cur.at(TokenKind.KW_PATTERN):
            items.append(_parse_pattern_decl(cur))
            continue
        if cur.at(TokenKind.KW_FN):
            items.append(_parse_mixin_add(cur))
            continue
        if cur.at(TokenKind.KW_AROUND):
            items.append(_parse_mixin_around(cur))
            continue
        if cur.at(TokenKind.IDENT) and cur.peek().text == "hook":
            items.append(_parse_mixin_hook(cur))
            continue
        # For type-target mixins, allow adding record fields as `name: Type`.
        if cur.at(TokenKind.IDENT) and cur.peek(1).kind == TokenKind.COLON:
            items.append(_parse_mixin_field_add(cur))
            continue
        bad = cur.peek()
        if bad.kind == TokenKind.IDENT and cur.peek(1).kind == TokenKind.EQ:
            raise ParseError(
                "Unexpected mixin item: assignment at mixin scope; hint: use `fn ... = ...` or `name: Type` (type mixins)",
                bad.span,
            )
        if bad.kind in (TokenKind.KW_LET, TokenKind.KW_NEED, TokenKind.KW_ON):
            raise ParseError(
                "Unexpected mixin item: declarations like let/need/on are not valid inside mixins (use fn/around/hook/pattern)",
                bad.span,
            )
        if isinstance(target, ast.MixinTargetSector):
            raise ParseError(
                "Expected mixin item; sector mixins support: pattern, fn, around, hook",
                bad.span,
            )
        raise ParseError(
            "Expected mixin item; type mixins support: pattern, fn, around, hook, field: Type",
            bad.span,
        )

        if cur.at(TokenKind.NL):
            cur.advance()
    ded = cur.expect(TokenKind.DEDENT)
    span = kw.span.merge(ded.span)
    return ast.MixinDecl(name=name, version=version, target=target, items=items, span=span)


def _parse_mixin_add(cur: _Cursor) -> ast.MixinFnAdd:
    kw = cur.expect(TokenKind.KW_FN)
    name = _parse_ident(cur)
    cur.expect(TokenKind.LPAREN)
    params: list[ast.ParamDecl] = []
    if not cur.at(TokenKind.RPAREN):
        params.append(_parse_param(cur))
        while cur.match(TokenKind.COMMA):
            params.append(_parse_param(cur))
    rp = cur.expect(TokenKind.RPAREN)
    ret_ty: ast.TypeRef | None = None
    if cur.match(TokenKind.ARROW):
        ret_ty = _parse_type_ref(cur)
    sig_span = kw.span.merge(rp.span)
    sig = ast.FnSignature(name=name, params=params, retType=ret_ty, span=sig_span)
    cur.expect(TokenKind.EQ, "Expected '=' after mixin function signature (use '= expr' or '= do:')")
    body = _parse_fn_body(cur)
    span = kw.span.merge(body.span)
    return ast.MixinFnAdd(sig=sig, body=body, span=span)


def _parse_mixin_around(cur: _Cursor) -> ast.MixinAround:
    kw = cur.expect(TokenKind.KW_AROUND)
    cur.expect(TokenKind.KW_FN)
    name = _parse_ident(cur)
    cur.expect(TokenKind.LPAREN)
    params: list[ast.ParamDecl] = []
    if not cur.at(TokenKind.RPAREN):
        params.append(_parse_param(cur))
        while cur.match(TokenKind.COMMA):
            params.append(_parse_param(cur))
    rp = cur.expect(TokenKind.RPAREN)
    ret_ty: ast.TypeRef | None = None
    if cur.match(TokenKind.ARROW):
        ret_ty = _parse_type_ref(cur)
    sig_span = kw.span.merge(rp.span)
    sig = ast.FnSignature(name=name, params=params, retType=ret_ty, span=sig_span)
    block = _parse_block_after_colon(cur, kw.span)
    span = kw.span.merge(block.span)
    return ast.MixinAround(sig=sig, block=block, span=span)


def _parse_mixin_field_add(cur: _Cursor) -> ast.MixinFieldAdd:
    name = _parse_ident(cur)
    cur.expect(TokenKind.COLON)
    ty = _parse_type_ref(cur)
    span = name.span.merge(ty.span)
    return ast.MixinFieldAdd(name=name, ty=ty, span=span)


def _parse_hook_with_options(cur: _Cursor) -> dict[str, str]:
    opts: dict[str, str] = {}
    if not (cur.at(TokenKind.IDENT) and cur.peek().text == "with"):
        return opts

    cur.advance()
    cur.expect(TokenKind.LPAREN, "Expected '(' after hook with")
    while not cur.at(TokenKind.RPAREN):
        if cur.at(TokenKind.KW_CONST):
            tkey = cur.advance()
            k = ast.Ident(name=tkey.text, span=tkey.span)
        else:
            k = _parse_ident(cur)
        cur.expect(TokenKind.EQ, "Expected '=' in hook with(...) option")
        t = cur.peek()
        if t.kind in (TokenKind.STR, TokenKind.BOOL, TokenKind.IDENT):
            vtok = cur.advance()
            opts[k.name] = vtok.text
        elif t.kind == TokenKind.INT:
            if cur.peek().text == "0" and cur.peek(1).kind == TokenKind.MINUS and cur.peek(2).kind == TokenKind.INT:
                # Backward compat for odd forms; keep parser robust.
                # Prefer plain negative ints in source.
                v0 = cur.advance().text
                cur.advance()
                v2 = cur.advance().text
                opts[k.name] = f"{v0}-{v2}"
            else:
                vtok = cur.advance()
                opts[k.name] = vtok.text
        elif t.kind == TokenKind.MINUS and cur.peek(1).kind == TokenKind.INT:
            cur.advance()
            vtok = cur.advance()
            opts[k.name] = f"-{vtok.text}"
        else:
            raise ParseError("Expected hook option value (str/bool/int/ident)", t.span)
        if not cur.match(TokenKind.COMMA):
            break
    cur.expect(TokenKind.RPAREN, "Expected ')' to close hook with(...)")
    return opts


def _parse_mixin_hook(cur: _Cursor) -> ast.MixinHook:
    hook_kw = cur.expect(TokenKind.IDENT, "Expected 'hook' item in mixin body")
    if hook_kw.text != "hook":
        raise ParseError("Expected 'hook' item in mixin body", hook_kw.span)

    point_tok = cur.expect(TokenKind.IDENT, "Expected hook point (head/tail/invoke)")
    point = point_tok.text
    if point not in ("head", "tail", "invoke"):
        raise ParseError("Expected hook point (head/tail/invoke)", point_tok.span)

    cur.expect(TokenKind.KW_FN)
    name = _parse_ident(cur)
    cur.expect(TokenKind.LPAREN)
    params: list[ast.ParamDecl] = []
    if not cur.at(TokenKind.RPAREN):
        params.append(_parse_param(cur))
        while cur.match(TokenKind.COMMA):
            params.append(_parse_param(cur))
    rp = cur.expect(TokenKind.RPAREN)
    ret_ty: ast.TypeRef | None = None
    if cur.match(TokenKind.ARROW):
        ret_ty = _parse_type_ref(cur)
    sig = ast.FnSignature(name=name, params=params, retType=ret_ty, span=hook_kw.span.merge(rp.span))

    opts = _parse_hook_with_options(cur)

    cur.expect(TokenKind.EQ, "Expected '=' after hook signature (use '= expr' or '= do:')")
    body = _parse_fn_body(cur)
    span = hook_kw.span.merge(body.span)
    return ast.MixinHook(point=point, sig=sig, body=body, opts=opts, span=span)


def _parse_use_mixin(cur: _Cursor) -> ast.UseMixinStmt:
    kw = cur.expect(TokenKind.KW_USE)
    cur.expect(TokenKind.KW_MIXIN)
    name = _parse_qualified_name(cur)
    version = _parse_version_token(cur)
    span = kw.span.merge(cur.peek(-1).span)
    return ast.UseMixinStmt(name=name, version=version, span=span)


def _parse_use(cur: _Cursor) -> ast.UseStmt:
    kw = cur.expect(TokenKind.KW_USE)
    name = _parse_qualified_name(cur)
    span = kw.span.merge(name.span)
    return ast.UseStmt(name=name, span=span)


def _parse_resolve_mixin(cur: _Cursor) -> ast.ResolveMixinStmt:
    kw = cur.expect(TokenKind.KW_RESOLVE)
    # Parse `mixin-conflict` as `IDENT('mixin') MINUS IDENT('conflict')`.
    a_tok = cur.peek()
    if a_tok.kind in (TokenKind.IDENT, TokenKind.KW_MIXIN):
        a = cur.advance()
    else:
        raise ParseError("Expected 'mixin-conflict'", a_tok.span)
    cur.expect(TokenKind.MINUS, "Expected 'mixin-conflict'")
    b = cur.expect(TokenKind.IDENT, "Expected 'mixin-conflict'")
    if a.text != "mixin" or b.text != "conflict":
        raise ParseError("Expected 'mixin-conflict'", a.span.merge(b.span))

    cur.expect(TokenKind.COLON)
    cur.expect(TokenKind.NL)
    cur.expect(TokenKind.INDENT)
    rules: list[ast.PreferRule] = []
    while not cur.at(TokenKind.DEDENT) and not cur.at(TokenKind.EOF):
        if cur.at(TokenKind.NL):
            cur.advance()
            continue
        pr_kw = cur.expect(TokenKind.KW_PREFER)
        prefer_name = _parse_qualified_name(cur)
        prefer_ver = _parse_version_token(cur)
        cur.expect(TokenKind.KW_OVER)
        over_name = _parse_qualified_name(cur)
        over_ver = _parse_version_token(cur)
        span = pr_kw.span.merge(cur.peek(-1).span)
        rules.append(
            ast.PreferRule(
                prefer=ast.PreferRef(name=prefer_name, version=prefer_ver),
                over=ast.PreferRef(name=over_name, version=over_ver),
                span=span,
            )
        )
        if cur.at(TokenKind.NL):
            cur.advance()
    ded = cur.expect(TokenKind.DEDENT)
    span = kw.span.merge(ded.span)
    return ast.ResolveMixinStmt(rules=rules, span=span)


# ---------------- expressions ----------------

_PRECEDENCE: dict[TokenKind, int] = {
    TokenKind.KW_OR: 10,
    TokenKind.KW_AND: 20,
    TokenKind.EQEQ: 30,
    TokenKind.NEQ: 30,
    TokenKind.LT: 30,
    TokenKind.LTE: 30,
    TokenKind.GT: 30,
    TokenKind.GTE: 30,
    TokenKind.PLUS: 40,
    TokenKind.MINUS: 40,
    TokenKind.STAR: 50,
    TokenKind.SLASH: 50,
}


def _parse_expr(cur: _Cursor) -> ast.Expr:
    return _parse_pipe(cur)


def _parse_pipe(cur: _Cursor) -> ast.Expr:
    head = _parse_binary(cur, 0)
    stages: list[ast.Expr] = []
    while cur.match(TokenKind.PIPE):
        stages.append(_parse_binary(cur, 0))
    if stages:
        span = head.span.merge(stages[-1].span)
        return ast.PipeExpr(head=head, stages=stages, span=span)
    return head


def _parse_binary(cur: _Cursor, min_prec: int) -> ast.Expr:
    left = _parse_unary(cur)
    while True:
        op = cur.peek().kind
        prec = _PRECEDENCE.get(op)
        if prec is None or prec < min_prec:
            break
        tok = cur.advance()
        right = _parse_binary(cur, prec + 1)
        span = left.span.merge(right.span)
        left = ast.BinaryExpr(op=tok.text, left=left, right=right, span=span)
    return left


def _parse_unary(cur: _Cursor) -> ast.Expr:
    if cur.at(TokenKind.MINUS) or cur.at(TokenKind.KW_NOT):
        tok = cur.advance()
        expr = _parse_unary(cur)
        return ast.UnaryExpr(op=tok.text, expr=expr, span=tok.span.merge(expr.span))
    return _parse_postfix(cur)


def _parse_postfix(cur: _Cursor) -> ast.Expr:
    expr = _parse_primary(cur)
    while True:
        if cur.match(TokenKind.LPAREN):
            args: list[ast.CallArg] = []

            def parse_call_arg() -> ast.CallArg:
                if cur.match(TokenKind.STAR):
                    v = _parse_expr(cur)
                    return ast.CallArgStar(value=v, span=v.span)
                if cur.match(TokenKind.STARSTAR):
                    v = _parse_expr(cur)
                    return ast.CallArgStarStar(value=v, span=v.span)
                if cur.peek().kind in (TokenKind.IDENT, TokenKind.KW_OK, TokenKind.KW_ERR, TokenKind.KW_SOME, TokenKind.KW_NONE) and cur.peek(1).kind == TokenKind.EQ:
                    name = _parse_ident(cur)
                    cur.expect(TokenKind.EQ)
                    v = _parse_expr(cur)
                    return ast.CallArgKw(name=name, value=v, span=name.span.merge(v.span))
                v = _parse_expr(cur)
                return ast.CallArgPos(value=v, span=v.span)

            if not cur.at(TokenKind.RPAREN):
                args.append(parse_call_arg())
                while cur.match(TokenKind.COMMA):
                    if cur.at(TokenKind.RPAREN):
                        break
                    args.append(parse_call_arg())
            rp = cur.expect(TokenKind.RPAREN)
            expr = ast.CallExpr(callee=expr, args=args, span=expr.span.merge(rp.span))
            continue
        if cur.match(TokenKind.DOT):
            field = _parse_ident(cur)
            expr = ast.MemberExpr(object=expr, field=field, span=expr.span.merge(field.span))
            continue
        if cur.match(TokenKind.LBRACKET):
            idx = _parse_expr(cur)
            rb = cur.expect(TokenKind.RBRACKET)
            expr = ast.IndexExpr(object=expr, index=idx, span=expr.span.merge(rb.span))
            continue
        if cur.match(TokenKind.QMARK):
            q = cur.peek(-1)
            expr = ast.TrySuffixExpr(inner=expr, span=expr.span.merge(q.span))
            continue
        break
    return expr


def _parse_primary(cur: _Cursor) -> ast.Expr:
    t = cur.peek()

    if cur.at(TokenKind.INT):
        tok = cur.advance()
        lit = ast.Literal(kind="LitInt", value=tok.text, span=tok.span)
        return ast.LitExpr(lit=lit, span=tok.span)
    if cur.at(TokenKind.FLOAT):
        tok = cur.advance()
        lit = ast.Literal(kind="LitFloat", value=tok.text, span=tok.span)
        return ast.LitExpr(lit=lit, span=tok.span)
    if cur.at(TokenKind.STR):
        tok = cur.advance()
        lit = ast.Literal(kind="LitStr", value=tok.text, span=tok.span)
        return ast.LitExpr(lit=lit, span=tok.span)
    if cur.at(TokenKind.BYTES):
        tok = cur.advance()
        lit = ast.Literal(kind="LitBytes", value=tok.text, span=tok.span)
        return ast.LitExpr(lit=lit, span=tok.span)
    if cur.at(TokenKind.BOOL):
        tok = cur.advance()
        lit = ast.Literal(kind="LitBool", value=(tok.text == "true"), span=tok.span)
        return ast.LitExpr(lit=lit, span=tok.span)

    if cur.peek().kind in (TokenKind.IDENT, TokenKind.KW_OK, TokenKind.KW_ERR, TokenKind.KW_SOME, TokenKind.KW_NONE):
        ident = _parse_ident(cur)
        return ast.VarExpr(name=ident, span=ident.span)

    if cur.at(TokenKind.LBRACE):
        return _parse_record_lit(cur)

    if cur.match(TokenKind.LPAREN):
        # Unit literal: `()`
        if cur.at(TokenKind.RPAREN):
            rp = cur.expect(TokenKind.RPAREN)
            return ast.TupleLitExpr(items=[], span=rp.span)
        first = _parse_expr(cur)
        if cur.match(TokenKind.COMMA):
            items = [first]
            if not cur.at(TokenKind.RPAREN):
                items.append(_parse_expr(cur))
                while cur.match(TokenKind.COMMA):
                    if cur.at(TokenKind.RPAREN):
                        break
                    items.append(_parse_expr(cur))
            rp = cur.expect(TokenKind.RPAREN)
            return ast.TupleLitExpr(items=items, span=first.span.merge(rp.span))
        rp = cur.expect(TokenKind.RPAREN)
        return first

    if cur.at(TokenKind.KW_MATCH):
        return _parse_match(cur)

    if cur.at(TokenKind.KW_AWAIT):
        kw = cur.advance()
        qn = _parse_qualified_name(cur)
        return ast.AwaitExpr(eventType=qn, span=kw.span.merge(qn.span))

    if cur.at(TokenKind.KW_RPC):
        kw = cur.advance()
        sector = _parse_ident(cur)
        cur.expect(TokenKind.DOT)
        fn = _parse_ident(cur)
        cur.expect(TokenKind.LPAREN)
        args: list[ast.Expr] = []
        if not cur.at(TokenKind.RPAREN):
            args.append(_parse_expr(cur))
            while cur.match(TokenKind.COMMA):
                if cur.at(TokenKind.RPAREN):
                    break
                args.append(_parse_expr(cur))
        rp = cur.expect(TokenKind.RPAREN)
        return ast.RpcExpr(sector=sector, fnName=fn, args=args, span=kw.span.merge(rp.span))

    if cur.at(TokenKind.KW_CALL):
        kw = cur.advance()
        sector = _parse_ident(cur)
        cur.expect(TokenKind.DOT)
        fn = _parse_ident(cur)
        cur.expect(TokenKind.LPAREN)
        args: list[ast.Expr] = []
        if not cur.at(TokenKind.RPAREN):
            args.append(_parse_expr(cur))
            while cur.match(TokenKind.COMMA):
                if cur.at(TokenKind.RPAREN):
                    break
                args.append(_parse_expr(cur))
        rp = cur.expect(TokenKind.RPAREN)
        return ast.CallSectorExpr(sector=sector, fnName=fn, args=args, span=kw.span.merge(rp.span))

    if cur.at(TokenKind.KW_PROCEED):
        kw = cur.advance()
        cur.expect(TokenKind.LPAREN)
        args: list[ast.Expr] = []
        if not cur.at(TokenKind.RPAREN):
            args.append(_parse_expr(cur))
            while cur.match(TokenKind.COMMA):
                if cur.at(TokenKind.RPAREN):
                    break
                args.append(_parse_expr(cur))
        rp = cur.expect(TokenKind.RPAREN)
        return ast.ProceedExpr(args=args, span=kw.span.merge(rp.span))

    raise ParseError("Expected expression", t.span)


def _parse_record_lit(cur: _Cursor) -> ast.RecordLitExpr:
    l = cur.expect(TokenKind.LBRACE)
    items: list[ast.RecordItem] = []
    if not cur.at(TokenKind.RBRACE):
        items.append(_parse_record_item(cur))
        while cur.match(TokenKind.COMMA):
            if cur.at(TokenKind.RBRACE):
                break
            items.append(_parse_record_item(cur))
    r = cur.expect(TokenKind.RBRACE)
    return ast.RecordLitExpr(items=items, span=l.span.merge(r.span))


def _parse_record_item(cur: _Cursor) -> ast.RecordItem:
    key = _parse_ident(cur)
    cur.expect(TokenKind.EQ)
    value = _parse_expr(cur)
    return ast.RecordItem(key=key, value=value, span=key.span.merge(value.span))


def _parse_match(cur: _Cursor) -> ast.MatchExpr:
    kw = cur.expect(TokenKind.KW_MATCH)
    scrut = _parse_expr(cur)
    cur.expect(TokenKind.COLON, "Expected ':' after match scrutinee")
    cur.expect(TokenKind.NL, "Expected newline after match header")
    cur.expect(TokenKind.INDENT, "Expected indented match arms")
    arms: list[ast.MatchArm] = []
    while not cur.at(TokenKind.DEDENT) and not cur.at(TokenKind.EOF):
        if cur.at(TokenKind.NL):
            cur.advance()
            continue
        if cur.at(TokenKind.ARROW):
            raise ParseError("Expected match arm pattern before '->'", cur.peek().span)
        if cur.at(TokenKind.KW_DO):
            raise ParseError("Expected match arm pattern before 'do:'", cur.peek().span)
        pat = _parse_pattern(cur)
        cur.expect(TokenKind.ARROW, "Expected '->' after match arm pattern")
        if cur.at(TokenKind.NL):
            raise ParseError("Expected match arm body after '->' (expression or do: block)", cur.peek().span)
        if cur.at(TokenKind.KW_DO):
            kw_do = cur.advance()
            block = _parse_block_after_colon(cur, kw_do.span)
            body = ast.BodyDo(block=block, span=kw_do.span.merge(block.span))
        else:
            body = _parse_expr(cur)
        if cur.at(TokenKind.NL):
            cur.advance()
        arms.append(ast.MatchArm(pat=pat, body=body, span=pat.span.merge(body.span if hasattr(body, 'span') else pat.span)))
    ded = cur.expect(TokenKind.DEDENT)
    span = kw.span.merge(ded.span)
    return ast.MatchExpr(scrutinee=scrut, arms=arms, span=span)


def _parse_pattern(cur: _Cursor) -> ast.Pattern:
    t = cur.peek()
    if cur.at(TokenKind.IDENT) and t.text == "_":
        cur.advance()
        return ast.PWildcard(span=t.span)

    if cur.at(TokenKind.BOOL):
        tok = cur.advance()
        return ast.PBool(value=(tok.text == "true"), span=tok.span)

    name = _parse_qualified_name(cur)
    if cur.match(TokenKind.LPAREN):
        args: list[ast.Pattern] = []
        if not cur.at(TokenKind.RPAREN):
            args.append(_parse_pattern(cur))
            while cur.match(TokenKind.COMMA):
                args.append(_parse_pattern(cur))
        rp = cur.expect(TokenKind.RPAREN)
        return ast.PConstructor(name=name, args=args, span=name.span.merge(rp.span))

    if len(name.parts) == 1:
        # Heuristic: Uppercase identifiers are treated as constructors/pattern aliases.
        # This also makes nullary constructors like `None` parse as constructor patterns.
        if name.parts[0].name[:1].isupper():
            return ast.PConstructor(name=name, args=None, span=name.span)
        return ast.PVar(name=name.parts[0], span=name.span)
    return ast.PConstructor(name=name, args=None, span=name.span)


def _parse_pattern_decl(cur: _Cursor) -> ast.PatternDecl:
    kw = cur.expect(TokenKind.KW_PATTERN)
    name = _parse_qualified_name(cur)
    cur.expect(TokenKind.EQ, "Expected '=' after pattern name")
    pat = _parse_pattern(cur)
    span = kw.span.merge(pat.span)
    return ast.PatternDecl(name=name, pat=pat, span=span)


def _parse_stmt(cur: _Cursor) -> ast.Stmt:
    if cur.at(TokenKind.KW_LET):
        kw = cur.advance()
        name = _parse_ident(cur)
        cur.expect(TokenKind.EQ)
        value = _parse_expr(cur)
        return ast.LetStmt(name=name, value=value, span=kw.span.merge(value.span))

    if cur.at(TokenKind.KW_EMIT):
        kw = cur.advance()
        expr = _parse_expr(cur)
        return ast.EmitStmt(expr=expr, span=kw.span.merge(expr.span))

    if cur.at(TokenKind.KW_RETURN):
        kw = cur.advance()
        expr = _parse_expr(cur)
        return ast.ReturnStmt(expr=expr, span=kw.span.merge(expr.span))

    if cur.at(TokenKind.KW_STOP):
        kw = cur.advance()
        cur.expect(TokenKind.LPAREN)
        cur.expect(TokenKind.RPAREN)
        return ast.StopStmt(span=kw.span)

    if cur.at(TokenKind.KW_YIELD):
        kw = cur.advance()
        cur.expect(TokenKind.LPAREN)
        cur.expect(TokenKind.RPAREN)
        return ast.YieldStmt(span=kw.span)

    if cur.at(TokenKind.KW_IF):
        return _parse_if_stmt(cur)

    if cur.at(TokenKind.KW_FOR):
        return _parse_for_stmt(cur)

    save = cur.i
    lvalue = _try_parse_lvalue(cur)
    if lvalue is not None and cur.peek().kind in (
        TokenKind.EQ,
        TokenKind.PLUSEQ,
        TokenKind.MINUSEQ,
        TokenKind.STAREQ,
        TokenKind.SLASHEQ,
    ):
        op = cur.advance()
        value = _parse_expr(cur)
        return ast.AssignStmt(target=lvalue, op=op.text, value=value, span=lvalue.span.merge(value.span))
    cur.i = save

    # assignment vs expr stmt
    expr = _parse_expr(cur)
    return ast.ExprStmt(expr=expr, span=expr.span)


def _try_parse_lvalue(cur: _Cursor) -> ast.LValue | None:
    if cur.peek().kind not in (TokenKind.IDENT, TokenKind.KW_OK, TokenKind.KW_ERR, TokenKind.KW_SOME, TokenKind.KW_NONE):
        return None
    base = _parse_ident(cur)
    lv: ast.LValue = ast.LVar(name=base, span=base.span)
    while True:
        if cur.match(TokenKind.DOT):
            field = _parse_ident(cur)
            lv = ast.LMember(object=ast.VarExpr(name=base, span=base.span), field=field, span=lv.span.merge(field.span))
            continue
        if cur.match(TokenKind.LBRACKET):
            idx = _parse_expr(cur)
            rb = cur.expect(TokenKind.RBRACKET)
            lv = ast.LIndex(object=ast.VarExpr(name=base, span=base.span), index=idx, span=lv.span.merge(rb.span))
            continue
        break
    return lv


def _parse_if_stmt(cur: _Cursor) -> ast.IfStmt:
    kw = cur.expect(TokenKind.KW_IF)
    cond = _parse_expr(cur)
    then_block = _parse_block_after_colon(cur, kw.span)
    else_block: ast.Block | None = None
    if cur.at(TokenKind.KW_ELSE):
        kw_else = cur.advance()
        else_block = _parse_block_after_colon(cur, kw_else.span)
    span = kw.span.merge((else_block.span if else_block else then_block.span))
    return ast.IfStmt(cond=cond, thenBlock=then_block, elseBlock=else_block, span=span)


def _parse_for_stmt(cur: _Cursor) -> ast.ForStmt:
    kw = cur.expect(TokenKind.KW_FOR)
    binder = _parse_ident(cur)
    cur.expect(TokenKind.KW_IN)
    it = _parse_expr(cur)
    body = _parse_block_after_colon(cur, kw.span)
    span = kw.span.merge(body.span)
    return ast.ForStmt(binder=binder, iterable=it, body=body, span=span)
