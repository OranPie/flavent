from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .diagnostics import EffectError, TypeError
from .hir import (
    AbortHandlerStmt,
    AssignStmt,
    AwaitEventExpr,
    BinaryExpr,
    Block,
    CallArgKw,
    CallArgPos,
    CallArgStar,
    CallArgStarStar,
    CallExpr,
    EmitStmt,
    Expr,
    ExprStmt,
    FnDecl,
    ForStmt,
    HandlerDecl,
    IfStmt,
    IndexExpr,
    LetStmt,
    LitExpr,
    LIndex,
    LMember,
    LVar,
    MatchArmExpr,
    MatchArmStmt,
    MatchExpr,
    MatchStmt,
    MemberExpr,
    Program,
    RecordLitExpr,
    ReturnStmt,
    RpcCallExpr,
    SectorDecl,
    StopStmt,
    TupleLitExpr,
    UnaryExpr,
    UndefExpr,
    VarExpr,
    YieldStmt,
    PVar,
    PBool,
    PWildcard,
    PCtor,
)
from .resolve import Resolution
from .symbols import Symbol, SymbolId, SymbolKind, TypeId


@dataclass(frozen=True, slots=True)
class _TMeta:
    id: int


@dataclass(frozen=True, slots=True)
class _TGen:
    id: int


T = object


@dataclass(slots=True)
class _TypeCtx:
    res: Resolution
    sym_by_id: dict[SymbolId, Symbol]
    type_name_by_id: dict[TypeId, str]
    type_id_by_name: dict[str, TypeId]
    type_alias: dict[TypeId, tuple[list[TypeId], T]]
    fn_sig: dict[SymbolId, tuple[list[T], T]]
    fn_param_meta: dict[SymbolId, list[tuple[SymbolId, str, T]]]
    fn_tparams: dict[SymbolId, list[TypeId]]
    fn_effect: dict[SymbolId, Optional[SymbolId]]
    ctor_sig: dict[SymbolId, tuple[list[TypeId], list[T], T]]
    record_fields: dict[TypeId, dict[str, T]]
    next_meta: int

    current_sector: Optional[SymbolId]
    expected_effect: Optional[SymbolId]

    env: dict[SymbolId, T]
    global_env: dict[SymbolId, T]
    meta_bindings: dict[int, T]
    meta_record_fields: dict[int, dict[str, T]]

    def fresh_meta(self) -> _TMeta:
        mid = self.next_meta
        self.next_meta += 1
        return _TMeta(mid)


@dataclass(frozen=True, slots=True)
class _Effect:
    kind: str  # 'pure' | 'sector'
    sector: Optional[SymbolId]


_PURE = _Effect(kind="pure", sector=None)


def check_program(hir: Program, res: Resolution) -> None:
    sym_by_id = {s.id: s for s in res.symbols}
    type_name_by_id = {s.id: s.name for s in res.symbols if s.kind == SymbolKind.TYPE}
    type_id_by_name = {s.name: s.id for s in res.symbols if s.kind == SymbolKind.TYPE}

    fn_sig: dict[SymbolId, tuple[list[T], T]] = {}
    fn_param_meta: dict[SymbolId, list[tuple[SymbolId, str, T]]] = {}
    fn_tparams: dict[SymbolId, list[TypeId]] = {}
    fn_effect: dict[SymbolId, Optional[SymbolId]] = {}

    type_alias: dict[TypeId, tuple[list[TypeId], T]] = {}
    for td in hir.types:
        if hasattr(td.rhs, "target"):
            sym = sym_by_id.get(td.sym)
            tps: list[TypeId] = []
            if sym is not None:
                raw = (sym.data or {}).get("type_param_ids")
                if isinstance(raw, list) and all(isinstance(x, int) for x in raw):
                    tps = list(raw)
            type_alias[td.sym] = (tps, _lower_type(type_id_by_name, td.rhs.target, tparams=tps))

    ctor_sig: dict[SymbolId, tuple[list[TypeId], list[T], T]] = {}
    for td in hir.types:
        if hasattr(td.rhs, "variants"):
            # Sum type: collect ctor signatures.
            sym = sym_by_id.get(td.sym)
            tps: list[TypeId] = []
            if sym is not None:
                data = sym.data or {}
                raw = data.get("type_param_ids")
                if isinstance(raw, list) and all(isinstance(x, int) for x in raw):
                    tps = list(raw)

            ret_t: T
            if tps:
                ret_t = ("app", td.sym, [_TGen(x) for x in tps])
            else:
                ret_t = ("con", td.sym)

            for v in td.rhs.variants:
                payload = v.payload or []
                pts = [_lower_type(type_id_by_name, t, tparams=tps) for t in payload]
                ctor_sig[v.ctor] = (tps, pts, ret_t)

    record_fields: dict[TypeId, dict[str, T]] = {}
    for td in hir.types:
        if hasattr(td.rhs, "fields"):
            tid = td.sym
            sym = sym_by_id.get(tid)
            tps: list[TypeId] = []
            if sym is not None:
                raw = (sym.data or {}).get("type_param_ids")
                if isinstance(raw, list) and all(isinstance(x, int) for x in raw):
                    tps = list(raw)

            fields: dict[str, T] = {}
            for f in td.rhs.fields:
                fields[f.name] = _lower_type(type_id_by_name, f.ty, tparams=tps)
            record_fields[tid] = fields

    def _collect_scheme_for(fn_sym: SymbolId) -> None:
        sym = sym_by_id.get(fn_sym)
        if sym is None:
            return
        data = sym.data or {}
        tps = data.get("type_param_ids")
        if isinstance(tps, list) and all(isinstance(x, int) for x in tps):
            fn_tparams[fn_sym] = list(tps)

    for fn in hir.fns:
        _collect_scheme_for(fn.sym)
        tps = fn_tparams.get(fn.sym)
        pts = _lower_type_list(type_id_by_name, fn.params, tparams=tps)
        fn_sig[fn.sym] = (pts, _lower_type(type_id_by_name, fn.retType, tparams=tps))
        fn_param_meta[fn.sym] = [(p.sym, p.kind, _lower_type(type_id_by_name, p.ty, tparams=tps)) for p in fn.params]
        fn_effect[fn.sym] = _fn_effect(sym_by_id, fn.sym, owner_sector=fn.ownerSector)

    for sec in hir.sectors:
        for fn in sec.fns:
            _collect_scheme_for(fn.sym)
            tps = fn_tparams.get(fn.sym)
            pts = _lower_type_list(type_id_by_name, fn.params, tparams=tps)
            fn_sig[fn.sym] = (pts, _lower_type(type_id_by_name, fn.retType, tparams=tps))
            fn_param_meta[fn.sym] = [(p.sym, p.kind, _lower_type(type_id_by_name, p.ty, tparams=tps)) for p in fn.params]
            fn_effect[fn.sym] = _fn_effect(sym_by_id, fn.sym, owner_sector=sec.sym)

    ctx0 = _TypeCtx(
        res=res,
        sym_by_id=sym_by_id,
        type_name_by_id=type_name_by_id,
        type_id_by_name=type_id_by_name,
        type_alias=type_alias,
        fn_sig=fn_sig,
        fn_param_meta=fn_param_meta,
        fn_tparams=fn_tparams,
        fn_effect=fn_effect,
        ctor_sig=ctor_sig,
        record_fields=record_fields,
        next_meta=1,
        current_sector=None,
        expected_effect=None,
        env={},
        global_env={},
        meta_bindings={},
        meta_record_fields={},
    )

    # Top-level values: const/let must be pure per REF2; need is allowed.
    for vd in [*hir.consts, *hir.globals]:
        t, eff = _infer_expr(ctx0, vd.expr, expected=None)
        if eff.kind != "pure":
            raise EffectError("top-level initializer must be pure", vd.span)
        ctx0.global_env[vd.sym] = t

    for vd in hir.needs:
        t, _ = _infer_expr(ctx0, vd.expr, expected=None)
        ctx0.global_env[vd.sym] = t

    for fn in hir.fns:
        _check_fn(ctx0, fn, owner_sector=None)

    for sec in hir.sectors:
        # Sector `let` declarations live in sector state and are assignable from handlers.
        # Record them in global_env so AssignStmt can typecheck them.
        for vd in sec.lets:
            t, eff = _infer_expr(ctx0, vd.expr, expected=None)
            if eff.kind != "pure":
                raise EffectError("sector let initializer must be pure", vd.span)
            ctx0.global_env[vd.sym] = t
        for fn in sec.fns:
            _check_fn(ctx0, fn, owner_sector=sec.sym)
        for h in sec.handlers:
            _check_handler(ctx0, h, owner_sector=sec.sym)


def _lower_type_list(type_id_by_name: dict[str, TypeId], params: list, *, tparams: list[TypeId] | None = None) -> list[T]:
    return [_lower_type(type_id_by_name, p.ty, tparams=tparams) for p in params]


def _constrain_record_field(ctx: _TypeCtx, mid: int, field: str, *, expected: Optional[T], span) -> T:
    fields = ctx.meta_record_fields.setdefault(mid, {})
    ft = fields.get(field)
    if ft is None:
        ft = expected if expected is not None else ctx.fresh_meta()
        fields[field] = ft
        return ft
    if expected is not None:
        _unify(ctx, ft, expected, span)
    return ft


def _instantiate(ctx: _TypeCtx, t: T) -> T:
    subst: dict[int, _TMeta] = {}

    def go(x: T) -> T:
        x = _prune(ctx, x)
        if isinstance(x, _TGen):
            m = subst.get(x.id)
            if m is None:
                m = ctx.fresh_meta()
                subst[x.id] = m
            return m
        if isinstance(x, tuple) and x:
            tag = x[0]
            if tag == "app":
                return ("app", x[1], [go(a) for a in x[2]])
            if tag == "fn":
                return x
            if tag == "ctor":
                return x
        return x

    return go(t)


def _lower_type(type_id_by_name: dict[str, TypeId], tr, *, tparams: list[TypeId] | None = None) -> T:
    if tr is None:
        unit = type_id_by_name.get("Unit")
        if unit is None:
            return ("con", 0)
        return ("con", unit)
    if hasattr(tr, "base"):
        base = tr.base
        args = [_lower_type(type_id_by_name, a, tparams=tparams) for a in tr.args]
        return ("app", base, args)
    if hasattr(tr, "id"):
        if tparams is not None and tr.id in tparams:
            return _TGen(tr.id)
        return ("con", tr.id)
    raise TypeError("Unsupported type", tr.span)


def _expand_type_alias(ctx: _TypeCtx, t: T, *, span) -> T:
    def subst_gens(x: T, subst: dict[int, T]) -> T:
        x = _prune(ctx, x)
        if isinstance(x, _TGen):
            return subst.get(x.id, x)
        if isinstance(x, tuple) and x:
            tag = x[0]
            if tag == "app":
                return ("app", x[1], [subst_gens(a, subst) for a in x[2]])
            if tag == "tuple":
                return ("tuple", [subst_gens(a, subst) for a in x[1]])
        return x

    seen: set[int] = set()
    cur = _prune(ctx, t)
    while isinstance(cur, tuple) and cur and cur[0] in ("con", "app"):
        tid = cur[1]
        ali = ctx.type_alias.get(tid)
        if ali is None:
            break
        if tid in seen:
            raise TypeError("cyclic type alias", span)
        seen.add(tid)
        tps, target = ali
        subst: dict[int, T] = {}
        if tps:
            if cur[0] != "app" or len(cur[2]) != len(tps):
                raise TypeError("type mismatch", span)
            for pid, arg in zip(tps, cur[2], strict=True):
                subst[int(pid)] = arg
        cur = subst_gens(target, subst)
        cur = _prune(ctx, cur)
    return cur


def _fn_effect(sym_by_id: dict[SymbolId, Symbol], fn_sym: SymbolId, *, owner_sector: Optional[SymbolId]) -> Optional[SymbolId]:
    if owner_sector is not None:
        return owner_sector
    sym = sym_by_id.get(fn_sym)
    if sym is None:
        return None
    data = sym.data or {}
    sec = data.get("sector")
    if isinstance(sec, int):
        return sec
    return None


def _check_fn(ctx0: _TypeCtx, fn: FnDecl, *, owner_sector: Optional[SymbolId]) -> None:
    expected = _fn_effect(ctx0.sym_by_id, fn.sym, owner_sector=owner_sector)
    tps = ctx0.fn_tparams.get(fn.sym)

    ctx = _TypeCtx(
        res=ctx0.res,
        sym_by_id=ctx0.sym_by_id,
        type_name_by_id=ctx0.type_name_by_id,
        type_id_by_name=ctx0.type_id_by_name,
        type_alias=ctx0.type_alias,
        fn_sig=ctx0.fn_sig,
        fn_param_meta=ctx0.fn_param_meta,
        fn_tparams=ctx0.fn_tparams,
        fn_effect=ctx0.fn_effect,
        ctor_sig=ctx0.ctor_sig,
        record_fields=ctx0.record_fields,
        next_meta=ctx0.next_meta,
        current_sector=owner_sector,
        expected_effect=expected,
        env={},
        global_env=ctx0.global_env,
        meta_bindings={},
        meta_record_fields=dict(ctx0.meta_record_fields),
    )

    for p in fn.params:
        ctx.env[p.sym] = _lower_type(ctx.type_id_by_name, p.ty, tparams=tps)

    eff = _check_block(ctx, fn.body, expected_ret=_lower_type(ctx.type_id_by_name, fn.retType, tparams=tps), in_handler=False)

    if expected is None:
        if eff.kind != "pure":
            raise EffectError("pure function body has effects", fn.span)
    else:
        if eff.kind == "sector" and eff.sector != expected:
            raise EffectError("function body mixes sectors", fn.span)


def _check_handler(ctx0: _TypeCtx, h: HandlerDecl, *, owner_sector: SymbolId) -> None:
    ctx = _TypeCtx(
        res=ctx0.res,
        sym_by_id=ctx0.sym_by_id,
        type_name_by_id=ctx0.type_name_by_id,
        type_id_by_name=ctx0.type_id_by_name,
        type_alias=ctx0.type_alias,
        fn_sig=ctx0.fn_sig,
        fn_param_meta=ctx0.fn_param_meta,
        fn_tparams=ctx0.fn_tparams,
        fn_effect=ctx0.fn_effect,
        ctor_sig=ctx0.ctor_sig,
        record_fields=ctx0.record_fields,
        next_meta=ctx0.next_meta,
        current_sector=owner_sector,
        expected_effect=owner_sector,
        env={},
        global_env=ctx0.global_env,
        meta_bindings={},
        meta_record_fields=dict(ctx0.meta_record_fields),
    )

    if h.binder is not None:
        ctx.env[h.binder] = ("con", h.eventType)

    _check_block(ctx, h.body, expected_ret=("con", ctx.type_id_by_name.get("Unit", 0)), in_handler=True)


def _check_block(ctx: _TypeCtx, b: Block, *, expected_ret: T, in_handler: bool) -> _Effect:
    eff = _PURE
    for st in b.stmts:
        se = _check_stmt(ctx, st, expected_ret=expected_ret, in_handler=in_handler)
        eff = _join_effect(eff, se, st.span)
    return eff


def _check_stmt(ctx: _TypeCtx, st, *, expected_ret: T, in_handler: bool) -> _Effect:
    if isinstance(st, LetStmt):
        t, e = _infer_expr(ctx, st.expr, expected=None)
        ctx.env[st.sym] = t
        return e

    if isinstance(st, AssignStmt):
        t_lhs: T | None = None
        if isinstance(st.target, LVar):
            sym = st.target.sym
            t_lhs = ctx.env.get(sym)
            if t_lhs is None:
                # Allow assignment to sector-level `let` variables.
                t_lhs = ctx.global_env.get(sym)
            if t_lhs is None:
                raise TypeError("assign to unknown var", st.span)

        t_rhs, e_rhs = _infer_expr(ctx, st.expr, expected=t_lhs)
        if t_lhs is not None:
            _unify(ctx, t_lhs, t_rhs, st.span)
        return e_rhs

    if isinstance(st, EmitStmt):
        if ctx.current_sector is None:
            raise EffectError("emit outside sector", st.span)
        t, _ = _infer_expr(ctx, st.expr, expected=None)
        if not _is_event_type(ctx, t):
            raise TypeError("emit expects Event.* type", st.span)
        return _sector_eff(ctx.current_sector)

    if isinstance(st, ReturnStmt):
        t, e = _infer_expr(ctx, st.expr, expected=expected_ret)
        _unify(ctx, expected_ret, t, st.span)
        return e

    if isinstance(st, AbortHandlerStmt):
        if not in_handler:
            raise EffectError("abort_handler outside handler", st.span)
        if st.cause is not None:
            _infer_expr(ctx, st.cause, expected=None)
        return _sector_eff(ctx.current_sector)

    if isinstance(st, StopStmt) or isinstance(st, YieldStmt):
        if ctx.current_sector is None:
            raise EffectError("stop/yield outside sector", st.span)
        return _sector_eff(ctx.current_sector)

    if isinstance(st, ExprStmt):
        _, e = _infer_expr(ctx, st.expr, expected=None)
        return e

    if isinstance(st, IfStmt):
        t_cond, e_cond = _infer_expr(ctx, st.cond, expected=("con", ctx.type_id_by_name.get("Bool", 0)))
        _unify(ctx, ("con", ctx.type_id_by_name.get("Bool", 0)), t_cond, st.span)
        e_then = _check_block(ctx, st.thenBlock, expected_ret=expected_ret, in_handler=in_handler)
        e_else = _PURE
        if st.elseBlock is not None:
            e_else = _check_block(ctx, st.elseBlock, expected_ret=expected_ret, in_handler=in_handler)
        return _join_effect(_join_effect(e_cond, e_then, st.span), e_else, st.span)

    if isinstance(st, ForStmt):
        if ctx.current_sector is None:
            raise EffectError("for outside sector", st.span)
        _, e_it = _infer_expr(ctx, st.iterable, expected=None)
        ctx.env[st.binder] = ctx.fresh_meta()
        e_body = _check_block(ctx, st.body, expected_ret=expected_ret, in_handler=in_handler)
        return _join_effect(e_it, e_body, st.span)

    if isinstance(st, MatchStmt):
        t_scrut, e_scrut = _infer_expr(ctx, st.scrutinee, expected=None)
        e_all = e_scrut
        for arm in st.arms:
            saved = dict(ctx.env)
            _bind_pattern(ctx, arm.pat, t_scrut, arm.span)
            e_arm = _check_block(ctx, arm.body, expected_ret=expected_ret, in_handler=in_handler)
            e_all = _join_effect(e_all, e_arm, arm.span)
            ctx.env = saved
        return e_all

    raise TypeError("unsupported statement in typecheck", st.span)


def _infer_expr(ctx: _TypeCtx, e: Expr, *, expected: Optional[T]) -> tuple[T, _Effect]:
    if isinstance(e, UndefExpr):
        return ctx.fresh_meta(), _PURE

    if isinstance(e, LitExpr):
        return _lit_type(ctx, e), _PURE

    if isinstance(e, VarExpr):
        t = ctx.env.get(e.sym)
        if t is not None:
            return t, _PURE

        gt = ctx.global_env.get(e.sym)
        if gt is not None:
            return gt, _PURE

        sym = ctx.sym_by_id.get(e.sym)
        if sym is None:
            raise TypeError("unknown symbol", e.span)
        if sym.kind == SymbolKind.FN:
            return ("fn", e.sym), _PURE
        if sym.kind == SymbolKind.CTOR:
            # Default: a constructor reference is a ctor value (callable via `Ctor(...)`).
            # This is required for examples like `None()`.
            if expected is not None:
                # Contextual: allow using a nullary constructor as a value.
                # Example: `fn nil[T]() -> List[T] = Nil`.
                sig = ctx.ctor_sig.get(e.sym)
                if sig is not None:
                    _, pts0, rt0 = sig
                    if not pts0:
                        rt = _instantiate(ctx, rt0)
                        _unify(ctx, expected, rt, e.span)
                        return rt, _PURE

            # Allow using the nullary ctor `None` as a value.
            # This is important for ergonomic Option code: `unwrapOr(None, 0)`.
            if sym.name == "None" and expected is not None:
                t_opt = _prune(ctx, expected)
                if isinstance(t_opt, _TMeta):
                    bound = _option_type(ctx)
                    ctx.meta_bindings[t_opt.id] = bound
                    t_opt = bound
                if not _is_option_type(ctx, t_opt):
                    raise TypeError("None must construct Option", e.span)
                return t_opt, _PURE
            return ("ctor", e.sym), _PURE
        if sym.kind in (SymbolKind.VAR, SymbolKind.CONST, SymbolKind.NEED):
            m = ctx.fresh_meta()
            ctx.global_env[e.sym] = m
            return m, _PURE
        raise TypeError("unsupported var usage", e.span)

    if isinstance(e, CallExpr):
        return _infer_call(ctx, e, expected=expected)

    if isinstance(e, RpcCallExpr):
        if ctx.current_sector is None:
            raise EffectError("rpc/call outside sector", e.span)
        sig = ctx.fn_sig.get(e.fn)
        if sig is None:
            raise TypeError("unknown rpc target", e.span)
        arg_types = sig[0]
        if len(arg_types) != len(e.args):
            raise TypeError("arity mismatch", e.span)
        eff = _sector_eff(ctx.current_sector)
        for a, pt in zip(e.args, arg_types, strict=True):
            at, ae = _infer_expr(ctx, a, expected=pt)
            _unify(ctx, pt, at, a.span)
            eff = _join_effect(eff, ae, a.span)
        if not e.awaitResult:
            return ("con", ctx.type_id_by_name.get("Unit", 0)), eff
        return sig[1], eff

    if isinstance(e, AwaitEventExpr):
        if ctx.current_sector is None:
            raise EffectError("await outside sector", e.span)
        return ("con", e.typeId), _sector_eff(ctx.current_sector)

    if isinstance(e, MemberExpr):
        ot, oe = _infer_expr(ctx, e.object, expected=None)
        otp = _prune(ctx, ot)
        if isinstance(otp, tuple) and otp:
            tid: TypeId | None = None
            subst: dict[int, T] = {}
            if otp[0] == "con":
                tid = otp[1]
            elif otp[0] == "app":
                tid = otp[1]
                sym = ctx.sym_by_id.get(tid)
                tps = (sym.data or {}).get("type_param_ids") if sym is not None else None
                if isinstance(tps, list) and all(isinstance(x, int) for x in tps):
                    for pid, arg in zip(tps, otp[2], strict=False):
                        subst[int(pid)] = arg

            fields0 = ctx.record_fields.get(tid) if tid is not None else None
            if fields0 is not None:
                ft0 = fields0.get(e.field)
                if ft0 is None:
                    raise TypeError("unknown record field", e.span)
                ft = ft0
                if subst:
                    # local helper to avoid import cycles
                    def sg(x: T) -> T:
                        x = _prune(ctx, x)
                        if isinstance(x, _TGen):
                            return subst.get(x.id, x)
                        if isinstance(x, tuple) and x and x[0] == "app":
                            return ("app", x[1], [sg(a) for a in x[2]])
                        if isinstance(x, tuple) and x and x[0] == "tuple":
                            return ("tuple", [sg(a) for a in x[1]])
                        return x

                    ft = sg(ft0)
                if expected is not None:
                    _unify(ctx, expected, ft, e.span)
                return ft, oe
        if isinstance(otp, _TMeta):
            ft = _constrain_record_field(ctx, otp.id, e.field, expected=expected, span=e.span)
            return ft, oe
        return ctx.fresh_meta(), oe

    if isinstance(e, IndexExpr):
        ot, oe = _infer_expr(ctx, e.object, expected=None)
        it, ie = _infer_expr(ctx, e.index, expected=None)
        return ("index", ot, it), _join_effect(oe, ie, e.span)

    if isinstance(e, UnaryExpr):
        it, ie = _infer_expr(ctx, e.expr, expected=None)
        return it, ie

    if isinstance(e, BinaryExpr):
        lt, le = _infer_expr(ctx, e.left, expected=None)
        rt, re = _infer_expr(ctx, e.right, expected=None)
        eff = _join_effect(le, re, e.span)

        int_id = ctx.type_id_by_name.get("Int", 0)
        float_id = ctx.type_id_by_name.get("Float", 0)

        lt0 = _prune(ctx, lt)
        rt0 = _prune(ctx, rt)

        def is_int(t: T) -> bool:
            return isinstance(t, tuple) and t and t[0] == "con" and t[1] == int_id

        def is_float(t: T) -> bool:
            return isinstance(t, tuple) and t and t[0] == "con" and t[1] == float_id

        # Numeric promotion: allow Int <-> Float mixing for arithmetic ops.
        if e.op in ("+", "-", "*", "/"):
            if (is_int(lt0) and is_float(rt0)) or (is_float(lt0) and is_int(rt0)):
                return ("con", float_id), eff

        # Default: operands must unify.
        _unify(ctx, lt, rt, e.span)

        if e.op in ("==", "!=", "<", "<=", ">", ">="):
            return ("con", ctx.type_id_by_name.get("Bool", 0)), eff

        if e.op in ("and", "or"):
            _unify(ctx, lt, ("con", ctx.type_id_by_name.get("Bool", 0)), e.left.span)
            _unify(ctx, rt, ("con", ctx.type_id_by_name.get("Bool", 0)), e.right.span)
            return ("con", ctx.type_id_by_name.get("Bool", 0)), eff

        return lt, eff

    if isinstance(e, TupleLitExpr):
        eff = _PURE
        if not e.items:
            return ("con", ctx.type_id_by_name.get("Unit", 0)), eff
        ts: list[T] = []
        for it in e.items:
            t, te = _infer_expr(ctx, it, expected=None)
            ts.append(t)
            eff = _join_effect(eff, te, it.span)
        return ("tuple", ts), eff

    if isinstance(e, RecordLitExpr):
        eff = _PURE
        exp = _prune(ctx, expected) if expected is not None else None
        if isinstance(exp, _TMeta):
            exp = None

        def _subst_gens(t: T, subst: dict[int, T]) -> T:
            t = _prune(ctx, t)
            if isinstance(t, _TGen):
                return subst.get(t.id, t)
            if isinstance(t, tuple) and t:
                tag = t[0]
                if tag == "app":
                    return ("app", t[1], [_subst_gens(a, subst) for a in t[2]])
                if tag == "tuple":
                    return ("tuple", [_subst_gens(a, subst) for a in t[1]])
            return t

        if isinstance(exp, tuple) and exp:
            tid: TypeId | None = None
            subst: dict[int, T] = {}
            if exp[0] == "con" and exp[1] in ctx.record_fields:
                tid = exp[1]
            elif exp[0] == "app" and exp[1] in ctx.record_fields:
                tid = exp[1]
                sym = ctx.sym_by_id.get(tid)
                tps = (sym.data or {}).get("type_param_ids") if sym is not None else None
                if isinstance(tps, list) and all(isinstance(x, int) for x in tps):
                    for pid, arg in zip(tps, exp[2], strict=False):
                        subst[int(pid)] = arg

            if tid is not None:
                fields0 = ctx.record_fields[tid]
                fields = {k: _subst_gens(v, subst) for k, v in fields0.items()}
                seen: set[str] = set()
                for it in e.items:
                    ft = fields.get(it.key)
                    if ft is None:
                        raise TypeError("unknown record field", it.span)
                    vt, ve = _infer_expr(ctx, it.value, expected=ft)
                    _unify(ctx, ft, vt, it.span)
                    eff = _join_effect(eff, ve, it.span)
                    seen.add(it.key)
                if len(seen) != len(fields):
                    raise TypeError("missing record field", e.span)
                return exp, eff

        m = ctx.fresh_meta()
        for it in e.items:
            vt, ve = _infer_expr(ctx, it.value, expected=None)
            _constrain_record_field(ctx, m.id, it.key, expected=vt, span=it.span)
            eff = _join_effect(eff, ve, it.span)
        return m, eff

    if isinstance(e, MatchExpr):
        t_scrut, e_scrut = _infer_expr(ctx, e.scrutinee, expected=None)
        out_t = ctx.fresh_meta()
        e_all = e_scrut
        for arm in e.arms:
            saved = dict(ctx.env)
            _bind_pattern(ctx, arm.pat, t_scrut, arm.span)
            bt, be = _infer_expr(ctx, arm.body, expected=out_t)
            _unify(ctx, out_t, bt, arm.span)
            e_all = _join_effect(e_all, be, arm.span)
            ctx.env = saved
        return out_t, e_all

    raise TypeError("unsupported expr in typecheck", e.span)


def _infer_call(ctx: _TypeCtx, e: CallExpr, *, expected: Optional[T]) -> tuple[T, _Effect]:
    callee_t, callee_e = _infer_expr(ctx, e.callee, expected=None)

    if isinstance(callee_t, tuple) and callee_t and callee_t[0] == "fn":
        fn_sym = callee_t[1]
        sig = ctx.fn_sig.get(fn_sym)
        if sig is None:
            raise TypeError("unknown function", e.span)

        params, ret = sig
        meta0 = ctx.fn_param_meta.get(fn_sym) or []
        if fn_sym in ctx.fn_tparams:
            params = [_instantiate(ctx, p) for p in params]
            ret = _instantiate(ctx, ret)
            meta0 = [(psym, kind, _instantiate(ctx, pt)) for (psym, kind, pt) in meta0]

        # Build parameter table.
        fixed: list[tuple[str, T, Span]] = []
        varargs: tuple[T, Span] | None = None
        varkw: tuple[T, Span] | None = None
        for (psym, kind, pt) in meta0:
            name = ctx.sym_by_id.get(psym).name if ctx.sym_by_id.get(psym) else ""
            if kind == "varargs":
                varargs = (pt, ctx.sym_by_id.get(psym).span if ctx.sym_by_id.get(psym) else e.span)
            elif kind == "varkw":
                varkw = (pt, ctx.sym_by_id.get(psym).span if ctx.sym_by_id.get(psym) else e.span)
            else:
                fixed.append((name, pt, ctx.sym_by_id.get(psym).span if ctx.sym_by_id.get(psym) else e.span))

        fn_eff = ctx.fn_effect.get(fn_sym)
        if fn_eff is not None:
            if ctx.current_sector is None:
                raise EffectError("calling sector function from pure context", e.span)
            if ctx.current_sector != fn_eff:
                raise EffectError("direct cross-sector call; use rpc/call", e.span)

        # Collect call arguments.
        pos: list[tuple[Expr, Span]] = []
        kws: list[tuple[str, Expr, Span]] = []
        star: tuple[Expr, Span] | None = None
        starstar: tuple[Expr, Span] | None = None
        saw_kw = False

        for a in e.args:
            if isinstance(a, CallArgPos):
                if saw_kw:
                    raise TypeError("positional argument after keyword", a.span)
                pos.append((a.value, a.span))
            elif not isinstance(a, (CallArgKw, CallArgStar, CallArgStarStar)):
                if saw_kw:
                    raise TypeError("positional argument after keyword", a.span)
                pos.append((a, a.span))
            elif isinstance(a, CallArgKw):
                saw_kw = True
                kws.append((a.name, a.value, a.span))
            elif isinstance(a, CallArgStar):
                if star is not None or saw_kw:
                    raise TypeError("invalid *args position", a.span)
                saw_kw = True
                star = (a.value, a.span)
            elif isinstance(a, CallArgStarStar):
                if starstar is not None:
                    raise TypeError("duplicate **kwargs", a.span)
                saw_kw = True
                starstar = (a.value, a.span)
            else:
                raise TypeError("unsupported call argument", a.span)

        eff = callee_e

        # Assign fixed params from positional.
        provided: dict[str, bool] = {}
        i = 0
        for (nm, pt, _sp) in fixed:
            if i < len(pos):
                ex, sp = pos[i]
                at, ae = _infer_expr(ctx, ex, expected=pt)
                _unify(ctx, pt, at, sp)
                eff = _join_effect(eff, ae, sp)
                provided[nm] = True
                i += 1
            else:
                provided[nm] = False

        # Extra positional go to varargs.
        if i < len(pos):
            if varargs is None:
                raise TypeError("arity mismatch", e.span)
            vt, _vsp = varargs
            # If varargs is List[T], unify each extra positional with T; otherwise unify with vt.
            list_id = ctx.type_id_by_name.get("List")
            elem_t: T | None = None
            vt0 = _prune(ctx, vt)
            if isinstance(vt0, tuple) and vt0 and vt0[0] == "app" and list_id is not None and vt0[1] == list_id and len(vt0[2]) == 1:
                elem_t = vt0[2][0]
            for j in range(i, len(pos)):
                ex, sp = pos[j]
                expect_t = elem_t if elem_t is not None else vt
                at, ae = _infer_expr(ctx, ex, expected=expect_t)
                _unify(ctx, expect_t, at, sp)
                eff = _join_effect(eff, ae, sp)

        # Process keyword args.
        fixed_map: dict[str, T] = {nm: pt for (nm, pt, _sp) in fixed}
        for (nm, ex, sp) in kws:
            if nm in fixed_map:
                if provided.get(nm):
                    raise TypeError("duplicate keyword", sp)
                pt = fixed_map[nm]
                at, ae = _infer_expr(ctx, ex, expected=pt)
                _unify(ctx, pt, at, sp)
                eff = _join_effect(eff, ae, sp)
                provided[nm] = True
            else:
                if varkw is None:
                    raise TypeError("unknown keyword", sp)
                kt = varkw[0]
                map_id = ctx.type_id_by_name.get("Map")
                vt = kt
                vt0 = _prune(ctx, kt)
                if isinstance(vt0, tuple) and vt0 and vt0[0] == "app" and map_id is not None and vt0[1] == map_id and len(vt0[2]) == 2:
                    vt = vt0[2][1]
                at, ae = _infer_expr(ctx, ex, expected=vt)
                _unify(ctx, vt, at, sp)
                eff = _join_effect(eff, ae, sp)

        # Ensure all fixed params provided.
        for (nm, _pt, sp) in fixed:
            if not provided.get(nm, False):
                raise TypeError("missing argument", sp)

        # Handle *args (restricted: contributes to varargs only).
        if star is not None:
            if varargs is None:
                raise TypeError("unexpected *args", star[1])
            vt, _ = varargs
            at, ae = _infer_expr(ctx, star[0], expected=vt)
            _unify(ctx, vt, at, star[1])
            eff = _join_effect(eff, ae, star[1])

        # Handle **kwargs (restricted: must have varkw).
        if starstar is not None:
            if varkw is None:
                raise TypeError("unexpected **kwargs", starstar[1])
            kt, _ = varkw
            at, ae = _infer_expr(ctx, starstar[0], expected=kt)
            _unify(ctx, kt, at, starstar[1])
            eff = _join_effect(eff, ae, starstar[1])

        return ret, eff

    if isinstance(callee_t, tuple) and callee_t and callee_t[0] == "ctor":
        ctor_sym = callee_t[1]
        return _infer_ctor_call(ctx, ctor_sym, e, expected=expected)

    raise TypeError("call expects function or constructor", e.span)


def _infer_ctor_call(ctx: _TypeCtx, ctor_sym: SymbolId, e: CallExpr, *, expected: Optional[T]) -> tuple[T, _Effect]:
    name = ctx.sym_by_id.get(ctor_sym).name if ctx.sym_by_id.get(ctor_sym) else ""

    pos_args: list[tuple[Expr, Span]] = []
    for a in e.args:
        if isinstance(a, CallArgPos):
            pos_args.append((a.value, a.span))
        elif not isinstance(a, (CallArgKw, CallArgStar, CallArgStarStar)):
            pos_args.append((a, a.span))
        else:
            raise TypeError("constructor call expects positional args only", a.span)

    if name in ("Ok", "Err"):
        t_res: T
        if expected is None:
            t_res = _result_type(ctx)
        else:
            t_res = _prune(ctx, expected)
            if isinstance(t_res, _TMeta):
                bound = _result_type(ctx)
                ctx.meta_bindings[t_res.id] = bound
                t_res = bound
        if not _is_result_type(ctx, t_res):
            raise TypeError("Ok/Err must construct Result", e.span)
        t_ok, t_err = _result_args(t_res)
        if name == "Ok":
            if len(pos_args) != 1:
                raise TypeError("Ok expects 1 arg", e.span)
            at, ae = _infer_expr(ctx, pos_args[0][0], expected=t_ok)
            _unify(ctx, t_ok, at, pos_args[0][1])
            return t_res, ae
        if len(pos_args) != 1:
            raise TypeError("Err expects 1 arg", e.span)
        at, ae = _infer_expr(ctx, pos_args[0][0], expected=t_err)
        _unify(ctx, t_err, at, pos_args[0][1])
        return t_res, ae

    if name in ("Some", "None"):
        t_opt: T
        if expected is None:
            t_opt = _option_type(ctx)
        else:
            t_opt = _prune(ctx, expected)
            if isinstance(t_opt, _TMeta):
                bound = _option_type(ctx)
                ctx.meta_bindings[t_opt.id] = bound
                t_opt = bound
        if not _is_option_type(ctx, t_opt):
            raise TypeError("Some/None must construct Option", e.span)
        t_inner = _option_arg(t_opt)
        if name == "None":
            if pos_args:
                raise TypeError("None expects 0 args", e.span)
            return t_opt, _PURE
        if len(pos_args) != 1:
            raise TypeError("Some expects 1 arg", e.span)
        at, ae = _infer_expr(ctx, pos_args[0][0], expected=t_inner)
        _unify(ctx, t_inner, at, pos_args[0][1])
        return t_opt, ae

    sig = ctx.ctor_sig.get(ctor_sym)
    if sig is None:
        raise TypeError("unknown constructor", e.span)

    _, pts0, rt0 = sig
    pts = [_instantiate(ctx, p) for p in pts0]
    rt = _instantiate(ctx, rt0)

    if expected is not None:
        _unify(ctx, expected, rt, e.span)

    if len(pts) != len(pos_args):
        raise TypeError("arity mismatch", e.span)

    eff = _PURE
    for (a, sp), pt in zip(pos_args, pts, strict=True):
        at, ae = _infer_expr(ctx, a, expected=pt)
        _unify(ctx, pt, at, sp)
        eff = _join_effect(eff, ae, sp)
    return rt, eff


def _result_type(ctx: _TypeCtx) -> T:
    base = ctx.type_id_by_name.get("Result")
    if base is None:
        raise TypeError("missing builtin Result", ctx.res.program.span)
    return ("app", base, [ctx.fresh_meta(), ctx.fresh_meta()])


def _option_type(ctx: _TypeCtx) -> T:
    base = ctx.type_id_by_name.get("Option")
    if base is None:
        raise TypeError("missing builtin Option", ctx.res.program.span)
    return ("app", base, [ctx.fresh_meta()])


def _is_result_type(ctx: _TypeCtx, t: T) -> bool:
    t = _prune(ctx, t)
    return isinstance(t, tuple) and len(t) == 3 and t[0] == "app" and t[1] == ctx.type_id_by_name.get("Result")


def _result_args(t: T) -> tuple[T, T]:
    t = t  # already pruned at call sites
    return t[2][0], t[2][1]


def _is_option_type(ctx: _TypeCtx, t: T) -> bool:
    t = _prune(ctx, t)
    return isinstance(t, tuple) and len(t) == 3 and t[0] == "app" and t[1] == ctx.type_id_by_name.get("Option")


def _option_arg(t: T) -> T:
    t = t  # already pruned at call sites
    return t[2][0]


def _bind_pattern(ctx: _TypeCtx, pat, scrut_t: T, span) -> None:
    if isinstance(pat, PWildcard):
        return
    if isinstance(pat, PBool):
        _unify(ctx, ("con", ctx.type_id_by_name.get("Bool", 0)), scrut_t, span)
        return
    if isinstance(pat, PVar):
        ctx.env[pat.sym] = scrut_t
        return
    if isinstance(pat, PCtor):
        sig = ctx.ctor_sig.get(pat.ctor)
        if sig is None:
            return
        _, pts0, rt0 = sig
        pts = [_instantiate(ctx, p) for p in pts0]
        rt = _instantiate(ctx, rt0)
        _unify(ctx, scrut_t, rt, span)

        args = pat.args or []
        if len(args) != len(pts):
            raise TypeError("arity mismatch", span)
        for ap, pt in zip(args, pts, strict=True):
            _bind_pattern(ctx, ap, pt, span)
        return


def _lit_type(ctx: _TypeCtx, e: LitExpr) -> T:
    k = e.lit.kind
    if k == "LitInt":
        return ("con", ctx.type_id_by_name.get("Int", 0))
    if k == "LitFloat":
        return ("con", ctx.type_id_by_name.get("Float", 0))
    if k == "LitBool":
        return ("con", ctx.type_id_by_name.get("Bool", 0))
    if k == "LitStr":
        return ("con", ctx.type_id_by_name.get("Str", 0))
    if k == "LitBytes":
        return ("con", ctx.type_id_by_name.get("Bytes", 0))
    return ("con", ctx.type_id_by_name.get("Unit", 0))


def _is_event_type(ctx: _TypeCtx, t: T) -> bool:
    t = _prune(ctx, t)
    if isinstance(t, tuple) and len(t) == 2 and t[0] == "con":
        name = ctx.type_name_by_id.get(t[1], "")
        return name.startswith("Event.")
    return False


def _sector_eff(sector: Optional[SymbolId]) -> _Effect:
    return _Effect(kind="sector", sector=sector)


def _join_effect(a: _Effect, b: _Effect, span) -> _Effect:
    if a.kind == "pure":
        return b
    if b.kind == "pure":
        return a
    if a.sector == b.sector:
        return a
    raise EffectError("mixed sectors in one expression", span)


def _prune(ctx: _TypeCtx, t: T) -> T:
    if isinstance(t, _TMeta):
        bound = ctx.meta_bindings.get(t.id)
        if bound is None:
            return t
        pr = _prune(ctx, bound)
        ctx.meta_bindings[t.id] = pr
        return pr
    return t


def _merge_meta_record_fields(ctx: _TypeCtx, src: int, dst: int, span) -> None:
    a = ctx.meta_record_fields.get(src)
    if not a:
        return
    b = ctx.meta_record_fields.setdefault(dst, {})
    for k, v in a.items():
        if k in b:
            _unify(ctx, b[k], v, span)
        else:
            b[k] = v
    if src in ctx.meta_record_fields:
        del ctx.meta_record_fields[src]


def _apply_meta_record_constraints(ctx: _TypeCtx, mid: int, t: T, span) -> None:
    fields = ctx.meta_record_fields.get(mid)
    if not fields:
        return
    t = _prune(ctx, t)
    if isinstance(t, _TMeta):
        _merge_meta_record_fields(ctx, mid, t.id, span)
        return
    if isinstance(t, tuple) and t and t[0] in ("con", "app"):
        tid = t[1]
        decl0 = ctx.record_fields.get(tid)
        if decl0 is None:
            raise TypeError("type mismatch", span)

        decl = decl0
        if t[0] == "app":
            sym = ctx.sym_by_id.get(tid)
            tps = (sym.data or {}).get("type_param_ids") if sym is not None else None
            subst: dict[int, T] = {}
            if isinstance(tps, list) and all(isinstance(x, int) for x in tps):
                for pid, arg in zip(tps, t[2], strict=False):
                    subst[int(pid)] = arg

            def sg(x: T) -> T:
                x = _prune(ctx, x)
                if isinstance(x, _TGen):
                    return subst.get(x.id, x)
                if isinstance(x, tuple) and x and x[0] == "app":
                    return ("app", x[1], [sg(a) for a in x[2]])
                if isinstance(x, tuple) and x and x[0] == "tuple":
                    return ("tuple", [sg(a) for a in x[1]])
                return x

            decl = {k: sg(v) for k, v in decl0.items()}

        for k, v in fields.items():
            ft = decl.get(k)
            if ft is None:
                raise TypeError("unknown record field", span)
            _unify(ctx, ft, v, span)
        del ctx.meta_record_fields[mid]
        return
    raise TypeError("type mismatch", span)


def _unify(ctx: _TypeCtx, a: T, b: T, span) -> None:
    a = _prune(ctx, a)
    b = _prune(ctx, b)

    # Normalize through type aliases (e.g. Map[K,V] = List[...]).
    a = _expand_type_alias(ctx, a, span=span)
    b = _expand_type_alias(ctx, b, span=span)
    if a is b:
        return
    if isinstance(a, _TMeta):
        _apply_meta_record_constraints(ctx, a.id, b, span)
        ctx.meta_bindings[a.id] = b
        return
    if isinstance(b, _TMeta):
        _apply_meta_record_constraints(ctx, b.id, a, span)
        ctx.meta_bindings[b.id] = a
        return
    if isinstance(a, _TGen) and isinstance(b, _TGen):
        if a.id != b.id:
            raise TypeError("type mismatch", span)
        return
    if isinstance(a, _TGen) or isinstance(b, _TGen):
        raise TypeError("type mismatch", span)

    if isinstance(a, tuple) and isinstance(b, tuple) and a and b and a[0] == "con" and b[0] == "con":
        if a[1] != b[1]:
            raise TypeError("type mismatch", span)
        return

    if isinstance(a, tuple) and isinstance(b, tuple) and a and b and a[0] == "app" and b[0] == "app":
        if a[1] != b[1] or len(a[2]) != len(b[2]):
            raise TypeError("type mismatch", span)
        for x, y in zip(a[2], b[2], strict=True):
            _unify(ctx, x, y, span)
        return

    if isinstance(a, tuple) and isinstance(b, tuple) and a and b and a[0] == "tuple" and b[0] == "tuple":
        if len(a[1]) != len(b[1]):
            raise TypeError("type mismatch", span)
        for x, y in zip(a[1], b[1], strict=True):
            _unify(ctx, x, y, span)
        return

    raise TypeError("type mismatch", span)
