from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import ast
from .diagnostics import LowerError, ResolveError
from .hir import (
    AbortHandlerStmt,
    AssignStmt,
    AwaitEventExpr,
    BinaryExpr,
    Block,
    CallArg,
    CallArgKw,
    CallArgPos,
    CallArgStar,
    CallArgStarStar,
    CallExpr,
    EmitStmt,
    Expr,
    ExprStmt,
    FieldDecl,
    FnDecl,
    ForStmt,
    HandlerDecl,
    IfStmt,
    IndexExpr,
    LetStmt,
    LIndex,
    LMember,
    Literal,
    LitExpr,
    LValue,
    LVar,
    MatchArmExpr,
    MatchArmStmt,
    MatchExpr,
    MatchStmt,
    MemberExpr,
    Param,
    PCtor,
    Pattern,
    Program,
    RecordItem,
    RecordLitExpr,
    RecordType,
    ReturnStmt,
    RpcCallExpr,
    SectorDecl,
    StopStmt,
    SumType,
    TupleLitExpr,
    TypeAlias,
    TypeApp,
    TypeDecl,
    TypeRef,
    TypeVar,
    UnaryExpr,
    UndefExpr,
    ValueDecl,
    VariantDecl,
    YieldStmt,
    node_to_dict,
    PVar,
    PBool,
    PWildcard,
 )
from .resolve import Resolution, resolve_program
from .symbols import Symbol, SymbolId, SymbolKind, TypeId


@dataclass(slots=True)
class _Ctx:
    res: Resolution
    sym_by_id: dict[SymbolId, Symbol]
    type_by_name: dict[str, TypeId]
    ctor_by_name: dict[str, SymbolId]
    next_sym: int

    # Current boundary
    in_handler: bool = False
    try_mode: str = "forbid"  # 'result' | 'option' | 'handler' | 'forbid'

    def fresh_sym(self, prefix: str, span) -> SymbolId:
        sid = self.next_sym
        self.next_sym += 1
        return sid


def lower_program(prog: ast.Program) -> Program:
    res = resolve_program(prog)
    return lower_resolved(res)


def lower_resolved(res: Resolution) -> Program:
    sym_by_id = {s.id: s for s in res.symbols}
    type_by_name: dict[str, TypeId] = {s.name: s.id for s in res.symbols if s.kind == SymbolKind.TYPE}
    ctor_by_name: dict[str, SymbolId] = {s.name: s.id for s in res.symbols if s.kind == SymbolKind.CTOR}
    next_sym = (max(sym_by_id.keys()) + 1) if sym_by_id else 1

    ctx = _Ctx(res=res, sym_by_id=sym_by_id, type_by_name=type_by_name, ctor_by_name=ctor_by_name, next_sym=next_sym)

    # Collect program-level items.
    types: list[TypeDecl] = []
    consts: list[ValueDecl] = []
    globals_: list[ValueDecl] = []
    needs: list[ValueDecl] = []

    sectors_by_sym: dict[SymbolId, SectorDecl] = {}

    top_handlers: list[ast.OnHandler] = []
    sector_asts: list[ast.SectorDecl] = []
    top_fns: list[ast.FnDecl] = []

    for it in res.program.items:
        if isinstance(it, ast.TypeDecl):
            types.append(_lower_type_decl(ctx, it))
        elif isinstance(it, ast.ConstDecl):
            consts.append(_lower_value_decl(ctx, it.name, it.value, it.span))
        elif isinstance(it, ast.LetDecl):
            globals_.append(_lower_value_decl(ctx, it.name, it.value, it.span))
        elif isinstance(it, ast.NeedDecl):
            needs.append(_lower_value_decl(ctx, it.name, it.value, it.span))
        elif isinstance(it, ast.SectorDecl):
            sector_asts.append(it)
        elif isinstance(it, ast.OnHandler):
            top_handlers.append(it)
        elif isinstance(it, ast.FnDecl):
            top_fns.append(it)
        else:
            # mixins/use/resolve are not lowered in Phase 3 MVP
            continue

    # Build sectors declared in AST.
    for sd in sector_asts:
        sec = _lower_sector(ctx, sd)
        sectors_by_sym[sec.sym] = sec

    # Move top-level handlers into main.
    if top_handlers:
        # sector 'main' is a sector symbol.
        main_sector: SymbolId | None = None
        for s in res.symbols:
            if s.kind == SymbolKind.SECTOR and s.name == "main":
                main_sector = s.id
                break
        if main_sector is None:
            raise LowerError("Missing main sector symbol", res.program.span)

        sec = sectors_by_sym.get(main_sector)
        if sec is None:
            sec = SectorDecl(sym=main_sector, fns=[], handlers=[], lets=[], needs=[], span=res.program.span)
            sectors_by_sym[main_sector] = sec

        extra_handlers = [_lower_handler(ctx, h, owner_sector=main_sector) for h in top_handlers]
        sec.handlers.extend(extra_handlers)

    # Lower top-level fns, possibly attach to sectors if sector-qualified.
    program_fns: list[FnDecl] = []
    for fd in top_fns:
        fn_sym = _sym_of_ident(ctx, fd.name)
        owner = (ctx.sym_by_id.get(fn_sym).data or {}).get("sector") if ctx.sym_by_id.get(fn_sym) else None
        hfn = _lower_fn(ctx, fd, owner_sector=owner)
        if owner is not None:
            sec = sectors_by_sym.get(owner)
            if sec is None:
                sec = SectorDecl(sym=owner, fns=[], handlers=[], lets=[], needs=[], span=fd.span)
                sectors_by_sym[owner] = sec
            sec.fns.append(hfn)
        else:
            program_fns.append(hfn)

    sectors = list(sectors_by_sym.values())

    run = res.program.run is not None
    return Program(
        types=types,
        consts=consts,
        globals=globals_,
        needs=needs,
        fns=program_fns,
        sectors=sectors,
        run=run,
        span=res.program.span,
    )


def _sym_of_ident(ctx: _Ctx, ident: ast.Ident) -> SymbolId:
    sid = ctx.res.ident_to_symbol.get(id(ident))
    if sid is None:
        raise ResolveError(f"Unresolved identifier: {ident.name}", ident.span)
    return sid


def _type_of_qname(ctx: _Ctx, qn: ast.QualifiedName) -> TypeId:
    tid = ctx.res.typename_to_symbol.get(id(qn))
    if tid is not None:
        return tid

    name = ".".join(p.name for p in qn.parts)
    tid = ctx.type_by_name.get(name)
    if tid is None:
        raise ResolveError(f"Unknown type: {name}", qn.span)
    return tid


def _ctor_of_name(ctx: _Ctx, name: str, span) -> SymbolId:
    sid = ctx.ctor_by_name.get(name)
    if sid is None:
        raise LowerError(f"Unknown ctor: {name}", span)
    return sid


def _lower_type_decl(ctx: _Ctx, td: ast.TypeDecl) -> TypeDecl:
    sym = _type_of_qname(ctx, td.name)
    rhs = _lower_type_rhs(ctx, td.rhs)
    return TypeDecl(sym=sym, rhs=rhs, span=td.span)


def _lower_type_rhs(ctx: _Ctx, rhs: ast.TypeRhs) -> object:
    if isinstance(rhs, ast.TypeAlias):
        return TypeAlias(target=_lower_type_ref(ctx, rhs.target), span=rhs.span)
    if isinstance(rhs, ast.RecordType):
        fields = [FieldDecl(name=f.name.name, ty=_lower_type_ref(ctx, f.ty), span=f.span) for f in rhs.fields]
        return RecordType(fields=fields, span=rhs.span)
    if isinstance(rhs, ast.SumType):
        variants: list[VariantDecl] = []
        for v in rhs.variants:
            ctor = ctx.ctor_by_name.get(v.name.name)
            if ctor is None:
                # ctor might be user-defined; fall back to best-effort lookup by name in symbols.
                for s in ctx.sym_by_id.values():
                    if s.kind == SymbolKind.CTOR and s.name == v.name.name:
                        ctor = s.id
                        break
            if ctor is None:
                ctor = ctx.fresh_sym("ctor", v.span)
            payload = [_lower_type_ref(ctx, t) for t in (v.payload or [])] or None
            variants.append(VariantDecl(ctor=ctor, payload=payload, span=v.span))
        return SumType(variants=variants, span=rhs.span)
    raise LowerError("Unsupported type rhs", rhs.span)


def _lower_type_ref(ctx: _Ctx, tr: ast.TypeRef) -> TypeRef:
    if isinstance(tr, ast.TypeParen):
        return _lower_type_ref(ctx, tr.inner)
    if isinstance(tr, ast.TypeName):
        base = _type_of_qname(ctx, tr.name)
        if tr.args:
            return TypeApp(base=base, args=[_lower_type_ref(ctx, a) for a in tr.args], span=tr.span)
        return TypeVar(id=base, span=tr.span)
    raise LowerError("Unsupported type ref", tr.span)


def _lower_value_decl(ctx: _Ctx, name: ast.Ident, value: ast.Expr, span) -> ValueDecl:
    sym = _sym_of_ident(ctx, name)
    stmts, expr = _lower_expr(ctx, value)
    if stmts:
        # Hoist temporaries by wrapping into an expression-less block is not available in HIR.
        # MVP: reject for now.
        raise LowerError("Top-level initializer cannot contain control-flow sugar in Phase 3", span)
    return ValueDecl(sym=sym, expr=expr, span=span)


def _lower_sector(ctx: _Ctx, sd: ast.SectorDecl) -> SectorDecl:
    sym = _sym_of_ident(ctx, sd.name)
    lets: list[ValueDecl] = []
    needs: list[ValueDecl] = []
    fns: list[FnDecl] = []
    handlers: list[HandlerDecl] = []

    for it in sd.items:
        if isinstance(it, ast.LetDecl):
            lets.append(_lower_value_decl(ctx, it.name, it.value, it.span))
        elif isinstance(it, ast.NeedDecl):
            needs.append(_lower_value_decl(ctx, it.name, it.value, it.span))
        elif isinstance(it, ast.FnDecl):
            fns.append(_lower_fn(ctx, it, owner_sector=sym))
        elif isinstance(it, ast.OnHandler):
            handlers.append(_lower_handler(ctx, it, owner_sector=sym))

    return SectorDecl(sym=sym, fns=fns, handlers=handlers, lets=lets, needs=needs, span=sd.span)


def _lower_handler(ctx: _Ctx, h: ast.OnHandler, *, owner_sector: SymbolId) -> HandlerDecl:
    handler_sym = ctx.res.handler_to_symbol.get(id(h))
    if handler_sym is None:
        handler_sym = ctx.fresh_sym("handler", h.span)

    if isinstance(h.event, ast.EventType):
        event_ty = _type_of_qname(ctx, h.event.name)
    elif isinstance(h.event, ast.EventCall):
        event_ty = _type_of_qname(ctx, h.event.name)
    else:
        raise LowerError("Unsupported event pattern", h.span)

    binder_sym: SymbolId | None = None
    if h.binder is not None:
        binder_sym = _sym_of_ident(ctx, h.binder)

    when = None
    if h.when is not None:
        stmts, when_expr = _lower_expr(_with_handler(ctx), h.when)
        if stmts:
            raise LowerError("when guard cannot contain try-suffix in Phase 3", h.when.span)
        when = when_expr

    body_block = _lower_handler_body(ctx, h)

    return HandlerDecl(
        sym=handler_sym,
        eventType=event_ty,
        binder=binder_sym,
        when=when,
        body=body_block,
        span=h.span,
    )


def _with_handler(ctx: _Ctx) -> _Ctx:
    hctx = _Ctx(
        res=ctx.res,
        sym_by_id=ctx.sym_by_id,
        type_by_name=ctx.type_by_name,
        ctor_by_name=ctx.ctor_by_name,
        next_sym=ctx.next_sym,
        in_handler=True,
        try_mode="handler",
    )
    return hctx


def _with_fn(ctx: _Ctx, fd: ast.FnDecl) -> _Ctx:
    mode = "forbid"
    if fd.retType is not None and isinstance(fd.retType, ast.TypeName):
        base_name = ".".join(p.name for p in fd.retType.name.parts)
        if base_name == "Result":
            mode = "result"
        elif base_name == "Option":
            mode = "option"

    fctx = _Ctx(
        res=ctx.res,
        sym_by_id=ctx.sym_by_id,
        type_by_name=ctx.type_by_name,
        ctor_by_name=ctx.ctor_by_name,
        next_sym=ctx.next_sym,
        in_handler=False,
        try_mode=mode,
    )
    return fctx


def _lower_handler_body(ctx: _Ctx, h: ast.OnHandler) -> Block:
    hctx = _with_handler(ctx)
    if isinstance(h.body, ast.HandlerExpr):
        stmts, expr = _lower_expr(hctx, h.body.expr)
        stmts.append(ExprStmt(expr=expr, span=h.body.expr.span))
        return Block(stmts=stmts, span=h.span)
    return _lower_block(hctx, h.body.block)


def _lower_fn(ctx: _Ctx, fd: ast.FnDecl, *, owner_sector: Optional[SymbolId]) -> FnDecl:
    sym = _sym_of_ident(ctx, fd.name)

    fctx = _with_fn(ctx, fd)

    params = [Param(sym=_sym_of_ident(fctx, p.name), ty=_lower_type_ref(fctx, p.ty), kind=p.kind, span=p.span) for p in fd.params]
    ret = _lower_type_ref(fctx, fd.retType) if fd.retType is not None else None

    if isinstance(fd.body, ast.BodyExpr):
        stmts, expr = _lower_expr(fctx, fd.body.expr)
        stmts.append(ReturnStmt(expr=expr, span=fd.body.expr.span))
        body = Block(stmts=stmts, span=fd.body.span)
    else:
        body = _lower_block(fctx, fd.body.block)

    ctx.next_sym = max(ctx.next_sym, fctx.next_sym)

    return FnDecl(sym=sym, ownerSector=owner_sector, params=params, retType=ret, body=body, span=fd.span)


def _lower_block(ctx: _Ctx, b: ast.Block) -> Block:
    out: list[object] = []
    for st in b.stmts:
        out.extend(_lower_stmt(ctx, st))
    return Block(stmts=out, span=b.span)


def _lower_stmt(ctx: _Ctx, st: ast.Stmt) -> list[object]:
    if isinstance(st, ast.LetStmt):
        sym = _sym_of_ident(ctx, st.name)
        pre, expr = _lower_expr(ctx, st.value)
        return [*pre, LetStmt(sym=sym, expr=expr, span=st.span)]

    if isinstance(st, ast.AssignStmt):
        pre1, lv = _lower_lvalue(ctx, st.target)
        pre2, expr = _lower_expr(ctx, st.value)
        return [*pre1, *pre2, AssignStmt(target=lv, op=st.op, expr=expr, span=st.span)]

    if isinstance(st, ast.EmitStmt):
        pre, expr = _lower_expr(ctx, st.expr)
        return [*pre, EmitStmt(expr=expr, span=st.span)]

    if isinstance(st, ast.ReturnStmt):
        pre, expr = _lower_expr(ctx, st.expr)
        return [*pre, ReturnStmt(expr=expr, span=st.span)]

    if isinstance(st, ast.ExprStmt):
        pre, expr = _lower_expr(ctx, st.expr)
        return [*pre, ExprStmt(expr=expr, span=st.span)]

    if isinstance(st, ast.StopStmt):
        return [StopStmt(span=st.span)]

    if isinstance(st, ast.YieldStmt):
        return [YieldStmt(span=st.span)]

    if isinstance(st, ast.IfStmt):
        pre, cond = _lower_expr(ctx, st.cond)
        then_block = _lower_block(ctx, st.thenBlock)
        else_block = _lower_block(ctx, st.elseBlock) if st.elseBlock is not None else None
        return [*pre, IfStmt(cond=cond, thenBlock=then_block, elseBlock=else_block, span=st.span)]

    if isinstance(st, ast.ForStmt):
        pre, it = _lower_expr(ctx, st.iterable)
        binder = _sym_of_ident(ctx, st.binder)
        body = _lower_block(ctx, st.body)
        return [*pre, ForStmt(binder=binder, iterable=it, body=body, span=st.span)]

    raise LowerError("Unsupported stmt", st.span)


def _lower_lvalue(ctx: _Ctx, lv: ast.LValue) -> tuple[list[object], LValue]:
    if isinstance(lv, ast.LVar):
        return [], LVar(sym=_sym_of_ident(ctx, lv.name), span=lv.span)
    if isinstance(lv, ast.LMember):
        pre, obj = _lower_expr(ctx, lv.object)
        return pre, LMember(object=obj, field=lv.field.name, span=lv.span)
    if isinstance(lv, ast.LIndex):
        pre1, obj = _lower_expr(ctx, lv.object)
        pre2, idx = _lower_expr(ctx, lv.index)
        return [*pre1, *pre2], LIndex(object=obj, index=idx, span=lv.span)
    raise LowerError("Unsupported lvalue", lv.span)


def _lower_expr(ctx: _Ctx, e: ast.Expr) -> tuple[list[object], Expr]:
    if isinstance(e, ast.LitExpr):
        return [], LitExpr(lit=Literal(kind=e.lit.kind, value=e.lit.value, span=e.lit.span), span=e.span)

    if isinstance(e, ast.VarExpr):
        return [], _var(ctx, e.name)

    if isinstance(e, ast.RecordLitExpr):
        items: list[RecordItem] = []
        pre: list[object] = []
        for it in e.items:
            p, v = _lower_expr(ctx, it.value)
            pre.extend(p)
            items.append(RecordItem(key=it.key.name, value=v, span=it.span))
        return pre, RecordLitExpr(items=items, span=e.span)

    if isinstance(e, ast.TupleLitExpr):
        pre: list[object] = []
        items: list[Expr] = []
        for it in e.items:
            p, v = _lower_expr(ctx, it)
            pre.extend(p)
            items.append(v)
        return pre, TupleLitExpr(items=items, span=e.span)

    if isinstance(e, ast.CallExpr):
        pre1, callee = _lower_expr(ctx, e.callee)
        pre: list[object] = [*pre1]
        args: list[CallArg] = []
        for a in e.args:
            if isinstance(a, ast.CallArgPos):
                p, v = _lower_expr(ctx, a.value)
                pre.extend(p)
                args.append(CallArgPos(value=v, span=a.span))
            elif isinstance(a, ast.CallArgStar):
                p, v = _lower_expr(ctx, a.value)
                pre.extend(p)
                args.append(CallArgStar(value=v, span=a.span))
            elif isinstance(a, ast.CallArgKw):
                p, v = _lower_expr(ctx, a.value)
                pre.extend(p)
                args.append(CallArgKw(name=a.name.name, value=v, span=a.span))
            elif isinstance(a, ast.CallArgStarStar):
                p, v = _lower_expr(ctx, a.value)
                pre.extend(p)
                args.append(CallArgStarStar(value=v, span=a.span))
            else:
                # Backward compatibility: treat as positional arg.
                p, v = _lower_expr(ctx, a)
                pre.extend(p)
                args.append(CallArgPos(value=v, span=a.span))
        return pre, CallExpr(callee=callee, args=args, span=e.span)

    if isinstance(e, ast.MemberExpr):
        # If resolver bound the field ident to a symbol, treat this as a namespaced reference
        # (e.g. std.option.unwrapOr) rather than record member access.
        if id(e.field) in ctx.res.ident_to_symbol:
            return [], _var(ctx, e.field)
        pre, obj = _lower_expr(ctx, e.object)
        return pre, MemberExpr(object=obj, field=e.field.name, span=e.span)

    if isinstance(e, ast.IndexExpr):
        pre1, obj = _lower_expr(ctx, e.object)
        pre2, idx = _lower_expr(ctx, e.index)
        return [*pre1, *pre2], IndexExpr(object=obj, index=idx, span=e.span)

    if isinstance(e, ast.UnaryExpr):
        pre, inner = _lower_expr(ctx, e.expr)
        return pre, UnaryExpr(op=e.op, expr=inner, span=e.span)

    if isinstance(e, ast.BinaryExpr):
        pre1, left = _lower_expr(ctx, e.left)
        pre2, right = _lower_expr(ctx, e.right)
        return [*pre1, *pre2], BinaryExpr(op=e.op, left=left, right=right, span=e.span)

    if isinstance(e, ast.PipeExpr):
        pre, expr = _lower_expr(ctx, e.head)
        if pre:
            raise LowerError("Pipe head cannot contain try-suffix in Phase 3", e.span)
        cur = expr
        for stage in e.stages:
            cur = _lower_pipe_stage(ctx, cur, stage)
        return [], cur

    if isinstance(e, ast.MatchExpr):
        pre_scrut, scrut = _lower_expr(ctx, e.scrutinee)

        any_block = any(isinstance(a.body, ast.BodyDo) for a in e.arms)
        any_sugar = False
        arms_expr: list[MatchArmExpr] = []
        if not any_block:
            for arm in e.arms:
                p, b = _lower_expr(ctx, arm.body)
                if p:
                    any_sugar = True
                    break
                arms_expr.append(MatchArmExpr(pat=_lower_pattern(ctx, arm.pat), body=b, span=arm.span))
            if not any_sugar:
                return pre_scrut, MatchExpr(scrutinee=scrut, arms=arms_expr, span=e.span)

        # Lower MatchExpr-with-block-arms into a statement match:
        #   let tmp = <scrut>
        #   let res = undef
        #   match tmp:
        #     pat -> do: <stmts>; res = <expr>
        #   res
        tmp = ctx.fresh_sym("tmp", e.span)
        res_sym = ctx.fresh_sym("res", e.span)

        out: list[object] = [*pre_scrut]
        out.append(LetStmt(sym=tmp, expr=scrut, span=e.span))
        out.append(LetStmt(sym=res_sym, expr=UndefExpr(span=e.span), span=e.span))

        arms_stmt: list[MatchArmStmt] = []
        for arm in e.arms:
            if isinstance(arm.body, ast.BodyDo):
                blk = _lower_block(ctx, arm.body.block)
                # Assign the last expression statement into result, if present.
                if blk.stmts and isinstance(blk.stmts[-1], ExprStmt):
                    last = blk.stmts[-1]
                    blk = Block(stmts=[*blk.stmts[:-1], AssignStmt(target=LVar(sym=res_sym, span=last.span), op="=", expr=last.expr, span=last.span)], span=blk.span)
            else:
                pre_arm, expr = _lower_expr(ctx, arm.body)
                blk = Block(stmts=[*pre_arm, AssignStmt(target=LVar(sym=res_sym, span=arm.span), op="=", expr=expr, span=arm.span)], span=arm.span)
            arms_stmt.append(MatchArmStmt(pat=_lower_pattern(ctx, arm.pat), body=blk, span=arm.span))

        out.append(MatchStmt(scrutinee=_var_sym(tmp, e.span), arms=arms_stmt, span=e.span))
        return out, _var_sym(res_sym, e.span)

    if isinstance(e, ast.AwaitExpr):
        type_id = _type_of_qname(ctx, e.eventType)
        return [], AwaitEventExpr(typeId=type_id, span=e.span)

    if isinstance(e, ast.RpcExpr):
        sector = _sym_of_ident(ctx, e.sector)
        fn = _sym_of_ident(ctx, e.fnName)
        pre: list[object] = []
        args: list[Expr] = []
        for a in e.args:
            p, v = _lower_expr(ctx, a)
            pre.extend(p)
            args.append(v)
        return pre, RpcCallExpr(sector=sector, fn=fn, args=args, awaitResult=True, span=e.span)

    if isinstance(e, ast.CallSectorExpr):
        sector = _sym_of_ident(ctx, e.sector)
        fn = _sym_of_ident(ctx, e.fnName)
        pre: list[object] = []
        args: list[Expr] = []
        for a in e.args:
            p, v = _lower_expr(ctx, a)
            pre.extend(p)
            args.append(v)
        return pre, RpcCallExpr(sector=sector, fn=fn, args=args, awaitResult=False, span=e.span)

    if isinstance(e, ast.TrySuffixExpr):
        return _lower_try_suffix(ctx, e)

    if isinstance(e, ast.ProceedExpr):
        raise LowerError("proceed() cannot appear outside mixin weaving", e.span)

    if isinstance(e, ast.BodyDo):
        block = _lower_block(ctx, e.block)
        # Wrap block in MatchExpr with wildcard pattern if needed, 
        # but better to just use a Block if HIR supports it in Expr context.
        # Since HIR Expr doesn't have Block, we'll use a hack or reject.
        # Actually, bank_system.flv uses do: in match arms which are MatchArmStmt in HIR.
        # So we should be lowering to MatchStmt if it's a statement context.
        raise LowerError("BodyDo (do:) blocks in expressions not fully supported in HIR yet", e.span)


def _lower_pipe_stage(ctx: _Ctx, prev: Expr, stage: ast.Expr) -> Expr:
    if isinstance(stage, ast.VarExpr):
        callee = _var(ctx, stage.name)
        return CallExpr(callee=callee, args=[CallArgPos(value=prev, span=stage.span)], span=stage.span)

    if isinstance(stage, ast.MemberExpr):
        pre, m = _lower_expr(ctx, stage)
        if pre:
            raise LowerError("Pipe stage cannot contain try-suffix", stage.span)
        return CallExpr(callee=m, args=[CallArgPos(value=prev, span=stage.span)], span=stage.span)

    if isinstance(stage, ast.CallExpr):
        pre, callee = _lower_expr(ctx, stage.callee)
        if pre:
            raise LowerError("Pipe stage callee cannot contain try-suffix", stage.span)
        args: list[CallArg] = [CallArgPos(value=prev, span=stage.span)]
        for a in stage.args:
            if isinstance(a, ast.CallArgPos):
                ap, av = _lower_expr(ctx, a.value)
                if ap:
                    raise LowerError("Pipe stage args cannot contain try-suffix", a.span)
                args.append(CallArgPos(value=av, span=a.span))
            elif isinstance(a, ast.CallArgStar):
                ap, av = _lower_expr(ctx, a.value)
                if ap:
                    raise LowerError("Pipe stage args cannot contain try-suffix", a.span)
                args.append(CallArgStar(value=av, span=a.span))
            elif isinstance(a, ast.CallArgKw):
                ap, av = _lower_expr(ctx, a.value)
                if ap:
                    raise LowerError("Pipe stage args cannot contain try-suffix", a.span)
                args.append(CallArgKw(name=a.name.name, value=av, span=a.span))
            elif isinstance(a, ast.CallArgStarStar):
                ap, av = _lower_expr(ctx, a.value)
                if ap:
                    raise LowerError("Pipe stage args cannot contain try-suffix", a.span)
                args.append(CallArgStarStar(value=av, span=a.span))
            else:
                ap, av = _lower_expr(ctx, a)
                if ap:
                    raise LowerError("Pipe stage args cannot contain try-suffix", a.span)
                args.append(CallArgPos(value=av, span=a.span))
        return CallExpr(callee=callee, args=args, span=stage.span)

    raise LowerError("PipeStageError", stage.span)


def _lower_try_suffix(ctx: _Ctx, e: ast.TrySuffixExpr) -> tuple[list[object], Expr]:
    if ctx.try_mode == "forbid":
        raise LowerError("TrySuffix not allowed here (unknown propagation boundary)", e.span)

    pre, inner = _lower_expr(ctx, e.inner)

    tmp = ctx.fresh_sym("tmp", e.span)
    res_sym = ctx.fresh_sym("res", e.span)

    stmts: list[object] = [
        *pre,
        LetStmt(sym=tmp, expr=inner, span=e.span),
        LetStmt(sym=res_sym, expr=UndefExpr(span=e.span), span=e.span),
    ]

    if ctx.try_mode == "result":
        ok_ctor = _ctor_of_name(ctx, "Ok", e.span)
        err_ctor = _ctor_of_name(ctx, "Err", e.span)

        v_sym = ctx.fresh_sym("v", e.span)
        e_sym = ctx.fresh_sym("e", e.span)

        ok_arm = MatchArmStmt(
            pat=PCtor(ctor=ok_ctor, args=[PVar(sym=v_sym, span=e.span)], span=e.span),
            body=Block(
                stmts=[AssignStmt(target=LVar(sym=res_sym, span=e.span), op="=", expr=_var_sym(v_sym, e.span), span=e.span)],
                span=e.span,
            ),
            span=e.span,
        )

        err_expr = CallExpr(callee=_var_sym(err_ctor, e.span), args=[_var_sym(e_sym, e.span)], span=e.span)
        err_arm_body = Block(stmts=[ReturnStmt(expr=err_expr, span=e.span)], span=e.span)
        err_arm = MatchArmStmt(
            pat=PCtor(ctor=err_ctor, args=[PVar(sym=e_sym, span=e.span)], span=e.span),
            body=err_arm_body,
            span=e.span,
        )

        stmts.append(MatchStmt(scrutinee=_var_sym(tmp, e.span), arms=[ok_arm, err_arm], span=e.span))
        return stmts, _var_sym(res_sym, e.span)

    if ctx.try_mode == "option":
        some_ctor = _ctor_of_name(ctx, "Some", e.span)
        none_ctor = _ctor_of_name(ctx, "None", e.span)

        v_sym = ctx.fresh_sym("v", e.span)

        some_arm = MatchArmStmt(
            pat=PCtor(ctor=some_ctor, args=[PVar(sym=v_sym, span=e.span)], span=e.span),
            body=Block(
                stmts=[AssignStmt(target=LVar(sym=res_sym, span=e.span), op="=", expr=_var_sym(v_sym, e.span), span=e.span)],
                span=e.span,
            ),
            span=e.span,
        )

        none_value = CallExpr(callee=_var_sym(none_ctor, e.span), args=[], span=e.span)
        none_arm = MatchArmStmt(
            pat=PCtor(ctor=none_ctor, args=None, span=e.span),
            body=Block(stmts=[ReturnStmt(expr=none_value, span=e.span)], span=e.span),
            span=e.span,
        )

        stmts.append(MatchStmt(scrutinee=_var_sym(tmp, e.span), arms=[some_arm, none_arm], span=e.span))
        return stmts, _var_sym(res_sym, e.span)

    # handler mode
    ok_ctor = _ctor_of_name(ctx, "Ok", e.span)
    err_ctor = _ctor_of_name(ctx, "Err", e.span)

    v_sym = ctx.fresh_sym("v", e.span)
    e_sym = ctx.fresh_sym("e", e.span)

    ok_arm = MatchArmStmt(
        pat=PCtor(ctor=ok_ctor, args=[PVar(sym=v_sym, span=e.span)], span=e.span),
        body=Block(
            stmts=[AssignStmt(target=LVar(sym=res_sym, span=e.span), op="=", expr=_var_sym(v_sym, e.span), span=e.span)],
            span=e.span,
        ),
        span=e.span,
    )

    err_arm = MatchArmStmt(
        pat=PCtor(ctor=err_ctor, args=[PVar(sym=e_sym, span=e.span)], span=e.span),
        body=Block(stmts=[AbortHandlerStmt(cause=_var_sym(e_sym, e.span), span=e.span)], span=e.span),
        span=e.span,
    )

    stmts.append(MatchStmt(scrutinee=_var_sym(tmp, e.span), arms=[ok_arm, err_arm], span=e.span))
    return stmts, _var_sym(res_sym, e.span)


def _lower_pattern(ctx: _Ctx, p: ast.Pattern) -> Pattern:
    if isinstance(p, ast.PWildcard):
        return PWildcard(span=p.span)
    if isinstance(p, ast.PBool):
        return PBool(value=p.value, span=p.span)
    if isinstance(p, ast.PVar):
        return PVar(sym=_sym_of_ident(ctx, p.name), span=p.span)
    if isinstance(p, ast.PConstructor):
        name = ".".join(x.name for x in p.name.parts)

        # Pattern alias expansion (MVP): `pattern Foo = Some(_)` then `match x: Foo -> ...`.
        if p.args is None and hasattr(ctx.res, "pattern_aliases"):
            alias = getattr(ctx.res, "pattern_aliases", {}).get(name)
            if alias is not None:
                seen: set[str] = set()

                def expand(n: str, pat: ast.Pattern) -> ast.Pattern:
                    if n in seen:
                        raise LowerError(f"Cyclic pattern alias: {n}", p.span)
                    seen.add(n)
                    if isinstance(pat, ast.PConstructor):
                        nn = ".".join(x.name for x in pat.name.parts)
                        if pat.args is None:
                            nxt = getattr(ctx.res, "pattern_aliases", {}).get(nn)
                            if nxt is not None:
                                return expand(nn, nxt)
                    return pat

                return _lower_pattern(ctx, expand(name, alias))

        # Constructor is a value symbol.
        ctor = ctx.ctor_by_name.get(name)
        if ctor is None:
            # allow qualified ctor lookup by last segment
            ctor = ctx.ctor_by_name.get(p.name.parts[-1].name)
        if ctor is None:
            raise LowerError(f"Unknown constructor: {name}", p.span)
        args = [_lower_pattern(ctx, a) for a in (p.args or [])] or None
        return PCtor(ctor=ctor, args=args, span=p.span)
    raise LowerError("Unsupported pattern", p.span)


def _var(ctx: _Ctx, ident: ast.Ident) -> Expr:
    return _var_sym(_sym_of_ident(ctx, ident), ident.span)


def _var_sym(sym: SymbolId, span) -> Expr:
    from .hir import VarExpr

    return VarExpr(sym=sym, span=span)
