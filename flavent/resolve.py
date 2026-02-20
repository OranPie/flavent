from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Optional

from . import ast
from .diagnostics import ResolveError
from .lexer import lex
from .parser import parse_program
from .span import Span
from .symbols import Scope, Symbol, SymbolId, SymbolKind


@dataclass(frozen=True, slots=True)
class Resolution:
    program: ast.Program
    symbols: list[Symbol]
    ident_to_symbol: dict[int, SymbolId]
    typename_to_symbol: dict[int, SymbolId]
    handler_to_symbol: dict[int, SymbolId]
    pattern_aliases: dict[str, ast.Pattern]
    mixin_hook_plan: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class _Ctx:
    file: str
    discard_names: set[str]
    symbols: list[Symbol]
    next_id: int
    global_scope: Scope
    sector_scopes: dict[SymbolId, Scope]
    ident_to_symbol: dict[int, SymbolId]
    typename_to_symbol: dict[int, SymbolId]
    handler_to_symbol: dict[int, SymbolId]
    pattern_aliases: dict[str, ast.Pattern]

    def new_symbol(self, kind: SymbolKind, name: str, span: Span, *, owner: SymbolId | None = None, data: dict[str, Any] | None = None) -> SymbolId:
        sym_id = self.next_id
        self.next_id += 1
        self.symbols.append(Symbol(id=sym_id, kind=kind, name=name, span=span, owner=owner, data=data))
        return sym_id


def resolve_program(prog: ast.Program) -> Resolution:
    return resolve_program_with_stdlib(prog, use_stdlib=True)


_STDLIB_PRELUDE: ast.Program | None = None
_STDLIB_MODULES: dict[str, ast.Program] = {}
_DISCARD_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _find_module_path_in_roots(qname: str, roots: list[Path]) -> Path | None:
    parts = qname.split(".")
    for root in roots:
        mod_path = root.joinpath(*parts).with_suffix(".flv")
        if mod_path.exists():
            return mod_path
        pkg_path = root.joinpath(*parts) / "__init__.flv"
        if pkg_path.exists():
            return pkg_path
    return None


def _load_module_any(
    qname: str,
    *,
    fallback_span: Span,
    module_roots: list[Path] | None,
    cache: dict[str, ast.Program],
) -> ast.Program:
    cached = cache.get(qname)
    if cached is not None:
        return cached

    # Project/vendor modules (if enabled)
    if module_roots:
        mod_path = _find_module_path_in_roots(qname, module_roots)
        if mod_path is not None:
            try:
                src = mod_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                raise ResolveError(f"Missing module: {qname}", fallback_span)
            prog = parse_program(lex(str(mod_path), src))
            cache[qname] = prog
            return prog

    # Stdlib fallback
    prog = _load_stdlib_module(qname, fallback_span=fallback_span)
    cache[qname] = prog
    return prog


def _mixin_key(name: ast.QualifiedName, version: int) -> str:
    return f"{_qname_str(name)}@v{version}"


def _apply_mixins(prog: ast.Program) -> tuple[ast.Program, list[dict[str, Any]]]:
    mixins: dict[str, ast.MixinDecl] = {}
    uses: list[ast.UseMixinStmt] = []
    resolves: list[ast.ResolveMixinStmt] = []
    sectors: dict[str, ast.SectorDecl] = {}
    types: dict[str, ast.TypeDecl] = {}

    for it in prog.items:
        if isinstance(it, ast.MixinDecl):
            key = _mixin_key(it.name, it.version)
            mixins[key] = it
        elif isinstance(it, ast.UseMixinStmt):
            uses.append(it)
        elif isinstance(it, ast.ResolveMixinStmt):
            resolves.append(it)
        elif isinstance(it, ast.SectorDecl):
            sectors[it.name.name] = it
        elif isinstance(it, ast.TypeDecl):
            types[_qname_str(it.name)] = it

    if not uses:
        return prog, []

    hook_plan_entries: list[dict[str, Any]] = []

    # Build preference graph from resolve mixin-conflict rules.
    prefer_over: dict[str, set[str]] = {}
    for rm in resolves:
        for r in rm.rules:
            a = _mixin_key(r.prefer.name, r.prefer.version)
            b = _mixin_key(r.over.name, r.over.version)
            if a == b:
                raise ResolveError(f"Invalid mixin-conflict rule: prefer and over are the same mixin ({a})", r.span)
            prefer_over.setdefault(a, set()).add(b)

    def is_preferred(a: str, b: str) -> bool:
        seen: set[str] = set()
        stack = [a]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            for nxt in prefer_over.get(cur, set()):
                if nxt == b:
                    return True
                stack.append(nxt)
        return False

    def choose_preferred(cands: list[tuple[str, object]], *, span: Span) -> tuple[str, object]:
        # Pick the unique candidate that is preferred over all others.
        # If none, require explicit resolve rules.
        for k, v in cands:
            if all((k2 == k) or is_preferred(k, k2) for k2, _ in cands):
                return k, v
        names = ", ".join(k for k, _ in cands)
        raise ResolveError(f"Ambiguous mixin conflict: {names}. Add resolve mixin-conflict prefer/over rules.", span)

    def topo_sort(keys: list[str], *, span: Span) -> list[str]:
        # Stable topo sort: if no ordering, preserve input order.
        keys_set = set(keys)
        edges = {k: {x for x in prefer_over.get(k, set()) if x in keys_set} for k in keys}
        indeg: dict[str, int] = {k: 0 for k in keys}
        for k in keys:
            for v in edges.get(k, set()):
                indeg[v] += 1
        queue = [k for k in keys if indeg[k] == 0]
        out: list[str] = []
        while queue:
            k = queue.pop(0)
            out.append(k)
            for v in sorted(edges.get(k, set())):
                indeg[v] -= 1
                if indeg[v] == 0:
                    queue.append(v)
        if len(out) != len(keys):
            raise ResolveError("Cyclic mixin preference rules", span)
        return out

    # Determine used mixins in declared order.
    used_keys: list[str] = []
    for u in uses:
        key = _mixin_key(u.name, u.version)
        if key not in mixins:
            raise ResolveError(f"Unknown mixin: {key}", u.span)
        used_keys.append(key)

    # apply_order: preferred comes earlier. For weaving, we apply least-preferred first,
    # so preferred becomes outermost (last applied).
    apply_order = topo_sort(used_keys, span=uses[0].span)
    weave_order = list(reversed(apply_order))

    # Create mutable sector copies.
    new_sectors: dict[str, ast.SectorDecl] = {k: v for k, v in sectors.items()}

    def _clone_ident(x: ast.Ident) -> ast.Ident:
        return ast.Ident(name=x.name, span=x.span)

    def _clone_qname(qn: ast.QualifiedName) -> ast.QualifiedName:
        return ast.QualifiedName(parts=[_clone_ident(p) for p in qn.parts], span=qn.span)

    def _type_ref_eq(a: ast.TypeRef | None, b: ast.TypeRef | None) -> bool:
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if isinstance(a, ast.TypeParen):
            return _type_ref_eq(a.inner, b)
        if isinstance(b, ast.TypeParen):
            return _type_ref_eq(a, b.inner)
        if isinstance(a, ast.TypeName) and isinstance(b, ast.TypeName):
            if _qname_str(a.name) != _qname_str(b.name):
                return False
            if a.args is None and b.args is None:
                return True
            if a.args is None or b.args is None:
                return False
            if len(a.args) != len(b.args):
                return False
            return all(_type_ref_eq(x, y) for x, y in zip(a.args, b.args, strict=True))
        return False

    def _type_ref_strip_paren(t: ast.TypeRef | None) -> ast.TypeRef | None:
        cur = t
        while isinstance(cur, ast.TypeParen):
            cur = cur.inner
        return cur

    def _option_inner_type(t: ast.TypeRef | None) -> ast.TypeRef | None:
        core = _type_ref_strip_paren(t)
        if not isinstance(core, ast.TypeName):
            return None
        qn = _qname_str(core.name)
        if qn != "Option" and not qn.endswith(".Option"):
            return None
        if core.args is None or len(core.args) != 1:
            return None
        return core.args[0]

    def _rewrite_proceed(expr: ast.Expr, *, callee: ast.Ident) -> ast.Expr:
        if isinstance(expr, ast.ProceedExpr):
            v = ast.VarExpr(name=_clone_ident(callee), span=callee.span)
            return ast.CallExpr(callee=v, args=[ast.CallArgPos(value=_rewrite_proceed(a, callee=callee), span=expr.span) for a in expr.args], span=expr.span)
        if isinstance(expr, ast.CallExpr):
            args: list[ast.CallArg] = []
            for a in expr.args:
                if isinstance(a, ast.CallArgPos):
                    args.append(ast.CallArgPos(value=_rewrite_proceed(a.value, callee=callee), span=a.span))
                elif isinstance(a, ast.CallArgStar):
                    args.append(ast.CallArgStar(value=_rewrite_proceed(a.value, callee=callee), span=a.span))
                elif isinstance(a, ast.CallArgKw):
                    args.append(ast.CallArgKw(name=a.name, value=_rewrite_proceed(a.value, callee=callee), span=a.span))
                elif isinstance(a, ast.CallArgStarStar):
                    args.append(ast.CallArgStarStar(value=_rewrite_proceed(a.value, callee=callee), span=a.span))
                else:
                    args.append(ast.CallArgPos(value=_rewrite_proceed(a, callee=callee), span=expr.span))
            return ast.CallExpr(callee=_rewrite_proceed(expr.callee, callee=callee), args=args, span=expr.span)
        if isinstance(expr, ast.MemberExpr):
            return ast.MemberExpr(object=_rewrite_proceed(expr.object, callee=callee), field=expr.field, span=expr.span)
        if isinstance(expr, ast.IndexExpr):
            return ast.IndexExpr(object=_rewrite_proceed(expr.object, callee=callee), index=_rewrite_proceed(expr.index, callee=callee), span=expr.span)
        if isinstance(expr, ast.UnaryExpr):
            return ast.UnaryExpr(op=expr.op, expr=_rewrite_proceed(expr.expr, callee=callee), span=expr.span)
        if isinstance(expr, ast.BinaryExpr):
            return ast.BinaryExpr(op=expr.op, left=_rewrite_proceed(expr.left, callee=callee), right=_rewrite_proceed(expr.right, callee=callee), span=expr.span)
        if isinstance(expr, ast.PipeExpr):
            return ast.PipeExpr(head=_rewrite_proceed(expr.head, callee=callee), stages=[_rewrite_proceed(s, callee=callee) for s in expr.stages], span=expr.span)
        if isinstance(expr, ast.TupleLitExpr):
            return ast.TupleLitExpr(items=[_rewrite_proceed(a, callee=callee) for a in expr.items], span=expr.span)
        if isinstance(expr, ast.RecordLitExpr):
            items = [ast.RecordItem(key=i.key, value=_rewrite_proceed(i.value, callee=callee), span=i.span) for i in expr.items]
            return ast.RecordLitExpr(items=items, span=expr.span)
        if isinstance(expr, ast.MatchExpr):
            arms = [ast.MatchArm(pat=a.pat, body=_rewrite_proceed(a.body, callee=callee), span=a.span) for a in expr.arms]
            return ast.MatchExpr(scrutinee=_rewrite_proceed(expr.scrutinee, callee=callee), arms=arms, span=expr.span)
        if isinstance(expr, ast.TrySuffixExpr):
            return ast.TrySuffixExpr(inner=_rewrite_proceed(expr.inner, callee=callee), span=expr.span)
        if isinstance(expr, ast.AwaitExpr):
            return expr
        if isinstance(expr, ast.RpcExpr):
            return ast.RpcExpr(sector=expr.sector, fnName=expr.fnName, args=[_rewrite_proceed(a, callee=callee) for a in expr.args], span=expr.span)
        if isinstance(expr, ast.CallSectorExpr):
            return ast.CallSectorExpr(sector=expr.sector, fnName=expr.fnName, args=[_rewrite_proceed(a, callee=callee) for a in expr.args], span=expr.span)
        return expr

    def _rewrite_proceed_in_stmt(st: ast.Stmt, *, callee: ast.Ident) -> ast.Stmt:
        if isinstance(st, ast.LetStmt):
            return ast.LetStmt(name=st.name, value=_rewrite_proceed(st.value, callee=callee), span=st.span)
        if isinstance(st, ast.AssignStmt):
            return ast.AssignStmt(target=st.target, op=st.op, value=_rewrite_proceed(st.value, callee=callee), span=st.span)
        if isinstance(st, ast.ReturnStmt):
            return ast.ReturnStmt(expr=_rewrite_proceed(st.expr, callee=callee), span=st.span)
        if isinstance(st, ast.EmitStmt):
            return ast.EmitStmt(expr=_rewrite_proceed(st.expr, callee=callee), span=st.span)
        if isinstance(st, ast.ExprStmt):
            return ast.ExprStmt(expr=_rewrite_proceed(st.expr, callee=callee), span=st.span)
        if isinstance(st, ast.IfStmt):
            tb = _rewrite_proceed_in_block(st.thenBlock, callee=callee)
            eb = _rewrite_proceed_in_block(st.elseBlock, callee=callee) if st.elseBlock is not None else None
            return ast.IfStmt(cond=_rewrite_proceed(st.cond, callee=callee), thenBlock=tb, elseBlock=eb, span=st.span)
        if isinstance(st, ast.ForStmt):
            return ast.ForStmt(binder=st.binder, iterable=_rewrite_proceed(st.iterable, callee=callee), body=_rewrite_proceed_in_block(st.body, callee=callee), span=st.span)
        return st

    def _rewrite_proceed_in_block(b: ast.Block | None, *, callee: ast.Ident) -> ast.Block | None:
        if b is None:
            return None
        return ast.Block(stmts=[_rewrite_proceed_in_stmt(s, callee=callee) for s in b.stmts], span=b.span)

    def _rewrite_proceed_in_body(body: ast.FnBody, *, callee: ast.Ident) -> ast.FnBody:
        if isinstance(body, ast.BodyExpr):
            return ast.BodyExpr(expr=_rewrite_proceed(body.expr, callee=callee), span=body.span)
        if isinstance(body, ast.BodyDo):
            blk = _rewrite_proceed_in_block(body.block, callee=callee)
            assert blk is not None
            return ast.BodyDo(block=blk, span=body.span)
        return body

    def _contains_proceed_expr(e: ast.Expr) -> bool:
        if isinstance(e, ast.ProceedExpr):
            return True
        if isinstance(e, ast.CallExpr):
            return _contains_proceed_expr(e.callee) or any(_contains_proceed_expr(a) for a in e.args)
        if isinstance(e, ast.MemberExpr):
            return _contains_proceed_expr(e.object)
        if isinstance(e, ast.IndexExpr):
            return _contains_proceed_expr(e.object) or _contains_proceed_expr(e.index)
        if isinstance(e, ast.UnaryExpr):
            return _contains_proceed_expr(e.expr)
        if isinstance(e, ast.BinaryExpr):
            return _contains_proceed_expr(e.left) or _contains_proceed_expr(e.right)
        if isinstance(e, ast.PipeExpr):
            return _contains_proceed_expr(e.head) or any(_contains_proceed_expr(s) for s in e.stages)
        if isinstance(e, ast.TupleLitExpr):
            return any(_contains_proceed_expr(x) for x in e.items)
        if isinstance(e, ast.RecordLitExpr):
            return any(_contains_proceed_expr(x.value) for x in e.items)
        if isinstance(e, ast.MatchExpr):
            return _contains_proceed_expr(e.scrutinee) or any(_contains_proceed_expr(a.body) for a in e.arms)
        if isinstance(e, ast.TrySuffixExpr):
            return _contains_proceed_expr(e.inner)
        if isinstance(e, ast.RpcExpr):
            return any(_contains_proceed_expr(a) for a in e.args)
        if isinstance(e, ast.CallSectorExpr):
            return any(_contains_proceed_expr(a) for a in e.args)
        return False

    def _contains_proceed_stmt(st: ast.Stmt) -> bool:
        if isinstance(st, ast.LetStmt):
            return _contains_proceed_expr(st.value)
        if isinstance(st, ast.AssignStmt):
            return _contains_proceed_expr(st.value)
        if isinstance(st, ast.ReturnStmt):
            return _contains_proceed_expr(st.expr)
        if isinstance(st, ast.EmitStmt):
            return _contains_proceed_expr(st.expr)
        if isinstance(st, ast.ExprStmt):
            return _contains_proceed_expr(st.expr)
        if isinstance(st, ast.IfStmt):
            return _contains_proceed_expr(st.cond) or _contains_proceed_block(st.thenBlock) or (st.elseBlock is not None and _contains_proceed_block(st.elseBlock))
        if isinstance(st, ast.ForStmt):
            return _contains_proceed_expr(st.iterable) or _contains_proceed_block(st.body)
        return False

    def _contains_proceed_block(b: ast.Block) -> bool:
        return any(_contains_proceed_stmt(s) for s in b.stmts)

    def _ensure_no_proceed(body: ast.FnBody, *, span: Span) -> None:
        if isinstance(body, ast.BodyExpr):
            if _contains_proceed_expr(body.expr):
                raise ResolveError("proceed() appears in an unsupported position in mixin weaving", span)
        if isinstance(body, ast.BodyDo):
            if _contains_proceed_block(body.block):
                raise ResolveError("proceed() appears in an unsupported position in mixin weaving", span)

    @dataclass(frozen=True, slots=True)
    class _AroundSpec:
        mixin_key: str
        around: ast.MixinAround
        point: str
        origin: str
        conflict_policy: str
        strict_mode: bool
        hook_id: str
        priority: int
        depends: list[str]
        at: str | None
        span: Span

    def _mk_qname(name: str, span: Span) -> ast.QualifiedName:
        return ast.QualifiedName(parts=[ast.Ident(name=name, span=span)], span=span)

    def _mk_var(name: str, span: Span) -> ast.VarExpr:
        return ast.VarExpr(name=ast.Ident(name=name, span=span), span=span)

    def _mk_call(name: str, args: list[ast.Expr], span: Span) -> ast.CallExpr:
        return ast.CallExpr(
            callee=_mk_var(name, span),
            args=[ast.CallArgPos(value=a, span=span) for a in args],
            span=span,
        )

    def _mk_proceed(args: list[ast.Expr], span: Span) -> ast.ProceedExpr:
        return ast.ProceedExpr(args=args, span=span)

    def _body_to_block(body: ast.FnBody, *, span: Span) -> ast.Block:
        if isinstance(body, ast.BodyDo):
            return body.block
        if isinstance(body, ast.BodyExpr):
            return ast.Block(stmts=[ast.ReturnStmt(expr=body.expr, span=body.span)], span=body.span)
        return ast.Block(stmts=[ast.ReturnStmt(expr=ast.LitExpr(lit=ast.Literal(kind="LitInt", value="0", span=span), span=span), span=span)], span=span)

    def _parse_int(s: str | None, *, default: int, span: Span, key: str) -> int:
        if s is None or s == "":
            return default
        try:
            return int(s)
        except ValueError as exc:
            raise ResolveError(f"Invalid hook option `{key}` int value: {s!r}", span) from exc

    def _parse_bool(s: str | None, *, default: bool, span: Span, key: str) -> bool:
        if s is None or s == "":
            return default
        if s == "true":
            return True
        if s == "false":
            return False
        raise ResolveError(f"Invalid hook option `{key}` bool value: {s!r}", span)

    def _split_csv(s: str | None) -> list[str]:
        if s is None:
            return []
        parts = [p.strip() for p in s.split(",")]
        return [p for p in parts if p]

    def _safe_name(s: str) -> str:
        out = []
        for ch in s:
            if ch.isalnum() or ch == "_":
                out.append(ch)
            else:
                out.append("_")
        return "".join(out)

    def _validate_locator(
        locator: str | None,
        *,
        target: ast.FnDecl,
        sec_name: str,
        hook_id: str,
        span: Span,
        anchor_aliases: set[str] | None = None,
    ) -> None:
        if locator is None or locator == "":
            return
        text = locator
        line_part: int | None = None
        anchor_part: str | None = None
        if text.startswith("line:"):
            rest = text[len("line:") :]
            if "#" in rest:
                a, b = rest.split("#", 1)
                rest = a
                anchor_part = b
            try:
                line_part = int(rest)
            except ValueError as exc:
                raise ResolveError(f"Invalid hook locator line in `at`: {locator!r}", span) from exc
        elif text.startswith("anchor:"):
            anchor_part = text[len("anchor:") :]
        elif text.startswith("name:"):
            anchor_part = text[len("name:") :]
        else:
            anchor_part = text

        if line_part is not None and target.span.line != line_part:
            raise ResolveError(
                f"Hook locator mismatch for {hook_id}: expected line {line_part}, got {target.span.line} on {sec_name}.{target.name.name}",
                span,
            )
        valid_anchors = {target.name.name}
        if anchor_aliases:
            valid_anchors.update(anchor_aliases)
        if anchor_part is not None and anchor_part != "" and anchor_part not in valid_anchors:
            raise ResolveError(
                f"Hook locator mismatch for {hook_id}: expected anchor {anchor_part!r}, got {target.name.name!r}",
                span,
            )

    def _resolve_specs(specs: list[_AroundSpec], *, span: Span) -> tuple[list[_AroundSpec], list[tuple[_AroundSpec, str]]]:
        if not specs:
            return [], []
        groups: dict[str, list[_AroundSpec]] = {}
        order_ids: list[str] = []
        spec_order_idx: dict[int, int] = {}
        for i, sp in enumerate(specs):
            spec_order_idx[id(sp)] = i
            if sp.hook_id not in groups:
                groups[sp.hook_id] = []
                order_ids.append(sp.hook_id)
            groups[sp.hook_id].append(sp)

        selected: list[_AroundSpec] = []
        dropped: list[tuple[_AroundSpec, str]] = []
        for hook_id in order_ids:
            group = groups[hook_id]
            if len(group) == 1:
                selected.append(group[0])
                continue
            if any(sp.conflict_policy == "error" for sp in group):
                raise ResolveError(f"Duplicate hook id in same target: {hook_id}", group[0].span)
            prefer_specs = [sp for sp in group if sp.conflict_policy == "prefer"]
            if prefer_specs:
                chosen = sorted(prefer_specs, key=lambda sp: (-sp.priority, spec_order_idx[id(sp)]))[0]
                selected.append(chosen)
                continue
            # All `drop`: remove all candidates for this hook id.
            for sp in group:
                dropped.append((sp, "duplicate_drop"))
            continue

        if not selected:
            return [], dropped

        while True:
            by_id: dict[str, _AroundSpec] = {sp.hook_id: sp for sp in selected}
            kept: list[_AroundSpec] = []
            removed = False
            for sp in selected:
                missing = [dep for dep in sp.depends if dep not in by_id]
                if not missing:
                    kept.append(sp)
                    continue
                if sp.strict_mode:
                    raise ResolveError(f"Unknown hook dependency: {missing[0]} (needed by {sp.hook_id})", sp.span)
                dropped.append((sp, f"unknown_dependency:{missing[0]}"))
                removed = True
            if not removed:
                break
            selected = kept
            if not selected:
                return [], dropped

        by_id = {sp.hook_id: sp for sp in selected}

        edges: dict[str, set[str]] = {sp.hook_id: set() for sp in selected}
        indeg: dict[str, int] = {sp.hook_id: 0 for sp in selected}
        order_idx: dict[str, int] = {sp.hook_id: i for i, sp in enumerate(selected)}

        for sp in selected:
            for dep in sp.depends:
                if sp.hook_id not in edges[dep]:
                    edges[dep].add(sp.hook_id)
                    indeg[sp.hook_id] += 1

        ready: list[str] = [hid for hid, d in indeg.items() if d == 0]
        out: list[_AroundSpec] = []
        while ready:
            ready.sort(key=lambda hid: (-by_id[hid].priority, order_idx[hid], hid))
            hid = ready.pop(0)
            out.append(by_id[hid])
            for nxt in sorted(edges[hid]):
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    ready.append(nxt)

        if len(out) != len(selected):
            raise ResolveError("Cyclic hook dependencies in mixin call stack resolver", span)
        return out, dropped

    def _clone_params(ps: list[ast.ParamDecl]) -> list[ast.ParamDecl]:
        out: list[ast.ParamDecl] = []
        for p in ps:
            out.append(
                ast.ParamDecl(
                    name=ast.Ident(name=p.name.name, span=p.name.span),
                    ty=p.ty,
                    kind=p.kind,
                    span=p.span,
                )
            )
        return out

    def _apply_around_specs(
        items: list[Any],
        *,
        around_by_fn: dict[str, list[_AroundSpec]],
        owner_name: str,
        owner_kind: str,
        anchor_alias_by_fn: dict[str, set[str]] | None = None,
        display_target_by_fn: dict[str, str] | None = None,
        hook_plan: list[dict[str, Any]] | None = None,
    ) -> list[Any]:
        def _plan_row(sp: _AroundSpec, *, target_name: str, depth: int | None, status: str, drop_reason: str = "") -> dict[str, Any]:
            row = {
                "owner_kind": owner_kind,
                "owner": owner_name,
                "target": f"{owner_name}.{target_name}",
                "hook_id": sp.hook_id,
                "point": sp.point,
                "origin": sp.origin,
                "conflict_policy": sp.conflict_policy,
                "mixin_key": sp.mixin_key,
                "priority": sp.priority,
                "depends": list(sp.depends),
                "at": sp.at,
                "depth": depth,
                "status": status,
            }
            if drop_reason:
                row["drop_reason"] = drop_reason
            return row

        def _append_plan(sp: _AroundSpec, *, target_name: str, depth: int | None, status: str, drop_reason: str = "") -> None:
            if hook_plan is None:
                return
            hook_plan.append(_plan_row(sp, target_name=target_name, depth=depth, status=status, drop_reason=drop_reason))

        owner_safe = _safe_name(owner_name)
        around_ordered: list[_AroundSpec] = []
        depth_by_spec: dict[int, int] = {}
        target_by_spec: dict[int, str] = {}
        active_row_by_spec: dict[int, dict[str, Any]] = {}
        active_rows: list[dict[str, Any]] = []
        for fname, specs in around_by_fn.items():
            head_specs = [sp for sp in specs if sp.point == "head"]
            invoke_specs = [sp for sp in specs if sp.point == "invoke"]
            tail_specs = [sp for sp in specs if sp.point == "tail"]
            ordered_head, dropped_head = _resolve_specs(head_specs, span=specs[0].span)
            ordered_invoke, dropped_invoke = _resolve_specs(invoke_specs, span=specs[0].span)
            ordered_tail, dropped_tail = _resolve_specs(tail_specs, span=specs[0].span)
            display_target = (display_target_by_fn or {}).get(fname, fname)
            for sp, reason in [*dropped_head, *dropped_invoke, *dropped_tail]:
                _append_plan(sp, target_name=display_target, depth=None, status="dropped", drop_reason=reason)
            # Outer stack order: heads then invokes then tails; tail executes after proceed so reverse it.
            outer_stack = [*ordered_head, *ordered_invoke, *reversed(ordered_tail)]
            for depth, sp in enumerate(outer_stack):
                depth_by_spec[id(sp)] = depth
                target_by_spec[id(sp)] = display_target
                row = _plan_row(sp, target_name=display_target, depth=depth, status="active")
                active_row_by_spec[id(sp)] = row
                active_rows.append(row)
            around_ordered.extend(reversed(outer_stack))

        for weave_idx, spec in enumerate(around_ordered, start=1):
            key = spec.mixin_key
            ar = spec.around
            fname = ar.sig.name.name
            target_name = target_by_spec.get(id(spec), fname)
            depth = depth_by_spec.get(id(spec))
            target = next((it for it in items if isinstance(it, ast.FnDecl) and it.name.name == fname), None)
            if target is None:
                raise ResolveError(f"Mixin {key} around-target fn not found: {owner_name}.{fname}", ar.span)
            try:
                _validate_locator(
                    spec.at,
                    target=target,
                    sec_name=owner_name,
                    hook_id=spec.hook_id,
                    span=spec.span,
                    anchor_aliases=(anchor_alias_by_fn or {}).get(fname),
                )
            except ResolveError as exc:
                if (not spec.strict_mode) and exc.message.startswith("Hook locator mismatch"):
                    if hook_plan is not None:
                        row = active_row_by_spec.pop(id(spec), None)
                        if row in active_rows:
                            active_rows.remove(row)
                    _append_plan(spec, target_name=target_name, depth=depth, status="dropped", drop_reason="locator_mismatch")
                    continue
                raise

            if len(ar.sig.params) != len(target.params):
                raise ResolveError(f"Mixin {key} around signature arity mismatch for {owner_name}.{fname}", ar.span)
            for ap, tp in zip(ar.sig.params, target.params, strict=True):
                if not _type_ref_eq(ap.ty, tp.ty):
                    raise ResolveError(f"Mixin {key} around signature param type mismatch for {owner_name}.{fname}", ap.span)
            if ar.sig.retType is not None and not _type_ref_eq(ar.sig.retType, target.retType):
                raise ResolveError(f"Mixin {key} around signature return type mismatch for {owner_name}.{fname}", ar.sig.span)

            orig_name = ast.Ident(name=f"__mixin_{key.replace('.', '_').replace('@', '_')}_{owner_safe}_{fname}_{weave_idx}_orig", span=target.name.span)
            orig = ast.FnDecl(
                name=orig_name,
                sectorQual=None,
                typeParams=target.typeParams,
                params=_clone_params(target.params),
                retType=target.retType,
                body=target.body,
                span=target.span,
            )
            items.append(orig)

            new_body = _rewrite_proceed_in_body(ast.BodyDo(block=ar.block, span=ar.block.span), callee=orig_name)
            _ensure_no_proceed(new_body, span=ar.span)
            new_target = ast.FnDecl(
                name=target.name,
                sectorQual=target.sectorQual,
                typeParams=target.typeParams,
                params=_clone_params(target.params),
                retType=target.retType,
                body=new_body,
                span=target.span,
            )
            items = [new_target if (isinstance(it, ast.FnDecl) and it.name.name == fname) else it for it in items]
        if hook_plan is not None:
            hook_plan.extend(active_rows)
        return items

    def apply_to_sector(sd: ast.SectorDecl, mixin_keys: list[str]) -> ast.SectorDecl:
        items = list(sd.items)
        existing_fn_by_name: dict[str, ast.FnDecl] = {it.name.name: it for it in items if isinstance(it, ast.FnDecl)}

        # Collect add candidates across all mixins.
        add_cands: dict[str, list[tuple[str, ast.MixinFnAdd]]] = {}
        raw_arounds: list[tuple[str, ast.MixinAround]] = []
        raw_hooks: list[tuple[str, ast.MixinHook]] = []
        for key in mixin_keys:
            md = mixins[key]
            for mi in md.items:
                if isinstance(mi, ast.MixinFnAdd):
                    add_cands.setdefault(mi.sig.name.name, []).append((key, mi))
                elif isinstance(mi, ast.MixinAround):
                    raw_arounds.append((key, mi))
                elif isinstance(mi, ast.MixinHook):
                    raw_hooks.append((key, mi))

        # Resolve adds.
        for fname, cands in add_cands.items():
            if fname in existing_fn_by_name:
                keys = ", ".join(k for k, _ in cands)
                raise ResolveError(f"Mixin adds conflict with existing fn {sd.name.name}.{fname}: {keys}", cands[0][1].span)
            if len(cands) == 1:
                chosen = cands[0]
            else:
                chosen = choose_preferred(cands, span=cands[0][1].span)
            key, add = chosen
            fd = ast.FnDecl(
                name=add.sig.name,
                sectorQual=None,
                typeParams=None,
                params=add.sig.params,
                retType=add.sig.retType,
                body=add.body,
                span=add.span,
            )
            items.append(fd)
            existing_fn_by_name[fname] = fd

        # Build around/hook specs by function target.
        around_by_fn: dict[str, list[_AroundSpec]] = {}
        hook_counter = 0

        for key, ar in raw_arounds:
            hook_counter += 1
            hook_id = f"{_safe_name(key)}__invoke__{ar.sig.name.name}__{hook_counter}"
            around_by_fn.setdefault(ar.sig.name.name, []).append(
                _AroundSpec(
                    mixin_key=key,
                    around=ar,
                    point="invoke",
                    origin="around",
                    conflict_policy="error",
                    strict_mode=True,
                    hook_id=hook_id,
                    priority=0,
                    depends=[],
                    at=None,
                    span=ar.span,
                )
            )

        for key, hk in raw_hooks:
            fname = hk.sig.name.name
            target = existing_fn_by_name.get(fname)
            if target is None:
                raise ResolveError(f"Mixin {key} hook target fn not found: {sd.name.name}.{fname}", hk.span)

            if len(hk.sig.params) < len(target.params):
                raise ResolveError(f"Mixin {key} hook signature arity mismatch for {sd.name.name}.{fname}", hk.span)
            for ap, tp in zip(hk.sig.params, target.params, strict=False):
                if not _type_ref_eq(ap.ty, tp.ty):
                    raise ResolveError(f"Mixin {key} hook signature param type mismatch for {sd.name.name}.{fname}", ap.span)

            opts = hk.opts
            allowed_opts = {"id", "priority", "depends", "at", "cancelable", "returnDep", "const", "constParams", "constArgs", "conflict", "strict"}
            unknown_opts = sorted(k for k in opts if k not in allowed_opts)
            if unknown_opts:
                raise ResolveError(f"Unknown hook option: {unknown_opts[0]}", hk.span)
            if hk.point != "head" and "cancelable" in opts:
                raise ResolveError(f"hook {hk.point} does not support cancelable", hk.span)
            if hk.point != "tail" and "returnDep" in opts:
                raise ResolveError(f"hook {hk.point} does not support returnDep", hk.span)
            if hk.point == "invoke" and ("const" in opts or "constParams" in opts or "constArgs" in opts):
                raise ResolveError("hook invoke does not support const parameters", hk.span)

            priority = _parse_int(opts.get("priority"), default=0, span=hk.span, key="priority")
            hook_id = opts.get("id") or f"{_safe_name(key)}__{hk.point}__{fname}__{hook_counter}"
            hook_counter += 1
            depends = _split_csv(opts.get("depends"))
            at = opts.get("at")
            cancelable = _parse_bool(opts.get("cancelable"), default=False, span=hk.span, key="cancelable")
            return_dep = opts.get("returnDep", "none")
            if return_dep not in ("none", "use_return", "replace_return"):
                raise ResolveError("hook returnDep must be one of: none, use_return, replace_return", hk.span)
            conflict_policy = opts.get("conflict", "error")
            if conflict_policy not in ("error", "prefer", "drop"):
                raise ResolveError("hook conflict must be one of: error, prefer, drop", hk.span)
            strict_mode = _parse_bool(opts.get("strict"), default=True, span=hk.span, key="strict")
            const_values = _split_csv(opts.get("const")) + _split_csv(opts.get("constParams")) + _split_csv(opts.get("constArgs"))

            if hk.point == "invoke":
                if const_values:
                    raise ResolveError("hook invoke does not support const parameters", hk.span)
                if len(hk.sig.params) != len(target.params):
                    raise ResolveError(f"Mixin {key} hook invoke arity mismatch for {sd.name.name}.{fname}", hk.span)
                if hk.sig.retType is not None and not _type_ref_eq(hk.sig.retType, target.retType):
                    raise ResolveError(f"Mixin {key} hook invoke return type mismatch for {sd.name.name}.{fname}", hk.sig.span)
                around = ast.MixinAround(sig=hk.sig, block=_body_to_block(hk.body, span=hk.span), span=hk.span)
                around_by_fn.setdefault(fname, []).append(
                    _AroundSpec(
                        mixin_key=key,
                        around=around,
                        point="invoke",
                        origin="hook",
                        conflict_policy=conflict_policy,
                        strict_mode=strict_mode,
                        hook_id=hook_id,
                        priority=priority,
                        depends=depends,
                        at=at,
                        span=hk.span,
                    )
                )
                continue

            if hk.point not in ("head", "tail"):
                raise ResolveError(f"Unsupported hook point: {hk.point}", hk.span)

            extra_ret = 1 if hk.point == "tail" and return_dep in ("use_return", "replace_return") else 0
            expected_n = len(target.params) + extra_ret + len(const_values)
            if len(hk.sig.params) != expected_n:
                raise ResolveError(
                    f"Mixin {key} hook {hk.point} signature arity mismatch for {sd.name.name}.{fname}: expected {expected_n}",
                    hk.span,
                )
            if hk.point == "head" and return_dep != "none":
                raise ResolveError("hook head does not support returnDep", hk.span)
            if hk.point == "tail" and cancelable:
                raise ResolveError("hook tail does not support cancelable", hk.span)
            if hk.point == "head" and cancelable:
                inner = _option_inner_type(hk.sig.retType)
                if inner is None:
                    raise ResolveError("hook head cancelable=true requires return type Option[T]", hk.sig.span)
                if target.retType is not None and not _type_ref_eq(inner, target.retType):
                    raise ResolveError("hook head cancelable=true Option[T] must match target return type", hk.sig.span)
            if hk.point == "tail" and return_dep in ("use_return", "replace_return"):
                prev_ret_param = hk.sig.params[len(target.params)]
                if target.retType is not None and not _type_ref_eq(prev_ret_param.ty, target.retType):
                    raise ResolveError("hook tail returnDep requires extra return parameter type matching target return type", prev_ret_param.span)
                if return_dep == "replace_return" and hk.sig.retType is not None and target.retType is not None and not _type_ref_eq(hk.sig.retType, target.retType):
                    raise ResolveError("hook tail returnDep=replace_return requires hook return type matching target return type", hk.sig.span)

            helper_name = f"__hook_{_safe_name(key)}_{_safe_name(sd.name.name)}_{_safe_name(fname)}_{hook_counter}_impl"
            helper_ident = ast.Ident(name=helper_name, span=hk.sig.name.span)
            helper_fn = ast.FnDecl(
                name=helper_ident,
                sectorQual=None,
                typeParams=None,
                params=hk.sig.params,
                retType=hk.sig.retType,
                body=hk.body,
                span=hk.span,
            )
            items.append(helper_fn)
            existing_fn_by_name[helper_name] = helper_fn

            arg_exprs: list[ast.Expr] = [_mk_var(p.name.name, hk.span) for p in target.params]
            proceed_expr = _mk_proceed(arg_exprs, hk.span)
            helper_call_args: list[ast.Expr] = list(arg_exprs)
            if extra_ret:
                helper_call_args.append(_mk_var("__hook_prev", hk.span))
            for raw in const_values:
                helper_call_args.append(ast.LitExpr(lit=ast.Literal(kind="LitStr", value=raw, span=hk.span), span=hk.span))
            helper_call = _mk_call(helper_name, helper_call_args, hk.span)

            wrapper_block: ast.Block
            if hk.point == "head":
                if cancelable:
                    chooser_name = ast.Ident(name="__hook_choice", span=hk.span)
                    ret_match = ast.MatchExpr(
                        scrutinee=_mk_var("__hook_choice", hk.span),
                        arms=[
                            ast.MatchArm(
                                pat=ast.PConstructor(
                                    name=_mk_qname("Some", hk.span),
                                    args=[ast.PVar(name=ast.Ident(name="v", span=hk.span), span=hk.span)],
                                    span=hk.span,
                                ),
                                body=_mk_var("v", hk.span),
                                span=hk.span,
                            ),
                            ast.MatchArm(
                                pat=ast.PConstructor(name=_mk_qname("None", hk.span), args=None, span=hk.span),
                                body=proceed_expr,
                                span=hk.span,
                            ),
                        ],
                        span=hk.span,
                    )
                    wrapper_block = ast.Block(
                        stmts=[
                            ast.LetStmt(name=chooser_name, value=helper_call, span=hk.span),
                            ast.ReturnStmt(expr=ret_match, span=hk.span),
                        ],
                        span=hk.span,
                    )
                else:
                    wrapper_block = ast.Block(
                        stmts=[
                            ast.ExprStmt(expr=helper_call, span=hk.span),
                            ast.ReturnStmt(expr=proceed_expr, span=hk.span),
                        ],
                        span=hk.span,
                    )
            else:
                prev_name = ast.Ident(name="__hook_prev", span=hk.span)
                stmts: list[ast.Stmt] = [ast.LetStmt(name=prev_name, value=proceed_expr, span=hk.span)]
                if return_dep == "replace_return":
                    stmts.append(ast.ReturnStmt(expr=helper_call, span=hk.span))
                elif return_dep == "use_return":
                    stmts.append(ast.ExprStmt(expr=helper_call, span=hk.span))
                    stmts.append(ast.ReturnStmt(expr=_mk_var("__hook_prev", hk.span), span=hk.span))
                else:
                    stmts.append(ast.ExprStmt(expr=helper_call, span=hk.span))
                    stmts.append(ast.ReturnStmt(expr=_mk_var("__hook_prev", hk.span), span=hk.span))
                wrapper_block = ast.Block(stmts=stmts, span=hk.span)

            around_sig = ast.FnSignature(
                name=ast.Ident(name=fname, span=hk.sig.name.span),
                params=target.params,
                retType=target.retType,
                span=hk.sig.span,
            )
            around_by_fn.setdefault(fname, []).append(
                _AroundSpec(
                    mixin_key=key,
                    around=ast.MixinAround(sig=around_sig, block=wrapper_block, span=hk.span),
                    point=hk.point,
                    origin="hook",
                    conflict_policy=conflict_policy,
                    strict_mode=strict_mode,
                    hook_id=hook_id,
                    priority=priority,
                    depends=depends,
                    at=at,
                    span=hk.span,
                )
            )

        items = _apply_around_specs(
            items,
            around_by_fn=around_by_fn,
            owner_name=sd.name.name,
            owner_kind="sector",
            hook_plan=hook_plan_entries,
        )

        return ast.SectorDecl(name=sd.name, supervisor=sd.supervisor, items=items, span=sd.span)

    # Apply per-sector / per-type.
    sector_to_mixins: dict[str, list[str]] = {name: [] for name in new_sectors}
    type_to_mixins: dict[str, list[str]] = {name: [] for name in types}
    for key in weave_order:
        md = mixins[key]
        if isinstance(md.target, ast.MixinTargetSector):
            sec_name = md.target.name.name
            if sec_name not in new_sectors:
                raise ResolveError(f"Mixin {key} targets unknown sector: {sec_name}", md.target.span)
            sector_to_mixins[sec_name].append(key)
        elif isinstance(md.target, ast.MixinTargetType):
            tname = _qname_str(md.target.name)
            if tname not in types:
                raise ResolveError(f"Mixin {key} targets unknown type: {tname}", md.target.span)
            type_to_mixins[tname].append(key)
        else:
            raise ResolveError("Unsupported mixin target", md.target.span)

    for sec_name, keys in sector_to_mixins.items():
        if not keys:
            continue
        new_sectors[sec_name] = apply_to_sector(new_sectors[sec_name], keys)

    # Apply to types.
    method_fns: dict[tuple[str, str], str] = {}
    new_types: dict[str, ast.TypeDecl] = {k: v for k, v in types.items()}
    new_top_fns: list[ast.FnDecl] = []
    new_patterns: list[ast.PatternDecl] = []

    def _synth_method_name(tname: str, mname: str) -> str:
        safe_t = tname.replace(".", "_")
        return f"__method__{safe_t}__{mname}"

    def _rewrite_type_method_calls_in_expr(e: ast.Expr) -> ast.Expr:
        if isinstance(e, ast.CallExpr) and isinstance(e.callee, ast.MemberExpr):
            m = e.callee
            if isinstance(m.object, ast.VarExpr):
                tn = m.object.name.name
                fn = method_fns.get((tn, m.field.name))
                if fn is not None:
                    ident = ast.Ident(name=fn, span=m.field.span)
                    return ast.CallExpr(callee=ast.VarExpr(name=ident, span=ident.span), args=[_rewrite_type_method_calls_in_expr(a) for a in e.args], span=e.span)
        if isinstance(e, ast.CallExpr):
            return ast.CallExpr(callee=_rewrite_type_method_calls_in_expr(e.callee), args=[_rewrite_type_method_calls_in_expr(a) for a in e.args], span=e.span)
        if isinstance(e, ast.MemberExpr):
            return ast.MemberExpr(object=_rewrite_type_method_calls_in_expr(e.object), field=e.field, span=e.span)
        if isinstance(e, ast.IndexExpr):
            return ast.IndexExpr(object=_rewrite_type_method_calls_in_expr(e.object), index=_rewrite_type_method_calls_in_expr(e.index), span=e.span)
        if isinstance(e, ast.UnaryExpr):
            return ast.UnaryExpr(op=e.op, expr=_rewrite_type_method_calls_in_expr(e.expr), span=e.span)
        if isinstance(e, ast.BinaryExpr):
            return ast.BinaryExpr(op=e.op, left=_rewrite_type_method_calls_in_expr(e.left), right=_rewrite_type_method_calls_in_expr(e.right), span=e.span)
        if isinstance(e, ast.PipeExpr):
            return ast.PipeExpr(head=_rewrite_type_method_calls_in_expr(e.head), stages=[_rewrite_type_method_calls_in_expr(s) for s in e.stages], span=e.span)
        if isinstance(e, ast.TupleLitExpr):
            return ast.TupleLitExpr(items=[_rewrite_type_method_calls_in_expr(x) for x in e.items], span=e.span)
        if isinstance(e, ast.RecordLitExpr):
            items = [ast.RecordItem(key=i.key, value=_rewrite_type_method_calls_in_expr(i.value), span=i.span) for i in e.items]
            return ast.RecordLitExpr(items=items, span=e.span)
        if isinstance(e, ast.MatchExpr):
            arms = [ast.MatchArm(pat=a.pat, body=_rewrite_type_method_calls_in_expr(a.body), span=a.span) for a in e.arms]
            return ast.MatchExpr(scrutinee=_rewrite_type_method_calls_in_expr(e.scrutinee), arms=arms, span=e.span)
        if isinstance(e, ast.TrySuffixExpr):
            return ast.TrySuffixExpr(inner=_rewrite_type_method_calls_in_expr(e.inner), span=e.span)
        if isinstance(e, (ast.AwaitExpr, ast.RpcExpr, ast.CallSectorExpr, ast.LitExpr, ast.VarExpr, ast.ProceedExpr)):
            return e
        return e

    def _rewrite_type_method_calls_in_stmt(st: ast.Stmt) -> ast.Stmt:
        if isinstance(st, ast.LetStmt):
            return ast.LetStmt(name=st.name, value=_rewrite_type_method_calls_in_expr(st.value), span=st.span)
        if isinstance(st, ast.AssignStmt):
            return ast.AssignStmt(target=st.target, op=st.op, value=_rewrite_type_method_calls_in_expr(st.value), span=st.span)
        if isinstance(st, ast.ReturnStmt):
            return ast.ReturnStmt(expr=_rewrite_type_method_calls_in_expr(st.expr), span=st.span)
        if isinstance(st, ast.EmitStmt):
            return ast.EmitStmt(expr=_rewrite_type_method_calls_in_expr(st.expr), span=st.span)
        if isinstance(st, ast.ExprStmt):
            return ast.ExprStmt(expr=_rewrite_type_method_calls_in_expr(st.expr), span=st.span)
        if isinstance(st, ast.IfStmt):
            tb = ast.Block(stmts=[_rewrite_type_method_calls_in_stmt(s) for s in st.thenBlock.stmts], span=st.thenBlock.span)
            eb = None
            if st.elseBlock is not None:
                eb = ast.Block(stmts=[_rewrite_type_method_calls_in_stmt(s) for s in st.elseBlock.stmts], span=st.elseBlock.span)
            return ast.IfStmt(cond=_rewrite_type_method_calls_in_expr(st.cond), thenBlock=tb, elseBlock=eb, span=st.span)
        if isinstance(st, ast.ForStmt):
            body = ast.Block(stmts=[_rewrite_type_method_calls_in_stmt(s) for s in st.body.stmts], span=st.body.span)
            return ast.ForStmt(binder=st.binder, iterable=_rewrite_type_method_calls_in_expr(st.iterable), body=body, span=st.span)
        return st

    def _rewrite_type_method_calls_in_body(body: ast.FnBody) -> ast.FnBody:
        if isinstance(body, ast.BodyExpr):
            return ast.BodyExpr(expr=_rewrite_type_method_calls_in_expr(body.expr), span=body.span)
        if isinstance(body, ast.BodyDo):
            blk = ast.Block(stmts=[_rewrite_type_method_calls_in_stmt(s) for s in body.block.stmts], span=body.block.span)
            return ast.BodyDo(block=blk, span=body.span)
        return body

    def apply_to_type(td: ast.TypeDecl, mixin_keys: list[str]) -> ast.TypeDecl:
        # Field injection (record types only)
        if not isinstance(td.rhs, ast.RecordType):
            raise ResolveError(f"Type mixin only supports record types: {_qname_str(td.name)}", td.span)

        type_name = _qname_str(td.name)
        type_method_key = td.name.parts[0].name if len(td.name.parts) == 1 else type_name
        existing_fields = {f.name.name for f in td.rhs.fields}
        field_cands: dict[str, list[tuple[str, ast.MixinFieldAdd]]] = {}
        method_cands: dict[str, list[tuple[str, ast.MixinFnAdd]]] = {}
        pat_cands: dict[str, list[tuple[str, ast.PatternDecl]]] = {}
        raw_arounds: list[tuple[str, ast.MixinAround]] = []
        raw_hooks: list[tuple[str, ast.MixinHook]] = []

        for key in mixin_keys:
            md = mixins[key]
            for mi in md.items:
                if isinstance(mi, ast.MixinFieldAdd):
                    field_cands.setdefault(mi.name.name, []).append((key, mi))
                elif isinstance(mi, ast.MixinFnAdd):
                    method_cands.setdefault(mi.sig.name.name, []).append((key, mi))
                elif isinstance(mi, ast.PatternDecl):
                    pat_cands.setdefault(_qname_str(mi.name), []).append((key, mi))
                elif isinstance(mi, ast.MixinAround):
                    raw_arounds.append((key, mi))
                elif isinstance(mi, ast.MixinHook):
                    raw_hooks.append((key, mi))

        new_fields = list(td.rhs.fields)
        for fname, cands in field_cands.items():
            if fname in existing_fields:
                keys = ", ".join(k for k, _ in cands)
                raise ResolveError(f"Mixin adds field that already exists: {type_name}.{fname} ({keys})", cands[0][1].span)
            chosen = cands[0] if len(cands) == 1 else choose_preferred(cands, span=cands[0][1].span)
            _, add = chosen
            new_fields.append(ast.FieldDecl(name=add.name, ty=add.ty, span=add.span))
            existing_fields.add(fname)

        # Methods: require first param to be `self: <Type>`.
        method_name_to_synth: dict[str, str] = {}
        method_name_by_synth: dict[str, str] = {}
        method_by_public_name: dict[str, ast.FnDecl] = {}
        method_anchor_alias_by_synth: dict[str, set[str]] = {}
        method_items: list[ast.FnDecl] = []
        for mname, cands in method_cands.items():
            chosen = cands[0] if len(cands) == 1 else choose_preferred(cands, span=cands[0][1].span)
            key, add = chosen
            if not add.sig.params:
                raise ResolveError(f"Mixin {key} method must have self param", add.span)
            p0 = add.sig.params[0]
            if p0.name.name != "self":
                raise ResolveError(f"Mixin {key} method first param must be self", p0.span)
            # Require self type matches the target type name.
            if not (isinstance(p0.ty, ast.TypeName) and _qname_str(p0.ty.name) == type_name):
                raise ResolveError(f"Mixin {key} method self type mismatch", p0.span)

            synth = _synth_method_name(type_name, mname)
            method_fns[(type_method_key, mname)] = synth
            method_name_to_synth[mname] = synth
            method_name_by_synth[synth] = mname
            method_anchor_alias_by_synth[synth] = {mname}
            method_item = ast.FnDecl(
                name=ast.Ident(name=synth, span=add.sig.name.span),
                sectorQual=None,
                typeParams=None,
                params=add.sig.params,
                retType=add.sig.retType,
                body=add.body,
                span=add.span,
            )
            method_items.append(method_item)
            method_by_public_name[mname] = method_item

        around_by_fn: dict[str, list[_AroundSpec]] = {}
        hook_counter = 0

        for key, ar in raw_arounds:
            method_name_for_target = ar.sig.name.name
            synth_name = method_name_to_synth.get(method_name_for_target)
            if synth_name is None:
                raise ResolveError(f"Mixin {key} around target method not found: {type_name}.{method_name_for_target}", ar.span)
            hook_counter += 1
            hook_id = f"{_safe_name(key)}__invoke__{method_name_for_target}__{hook_counter}"
            around_sig = ast.FnSignature(
                name=ast.Ident(name=synth_name, span=ar.sig.name.span),
                params=ar.sig.params,
                retType=ar.sig.retType,
                span=ar.sig.span,
            )
            around_by_fn.setdefault(synth_name, []).append(
                _AroundSpec(
                    mixin_key=key,
                    around=ast.MixinAround(sig=around_sig, block=ar.block, span=ar.span),
                    point="invoke",
                    origin="around",
                    conflict_policy="error",
                    strict_mode=True,
                    hook_id=hook_id,
                    priority=0,
                    depends=[],
                    at=None,
                    span=ar.span,
                )
            )

        for key, hk in raw_hooks:
            method_name_for_target = hk.sig.name.name
            synth_name = method_name_to_synth.get(method_name_for_target)
            target = method_by_public_name.get(method_name_for_target)
            if synth_name is None or target is None:
                raise ResolveError(f"Mixin {key} hook target method not found: {type_name}.{method_name_for_target}", hk.span)

            if len(hk.sig.params) < len(target.params):
                raise ResolveError(f"Mixin {key} hook signature arity mismatch for {type_name}.{method_name_for_target}", hk.span)
            for ap, tp in zip(hk.sig.params, target.params, strict=False):
                if not _type_ref_eq(ap.ty, tp.ty):
                    raise ResolveError(f"Mixin {key} hook signature param type mismatch for {type_name}.{method_name_for_target}", ap.span)

            opts = hk.opts
            allowed_opts = {"id", "priority", "depends", "at", "cancelable", "returnDep", "const", "constParams", "constArgs", "conflict", "strict"}
            unknown_opts = sorted(k for k in opts if k not in allowed_opts)
            if unknown_opts:
                raise ResolveError(f"Unknown hook option: {unknown_opts[0]}", hk.span)
            if hk.point != "head" and "cancelable" in opts:
                raise ResolveError(f"hook {hk.point} does not support cancelable", hk.span)
            if hk.point != "tail" and "returnDep" in opts:
                raise ResolveError(f"hook {hk.point} does not support returnDep", hk.span)
            if hk.point == "invoke" and ("const" in opts or "constParams" in opts or "constArgs" in opts):
                raise ResolveError("hook invoke does not support const parameters", hk.span)

            priority = _parse_int(opts.get("priority"), default=0, span=hk.span, key="priority")
            hook_id = opts.get("id") or f"{_safe_name(key)}__{hk.point}__{method_name_for_target}__{hook_counter}"
            hook_counter += 1
            depends = _split_csv(opts.get("depends"))
            at = opts.get("at")
            cancelable = _parse_bool(opts.get("cancelable"), default=False, span=hk.span, key="cancelable")
            return_dep = opts.get("returnDep", "none")
            if return_dep not in ("none", "use_return", "replace_return"):
                raise ResolveError("hook returnDep must be one of: none, use_return, replace_return", hk.span)
            conflict_policy = opts.get("conflict", "error")
            if conflict_policy not in ("error", "prefer", "drop"):
                raise ResolveError("hook conflict must be one of: error, prefer, drop", hk.span)
            strict_mode = _parse_bool(opts.get("strict"), default=True, span=hk.span, key="strict")
            const_values = _split_csv(opts.get("const")) + _split_csv(opts.get("constParams")) + _split_csv(opts.get("constArgs"))

            if hk.point == "invoke":
                if const_values:
                    raise ResolveError("hook invoke does not support const parameters", hk.span)
                if len(hk.sig.params) != len(target.params):
                    raise ResolveError(f"Mixin {key} hook invoke arity mismatch for {type_name}.{method_name_for_target}", hk.span)
                if hk.sig.retType is not None and not _type_ref_eq(hk.sig.retType, target.retType):
                    raise ResolveError(f"Mixin {key} hook invoke return type mismatch for {type_name}.{method_name_for_target}", hk.sig.span)
                around_by_fn.setdefault(synth_name, []).append(
                    _AroundSpec(
                        mixin_key=key,
                        around=ast.MixinAround(
                            sig=ast.FnSignature(
                                name=ast.Ident(name=synth_name, span=hk.sig.name.span),
                                params=target.params,
                                retType=target.retType,
                                span=hk.sig.span,
                            ),
                            block=_body_to_block(hk.body, span=hk.span),
                            span=hk.span,
                        ),
                        point="invoke",
                        origin="hook",
                        conflict_policy=conflict_policy,
                        strict_mode=strict_mode,
                        hook_id=hook_id,
                        priority=priority,
                        depends=depends,
                        at=at,
                        span=hk.span,
                    )
                )
                continue

            if hk.point not in ("head", "tail"):
                raise ResolveError(f"Unsupported hook point: {hk.point}", hk.span)

            extra_ret = 1 if hk.point == "tail" and return_dep in ("use_return", "replace_return") else 0
            expected_n = len(target.params) + extra_ret + len(const_values)
            if len(hk.sig.params) != expected_n:
                raise ResolveError(
                    f"Mixin {key} hook {hk.point} signature arity mismatch for {type_name}.{method_name_for_target}: expected {expected_n}",
                    hk.span,
                )
            if hk.point == "head" and return_dep != "none":
                raise ResolveError("hook head does not support returnDep", hk.span)
            if hk.point == "tail" and cancelable:
                raise ResolveError("hook tail does not support cancelable", hk.span)
            if hk.point == "head" and cancelable:
                inner = _option_inner_type(hk.sig.retType)
                if inner is None:
                    raise ResolveError("hook head cancelable=true requires return type Option[T]", hk.sig.span)
                if target.retType is not None and not _type_ref_eq(inner, target.retType):
                    raise ResolveError("hook head cancelable=true Option[T] must match target return type", hk.sig.span)
            if hk.point == "tail" and return_dep in ("use_return", "replace_return"):
                prev_ret_param = hk.sig.params[len(target.params)]
                if target.retType is not None and not _type_ref_eq(prev_ret_param.ty, target.retType):
                    raise ResolveError("hook tail returnDep requires extra return parameter type matching target return type", prev_ret_param.span)
                if return_dep == "replace_return" and hk.sig.retType is not None and target.retType is not None and not _type_ref_eq(hk.sig.retType, target.retType):
                    raise ResolveError("hook tail returnDep=replace_return requires hook return type matching target return type", hk.sig.span)

            helper_name = f"__hook_{_safe_name(key)}_{_safe_name(type_name)}_{_safe_name(method_name_for_target)}_{hook_counter}_impl"
            helper_ident = ast.Ident(name=helper_name, span=hk.sig.name.span)
            helper_fn = ast.FnDecl(
                name=helper_ident,
                sectorQual=None,
                typeParams=None,
                params=hk.sig.params,
                retType=hk.sig.retType,
                body=hk.body,
                span=hk.span,
            )
            method_items.append(helper_fn)

            arg_exprs: list[ast.Expr] = [_mk_var(p.name.name, hk.span) for p in target.params]
            proceed_expr = _mk_proceed(arg_exprs, hk.span)
            helper_call_args: list[ast.Expr] = list(arg_exprs)
            if extra_ret:
                helper_call_args.append(_mk_var("__hook_prev", hk.span))
            for raw in const_values:
                helper_call_args.append(ast.LitExpr(lit=ast.Literal(kind="LitStr", value=raw, span=hk.span), span=hk.span))
            helper_call = _mk_call(helper_name, helper_call_args, hk.span)

            wrapper_block: ast.Block
            if hk.point == "head":
                if cancelable:
                    chooser_name = ast.Ident(name="__hook_choice", span=hk.span)
                    ret_match = ast.MatchExpr(
                        scrutinee=_mk_var("__hook_choice", hk.span),
                        arms=[
                            ast.MatchArm(
                                pat=ast.PConstructor(
                                    name=_mk_qname("Some", hk.span),
                                    args=[ast.PVar(name=ast.Ident(name="v", span=hk.span), span=hk.span)],
                                    span=hk.span,
                                ),
                                body=_mk_var("v", hk.span),
                                span=hk.span,
                            ),
                            ast.MatchArm(
                                pat=ast.PConstructor(name=_mk_qname("None", hk.span), args=None, span=hk.span),
                                body=proceed_expr,
                                span=hk.span,
                            ),
                        ],
                        span=hk.span,
                    )
                    wrapper_block = ast.Block(
                        stmts=[
                            ast.LetStmt(name=chooser_name, value=helper_call, span=hk.span),
                            ast.ReturnStmt(expr=ret_match, span=hk.span),
                        ],
                        span=hk.span,
                    )
                else:
                    wrapper_block = ast.Block(
                        stmts=[
                            ast.ExprStmt(expr=helper_call, span=hk.span),
                            ast.ReturnStmt(expr=proceed_expr, span=hk.span),
                        ],
                        span=hk.span,
                    )
            else:
                prev_name = ast.Ident(name="__hook_prev", span=hk.span)
                stmts: list[ast.Stmt] = [ast.LetStmt(name=prev_name, value=proceed_expr, span=hk.span)]
                if return_dep == "replace_return":
                    stmts.append(ast.ReturnStmt(expr=helper_call, span=hk.span))
                elif return_dep == "use_return":
                    stmts.append(ast.ExprStmt(expr=helper_call, span=hk.span))
                    stmts.append(ast.ReturnStmt(expr=_mk_var("__hook_prev", hk.span), span=hk.span))
                else:
                    stmts.append(ast.ExprStmt(expr=helper_call, span=hk.span))
                    stmts.append(ast.ReturnStmt(expr=_mk_var("__hook_prev", hk.span), span=hk.span))
                wrapper_block = ast.Block(stmts=stmts, span=hk.span)

            around_by_fn.setdefault(synth_name, []).append(
                _AroundSpec(
                    mixin_key=key,
                    around=ast.MixinAround(
                        sig=ast.FnSignature(
                            name=ast.Ident(name=synth_name, span=hk.sig.name.span),
                            params=target.params,
                            retType=target.retType,
                            span=hk.sig.span,
                        ),
                        block=wrapper_block,
                        span=hk.span,
                    ),
                    point=hk.point,
                    origin="hook",
                    conflict_policy=conflict_policy,
                    strict_mode=strict_mode,
                    hook_id=hook_id,
                    priority=priority,
                    depends=depends,
                    at=at,
                    span=hk.span,
                )
            )

        method_items = _apply_around_specs(
            method_items,
            around_by_fn=around_by_fn,
            owner_name=type_name,
            owner_kind="type",
            anchor_alias_by_fn=method_anchor_alias_by_synth,
            display_target_by_fn=method_name_by_synth,
            hook_plan=hook_plan_entries,
        )
        new_top_fns.extend([it for it in method_items if isinstance(it, ast.FnDecl)])

        for pname, cands in pat_cands.items():
            chosen = cands[0] if len(cands) == 1 else choose_preferred(cands, span=cands[0][1].span)
            _, pd = chosen
            new_patterns.append(pd)

        return ast.TypeDecl(name=td.name, params=td.params, rhs=ast.RecordType(fields=new_fields, span=td.rhs.span), span=td.span)

    for tname, keys in type_to_mixins.items():
        if not keys:
            continue
        new_types[tname] = apply_to_type(new_types[tname], keys)

    # Rebuild items: keep non-mixin declarations, and replace sector decls.
    new_items: list[ast.TopItem] = []
    for it in prog.items:
        if isinstance(it, ast.SectorDecl):
            new_items.append(new_sectors.get(it.name.name, it))
        elif isinstance(it, ast.TypeDecl):
            new_items.append(new_types.get(_qname_str(it.name), it))
        elif isinstance(it, (ast.MixinDecl, ast.UseMixinStmt, ast.ResolveMixinStmt)):
            continue
        else:
            new_items.append(it)

    # Append synthesized method functions and pattern decls.
    new_items.extend(new_patterns)
    new_items.extend(new_top_fns)

    # Finally, rewrite Type.method(...) calls into calls of synthesized method functions.
    rewritten: list[ast.TopItem] = []
    for it in new_items:
        if isinstance(it, ast.FnDecl):
            rewritten.append(ast.FnDecl(name=it.name, sectorQual=it.sectorQual, typeParams=it.typeParams, params=it.params, retType=it.retType, body=_rewrite_type_method_calls_in_body(it.body), span=it.span))
        elif isinstance(it, ast.SectorDecl):
            items2: list[Any] = []
            for si in it.items:
                if isinstance(si, ast.FnDecl):
                    items2.append(ast.FnDecl(name=si.name, sectorQual=si.sectorQual, typeParams=si.typeParams, params=si.params, retType=si.retType, body=_rewrite_type_method_calls_in_body(si.body), span=si.span))
                else:
                    items2.append(si)
            rewritten.append(ast.SectorDecl(name=it.name, supervisor=it.supervisor, items=items2, span=it.span))
        else:
            rewritten.append(it)

    return ast.Program(items=rewritten, run=prog.run, span=prog.span), hook_plan_entries


def _load_stdlib_prelude(*, fallback_span: Span) -> ast.Program:
    global _STDLIB_PRELUDE
    if _STDLIB_PRELUDE is not None:
        return _STDLIB_PRELUDE

    prelude_path = Path(__file__).resolve().parent.parent / "stdlib" / "prelude.flv"
    try:
        src = prelude_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # If stdlib is missing, we fail early with a precise message.
        raise ResolveError("Missing stdlib/prelude.flv", fallback_span)

    _STDLIB_PRELUDE = parse_program(lex(str(prelude_path), src))
    return _STDLIB_PRELUDE


def _load_stdlib_module(qname: str, *, fallback_span: Span) -> ast.Program:
    cached = _STDLIB_MODULES.get(qname)
    if cached is not None:
        return cached

    stdlib_root = Path(__file__).resolve().parent.parent / "stdlib"
    parts = qname.split(".")
    mod_path = stdlib_root.joinpath(*parts).with_suffix(".flv")
    if not mod_path.exists():
        # Package-style module: `use collections` loads `stdlib/collections/__init__.flv`.
        mod_path = stdlib_root.joinpath(*parts) / "__init__.flv"
    try:
        src = mod_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ResolveError(f"Missing stdlib module: {qname}", fallback_span)

    prog = parse_program(lex(str(mod_path), src))
    _STDLIB_MODULES[qname] = prog
    return prog


def _expand_uses(prog: ast.Program, *, module_roots: list[Path] | None) -> ast.Program:
    # DFS expansion with cycle detection and de-dup.
    visited: set[str] = set()
    stack: list[str] = []
    out_items: list[ast.TopItem] = []
    cache: dict[str, ast.Program] = {}

    def qname_str(qn: ast.QualifiedName) -> str:
        return ".".join(p.name for p in qn.parts)

    def visit_module(qname: str, span: Span) -> None:
        if qname in visited:
            return
        if qname in stack:
            cycle = " -> ".join([*stack, qname])
            raise ResolveError(f"Cyclic use: {cycle}", span)
        stack.append(qname)
        mprog = _load_module_any(qname, fallback_span=span, module_roots=module_roots, cache=cache)
        # First expand nested uses.
        for it in mprog.items:
            if isinstance(it, ast.UseStmt):
                visit_module(qname_str(it.name), it.span)
        # Then add the module's non-use items.
        for it in mprog.items:
            if isinstance(it, ast.UseStmt):
                continue
            out_items.append(it)
        stack.pop()
        visited.add(qname)

    # Expand uses at program root.
    for it in prog.items:
        if isinstance(it, ast.UseStmt):
            # `_bridge_python` is an internal capability boundary.
            # User programs must not import it directly.
            if qname_str(it.name) == "_bridge_python":
                file_norm = it.span.file.replace("\\", "/")
                if "/stdlib/" not in file_norm and not file_norm.endswith("/stdlib/_bridge_python.flv"):
                    raise ResolveError("Direct use of _bridge_python is not allowed", it.span)
            visit_module(qname_str(it.name), it.span)

    # Keep original items, minus use declarations.
    kept = [it for it in prog.items if not isinstance(it, ast.UseStmt)]
    if not out_items:
        return prog
    return ast.Program(items=[*out_items, *kept], run=prog.run, span=prog.span)


def _load_discard_names(file: str) -> set[str]:
    # Default discard binding is `_`; users can override via nearest `flvdiscard` file.
    defaults = {"_"}
    path = Path(file)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    cur = path if path.is_dir() else path.parent
    config: Path | None = None
    while True:
        cand = cur / "flvdiscard"
        if cand.exists() and cand.is_file():
            config = cand
            break
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    if config is None:
        return defaults
    try:
        raw = config.read_text(encoding="utf-8")
    except OSError:
        return defaults

    names: list[str] = []
    for line in raw.splitlines():
        clean = line.split("#", 1)[0].strip()
        if not clean:
            continue
        for tok in clean.replace(",", " ").split():
            if _DISCARD_NAME_RE.match(tok):
                names.append(tok)
    if not names:
        return defaults
    return set(names)


def resolve_program_with_stdlib(
    prog: ast.Program,
    *,
    use_stdlib: bool,
    module_roots: list[Path] | None = None,
) -> Resolution:
    if use_stdlib:
        # Prevent stdlib prelude from including itself when users run `flavent check stdlib/prelude.flv`.
        if prog.span.file.replace("\\", "/").endswith("stdlib/prelude.flv"):
            return resolve_program_with_stdlib(prog, use_stdlib=False, module_roots=module_roots)
        prelude = _load_stdlib_prelude(fallback_span=prog.span)
        combined = ast.Program(items=[*prelude.items, *prog.items], run=prog.run, span=prog.span)
        return resolve_program_with_stdlib(combined, use_stdlib=False, module_roots=module_roots)

    # Expand module uses (stdlib only for now).
    prog = _expand_uses(prog, module_roots=module_roots)
    # Apply mixins by rewriting the AST into plain sector/type items.
    prog, mixin_hook_plan = _apply_mixins(prog)

    file = prog.span.file
    ctx = _Ctx(
        file=file,
        discard_names=_load_discard_names(file),
        symbols=[],
        next_id=1,
        global_scope=Scope.root(),
        sector_scopes={},
        ident_to_symbol={},
        typename_to_symbol={},
        handler_to_symbol={},
        pattern_aliases={},
    )

    _install_builtins(ctx)
    _collect_decls(ctx, prog)
    _resolve_uses(ctx, prog)

    return Resolution(
        program=prog,
        symbols=ctx.symbols,
        ident_to_symbol=ctx.ident_to_symbol,
        typename_to_symbol=ctx.typename_to_symbol,
        handler_to_symbol=ctx.handler_to_symbol,
        pattern_aliases=ctx.pattern_aliases,
        mixin_hook_plan=mixin_hook_plan,
    )


def _install_builtins(ctx: _Ctx) -> None:
    # Builtin value constructors.
    for name in ():
        sid = ctx.new_symbol(SymbolKind.CTOR, name, Span(file=ctx.file, start=0, end=0, line=1, col=1))
        ctx.global_scope.define("values", name, sid)

    # Builtin types (MVP set). These are referenced by REF specs and examples.
    for name in (
        "Unit",
        "Int",
        "Float",
        "Bool",
        "Str",
        "Bytes",
    ):
        sid = ctx.new_symbol(SymbolKind.TYPE, name, Span(file=ctx.file, start=0, end=0, line=1, col=1))
        ctx.global_scope.define("types", name, sid)


def _qname_str(qn: ast.QualifiedName) -> str:
    return ".".join(p.name for p in qn.parts)


def _collect_decls(ctx: _Ctx, prog: ast.Program) -> None:
    has_top_on = any(isinstance(it, ast.OnHandler) for it in prog.items)
    main_sector_id: SymbolId | None = None

    for it in prog.items:
        if isinstance(it, ast.SectorDecl) and it.name.name == "main":
            main_sector_id = _define_sector(ctx, it)

    if has_top_on and main_sector_id is None:
        span = prog.span
        main_sector_id = ctx.new_symbol(SymbolKind.SECTOR, "main", span)
        ctx.global_scope.define("sectors", "main", main_sector_id)
        ctx.sector_scopes[main_sector_id] = ctx.global_scope.child()

    for it in prog.items:
        if isinstance(it, ast.TypeDecl):
            _define_type(ctx, it)
        elif isinstance(it, ast.ConstDecl):
            _define_value_decl(ctx, it.name, SymbolKind.CONST)
        elif isinstance(it, ast.LetDecl):
            _define_value_decl(ctx, it.name, SymbolKind.VAR)
        elif isinstance(it, ast.NeedDecl):
            _define_value_decl(ctx, it.name, SymbolKind.NEED)
        elif isinstance(it, ast.FnDecl):
            _define_fn(ctx, it, owner=None)
        elif isinstance(it, ast.PatternDecl):
            # Patterns don't define symbols; they are resolved later.
            continue
        elif isinstance(it, ast.UseStmt):
            # use-items are expanded away before resolution; ignore if present.
            continue
        elif isinstance(it, ast.MixinDecl):
            _define_mixin(ctx, it)
        elif isinstance(it, ast.UseMixinStmt):
            pass
        elif isinstance(it, ast.ResolveMixinStmt):
            pass
        elif isinstance(it, ast.SectorDecl):
            if it.name.name != "main" or main_sector_id is None:
                _define_sector(ctx, it)
        elif isinstance(it, ast.OnHandler):
            if main_sector_id is not None:
                _define_handler(ctx, it, owner=main_sector_id)
        else:
            raise ResolveError("Unsupported top item in Phase 2", it.span)


def _define_type(ctx: _Ctx, td: ast.TypeDecl) -> SymbolId:
    name = _qname_str(td.name)
    existing = ctx.global_scope.lookup("types", name)
    if existing:
        raise ResolveError(f"Duplicate type: {name}", td.span)
    sid = ctx.new_symbol(SymbolKind.TYPE, name, td.span)
    ctx.global_scope.define("types", name, sid)
    ctx.typename_to_symbol[id(td.name)] = sid

    if isinstance(td.rhs, ast.SumType):
        for v in td.rhs.variants:
            ctor_name = v.name.name
            if not ctx.global_scope.lookup("values", ctor_name):
                ctor_id = ctx.new_symbol(SymbolKind.CTOR, ctor_name, v.span, owner=sid)
                ctx.global_scope.define("values", ctor_name, ctor_id)

    return sid


def _define_sector(ctx: _Ctx, sd: ast.SectorDecl) -> SymbolId:
    name = sd.name.name
    existing = ctx.global_scope.lookup("sectors", name)
    if existing:
        raise ResolveError(f"Duplicate sector: {name}", sd.span)
    sid = ctx.new_symbol(SymbolKind.SECTOR, name, sd.span)
    ctx.global_scope.define("sectors", name, sid)
    ctx.ident_to_symbol[id(sd.name)] = sid

    scope = ctx.global_scope.child()
    ctx.sector_scopes[sid] = scope

    for item in sd.items:
        if isinstance(item, ast.LetDecl):
            _define_in_scope(ctx, scope, item.name, SymbolKind.VAR, owner=sid)
        elif isinstance(item, ast.NeedDecl):
            _define_in_scope(ctx, scope, item.name, SymbolKind.NEED, owner=sid)
        elif isinstance(item, ast.FnDecl):
            _define_fn(ctx, item, owner=sid)
        elif isinstance(item, ast.OnHandler):
            _define_handler(ctx, item, owner=sid)
        else:
            raise ResolveError("Unsupported sector item in Phase 2", item.span)

    return sid


def _define_mixin(ctx: _Ctx, md: ast.MixinDecl) -> SymbolId:
    name = _qname_str(md.name)
    key = f"{name}@v{md.version}"
    existing = ctx.global_scope.lookup("mixins", key)
    if existing:
        raise ResolveError(f"Duplicate mixin: {key}", md.span)
    sid = ctx.new_symbol(SymbolKind.MIXIN, key, md.span)
    ctx.global_scope.define("mixins", key, sid)
    return sid


def _define_handler(ctx: _Ctx, h: ast.OnHandler, *, owner: SymbolId) -> SymbolId:
    name = f"handler@{h.span.start}:{h.span.end}"
    sid = ctx.new_symbol(SymbolKind.HANDLER, name, h.span, owner=owner)
    ctx.handler_to_symbol[id(h)] = sid
    return sid


def _define_value_decl(ctx: _Ctx, ident: ast.Ident, kind: SymbolKind) -> SymbolId:
    return _define_in_scope(ctx, ctx.global_scope, ident, kind, owner=None)


def _define_in_scope(ctx: _Ctx, scope: Scope, ident: ast.Ident, kind: SymbolKind, *, owner: SymbolId | None) -> SymbolId:
    name = ident.name
    if kind == SymbolKind.VAR and name in ctx.discard_names:
        sid = ctx.new_symbol(kind, name, ident.span, owner=owner, data={"discard": True})
        ctx.ident_to_symbol[id(ident)] = sid
        return sid

    # Duplicate names may come from `use` expansion (stdlib modules), which is allowed.
    # We still reject duplicates originating from the same source file (true duplicate definition).
    existing_in_this_scope = scope.values.get(name)
    if existing_in_this_scope:
        same_file = any(ctx.symbols[sid - 1].span.file == ident.span.file for sid in existing_in_this_scope)
        if same_file:
            raise ResolveError(f"Duplicate name in same scope: {name}", ident.span)
    sid = ctx.new_symbol(kind, name, ident.span, owner=owner)
    scope.define("values", name, sid)
    ctx.ident_to_symbol[id(ident)] = sid
    return sid


def _try_resolve_namespaced_value(ctx: _Ctx, e: ast.MemberExpr) -> Optional[SymbolId]:
    # Recognize chains like `std.option.unwrapOr` where each segment is an identifier.
    parts: list[str] = []
    cur: ast.Expr = e
    while isinstance(cur, ast.MemberExpr):
        parts.append(cur.field.name)
        cur = cur.object
    if not isinstance(cur, ast.VarExpr):
        return None
    parts.append(cur.name.name)
    parts = list(reversed(parts))
    if len(parts) < 2:
        return None

    # Last segment is the symbol name; prefix is the stdlib module qname.
    sym_name = parts[-1]
    mod_qname = ".".join(parts[:-1])

    stdlib_root = Path(__file__).resolve().parent.parent / "stdlib"
    mod_path = stdlib_root.joinpath(*mod_qname.split(".")).with_suffix(".flv")
    if not mod_path.exists():
        mod_path = stdlib_root.joinpath(*mod_qname.split(".")) / "__init__.flv"
    if not mod_path.exists():
        return None

    mod_file_suffix = str(mod_path).replace("\\", "/")

    # Filter global matches by source file.
    matches = ctx.global_scope.lookup("values", sym_name)
    if not matches:
        return None
    filtered = [sid for sid in matches if ctx.symbols[sid - 1].span.file.replace("\\", "/").endswith(mod_file_suffix)]
    if not filtered:
        return None
    if len(filtered) > 1:
        raise ResolveError(f"NameAmbiguity: {sym_name}", e.span)
    return filtered[0]


def _define_fn(ctx: _Ctx, fd: ast.FnDecl, *, owner: SymbolId | None) -> SymbolId:
    target_sector: SymbolId | None = None
    if fd.sectorQual is not None:
        matches = ctx.global_scope.lookup("sectors", fd.sectorQual.name)
        if not matches:
            raise ResolveError(f"Unknown sector: {fd.sectorQual.name}", fd.sectorQual.span)
        target_sector = matches[0]
        ctx.ident_to_symbol[id(fd.sectorQual)] = target_sector

    data: dict[str, Any] = {"sector": target_sector}
    if fd.typeParams:
        data["type_params"] = [p.name for p in fd.typeParams]

    if owner is not None:
        scope = ctx.sector_scopes[owner]
        sid = _define_in_scope(ctx, scope, fd.name, SymbolKind.FN, owner=owner)
        for sym in ctx.symbols:
            if sym.id == sid:
                sym_data = dict(sym.data or {})
                sym_data.update(data)
                ctx.symbols[sid - 1] = Symbol(id=sym.id, kind=sym.kind, name=sym.name, span=sym.span, owner=sym.owner, data=sym_data)
                break
        return sid

    sid = _define_in_scope(ctx, ctx.global_scope, fd.name, SymbolKind.FN, owner=None)
    for sym in ctx.symbols:
        if sym.id == sid:
            sym_data = dict(sym.data or {})
            sym_data.update(data)
            ctx.symbols[sid - 1] = Symbol(id=sym.id, kind=sym.kind, name=sym.name, span=sym.span, owner=sym.owner, data=sym_data)
            break
    return sid


def _resolve_uses(ctx: _Ctx, prog: ast.Program) -> None:
    main_sector = _lookup_single(ctx, ctx.global_scope, "sectors", "main")

    for it in prog.items:
        if isinstance(it, ast.PatternDecl):
            name = _qname_str(it.name)
            if name in ctx.pattern_aliases:
                raise ResolveError(f"Duplicate pattern: {name}", it.span)

            def _validate_alias_pat(p: ast.Pattern) -> None:
                if isinstance(p, ast.PWildcard):
                    return
                if isinstance(p, ast.PVar):
                    raise ResolveError("pattern alias cannot bind variables (use _)", p.span)
                if isinstance(p, ast.PConstructor):
                    for a in p.args or []:
                        _validate_alias_pat(a)
                    return

            _validate_alias_pat(it.pat)
            ctx.pattern_aliases[name] = it.pat
            continue
        if isinstance(it, ast.TypeDecl):
            _resolve_type_decl(ctx, it)
        elif isinstance(it, (ast.ConstDecl, ast.LetDecl, ast.NeedDecl)):
            _resolve_expr(ctx, ctx.global_scope, it.value)
        elif isinstance(it, ast.FnDecl):
            _resolve_fn(ctx, ctx.global_scope, it)
        elif isinstance(it, ast.SectorDecl):
            sector_id = _lookup_single(ctx, ctx.global_scope, "sectors", it.name.name)
            scope = ctx.sector_scopes[sector_id]
            for item in it.items:
                if isinstance(item, (ast.LetDecl, ast.NeedDecl)):
                    _resolve_expr(ctx, scope, item.value)
                elif isinstance(item, ast.FnDecl):
                    _resolve_fn(ctx, scope, item)
                elif isinstance(item, ast.OnHandler):
                    _resolve_handler(ctx, scope, item)
        elif isinstance(it, ast.OnHandler):
            if main_sector is not None:
                scope = ctx.sector_scopes[main_sector]
                _resolve_handler(ctx, scope, it)
        elif isinstance(it, ast.UseStmt):
            continue
        elif isinstance(it, (ast.MixinDecl, ast.UseMixinStmt, ast.ResolveMixinStmt)):
            continue


def _resolve_type_decl(ctx: _Ctx, td: ast.TypeDecl) -> None:
    params: dict[str, SymbolId] = {}
    if td.params:
        owner = ctx.typename_to_symbol.get(id(td.name))
        type_param_ids: list[int] = []
        for p in td.params:
            # Unique symbol name to avoid global collisions.
            uniq = f"{_qname_str(td.name)}#T@{p.name}"
            pid = ctx.new_symbol(SymbolKind.TYPE, uniq, p.span, owner=owner)
            params[p.name] = pid
            type_param_ids.append(pid)

        if owner is not None:
            for sym in ctx.symbols:
                if sym.id == owner:
                    sym_data = dict(sym.data or {})
                    sym_data["type_param_ids"] = type_param_ids
                    ctx.symbols[owner - 1] = Symbol(id=sym.id, kind=sym.kind, name=sym.name, span=sym.span, owner=sym.owner, data=sym_data)
                    break
    _resolve_type_rhs(ctx, td.rhs, params=params)


def _resolve_type_rhs(ctx: _Ctx, rhs: ast.TypeRhs, *, params: dict[str, SymbolId]) -> None:
    if isinstance(rhs, ast.TypeAlias):
        _resolve_type_ref(ctx, rhs.target, params=params)
        return
    if isinstance(rhs, ast.RecordType):
        for f in rhs.fields:
            _resolve_type_ref(ctx, f.ty, params=params)
        return
    if isinstance(rhs, ast.SumType):
        for v in rhs.variants:
            if v.payload:
                for t in v.payload:
                    _resolve_type_ref(ctx, t, params=params)
        return


def _resolve_type_ref(ctx: _Ctx, tr: ast.TypeRef, *, params: dict[str, SymbolId]) -> None:
    if isinstance(tr, ast.TypeParen):
        _resolve_type_ref(ctx, tr.inner, params=params)
        return
    if isinstance(tr, ast.TypeName):
        if len(tr.name.parts) == 1:
            p = params.get(tr.name.parts[0].name)
            if p is not None:
                ctx.typename_to_symbol[id(tr.name)] = p
                return
        name = _qname_str(tr.name)
        matches = ctx.global_scope.lookup("types", name)
        if not matches:
            raise ResolveError(f"Unknown type: {name}", tr.span)
        ctx.typename_to_symbol[id(tr.name)] = matches[0]
        if tr.args:
            for a in tr.args:
                _resolve_type_ref(ctx, a, params=params)
        return


def _resolve_fn(ctx: _Ctx, scope: Scope, fd: ast.FnDecl) -> None:
    params: dict[str, SymbolId] = {}
    if fd.typeParams:
        fn_owner = ctx.ident_to_symbol.get(id(fd.name))
        type_param_ids: list[int] = []
        for tp in fd.typeParams:
            uniq = f"{fd.name.name}#T@{tp.name}"
            pid = ctx.new_symbol(SymbolKind.TYPE, uniq, tp.span, owner=fn_owner)
            params[tp.name] = pid
            type_param_ids.append(pid)

        if fn_owner is not None:
            for sym in ctx.symbols:
                if sym.id == fn_owner:
                    sym_data = dict(sym.data or {})
                    sym_data["type_param_ids"] = type_param_ids
                    ctx.symbols[fn_owner - 1] = Symbol(id=sym.id, kind=sym.kind, name=sym.name, span=sym.span, owner=sym.owner, data=sym_data)
                    break

    for p in fd.params:
        _resolve_type_ref(ctx, p.ty, params=params)
    if fd.retType is not None:
        _resolve_type_ref(ctx, fd.retType, params=params)

    inner = scope.child()
    for p in fd.params:
        pid = _define_in_scope(ctx, inner, p.name, SymbolKind.VAR, owner=None)
        ctx.ident_to_symbol[id(p.name)] = pid

    if isinstance(fd.body, ast.BodyExpr):
        _resolve_expr(ctx, inner, fd.body.expr)
    else:
        _resolve_block(ctx, inner, fd.body.block)


def _resolve_handler(ctx: _Ctx, scope: Scope, h: ast.OnHandler) -> None:
    inner = scope.child()
    if h.binder is not None:
        _define_in_scope(ctx, inner, h.binder, SymbolKind.VAR, owner=None)
    if h.when is not None:
        _resolve_expr(ctx, inner, h.when)
    if isinstance(h.body, ast.HandlerExpr):
        _resolve_expr(ctx, inner, h.body.expr)
    else:
        _resolve_block(ctx, inner, h.body.block)


def _resolve_block(ctx: _Ctx, scope: Scope, b: ast.Block) -> None:
    for st in b.stmts:
        _resolve_stmt(ctx, scope, st)


def _resolve_stmt(ctx: _Ctx, scope: Scope, st: ast.Stmt) -> None:
    if isinstance(st, ast.LetStmt):
        _resolve_expr(ctx, scope, st.value)
        _define_in_scope(ctx, scope, st.name, SymbolKind.VAR, owner=None)
        return
    if isinstance(st, ast.AssignStmt):
        _resolve_lvalue(ctx, scope, st.target)
        _resolve_expr(ctx, scope, st.value)
        return
    if isinstance(st, ast.EmitStmt):
        _resolve_expr(ctx, scope, st.expr)
        return
    if isinstance(st, ast.ReturnStmt):
        _resolve_expr(ctx, scope, st.expr)
        return
    if isinstance(st, ast.ExprStmt):
        _resolve_expr(ctx, scope, st.expr)
        return
    if isinstance(st, ast.IfStmt):
        _resolve_expr(ctx, scope, st.cond)
        _resolve_block(ctx, scope.child(), st.thenBlock)
        if st.elseBlock is not None:
            _resolve_block(ctx, scope.child(), st.elseBlock)
        return
    if isinstance(st, ast.ForStmt):
        _resolve_expr(ctx, scope, st.iterable)
        body_scope = scope.child()
        _define_in_scope(ctx, body_scope, st.binder, SymbolKind.VAR, owner=None)
        _resolve_block(ctx, body_scope, st.body)
        return
    if isinstance(st, (ast.StopStmt, ast.YieldStmt)):
        return

    raise ResolveError("Unsupported statement in Phase 2", st.span)


def _resolve_lvalue(ctx: _Ctx, scope: Scope, lv: ast.LValue) -> None:
    if isinstance(lv, ast.LVar):
        _resolve_ident_value(ctx, scope, lv.name)
        return
    if isinstance(lv, ast.LMember):
        _resolve_expr(ctx, scope, lv.object)
        return
    if isinstance(lv, ast.LIndex):
        _resolve_expr(ctx, scope, lv.object)
        _resolve_expr(ctx, scope, lv.index)
        return


def _resolve_expr(ctx: _Ctx, scope: Scope, e: ast.Expr) -> None:
    if isinstance(e, ast.LitExpr):
        return
    if isinstance(e, ast.VarExpr):
        _resolve_ident_value(ctx, scope, e.name)
        return
    if isinstance(e, ast.RecordLitExpr):
        for it in e.items:
            _resolve_expr(ctx, scope, it.value)
        return
    if isinstance(e, ast.TupleLitExpr):
        for it in e.items:
            _resolve_expr(ctx, scope, it)
        return
    if isinstance(e, ast.CallExpr):
        _resolve_expr(ctx, scope, e.callee)
        for a in e.args:
            if isinstance(a, ast.CallArgPos):
                _resolve_expr(ctx, scope, a.value)
            elif isinstance(a, ast.CallArgStar):
                _resolve_expr(ctx, scope, a.value)
            elif isinstance(a, ast.CallArgKw):
                _resolve_expr(ctx, scope, a.value)
            elif isinstance(a, ast.CallArgStarStar):
                _resolve_expr(ctx, scope, a.value)
            else:
                # Backward compatibility: treat as positional arg.
                _resolve_expr(ctx, scope, a)
        return
    if isinstance(e, ast.MemberExpr):
        sid = _try_resolve_namespaced_value(ctx, e)
        if sid is not None:
            ctx.ident_to_symbol[id(e.field)] = sid
            return
        _resolve_expr(ctx, scope, e.object)
        return
    if isinstance(e, ast.IndexExpr):
        _resolve_expr(ctx, scope, e.object)
        _resolve_expr(ctx, scope, e.index)
        return
    if isinstance(e, ast.UnaryExpr):
        _resolve_expr(ctx, scope, e.expr)
        return
    if isinstance(e, ast.BinaryExpr):
        _resolve_expr(ctx, scope, e.left)
        _resolve_expr(ctx, scope, e.right)
        return
    if isinstance(e, ast.PipeExpr):
        _resolve_expr(ctx, scope, e.head)
        for s in e.stages:
            _resolve_expr(ctx, scope, s)
        return
    if isinstance(e, ast.MatchExpr):
        _resolve_expr(ctx, scope, e.scrutinee)
        for arm in e.arms:
            arm_scope = scope.child()
            _resolve_pattern(ctx, arm_scope, arm.pat)
            _resolve_expr(ctx, arm_scope, arm.body)
        return

    # Allow `do:` blocks in expression position (used by match arms).
    if isinstance(e, ast.BodyDo):
        _resolve_block(ctx, scope.child(), e.block)
        return
    if isinstance(e, ast.AwaitExpr):
        name = _qname_str(e.eventType)
        matches = ctx.global_scope.lookup("types", name)
        if matches:
            ctx.typename_to_symbol[id(e.eventType)] = matches[0]
        return
    if isinstance(e, ast.RpcExpr):
        sector_id = _lookup_single(ctx, ctx.global_scope, "sectors", e.sector.name)
        if sector_id is None:
            raise ResolveError(f"Unknown sector: {e.sector.name}", e.sector.span)
        ctx.ident_to_symbol[id(e.sector)] = sector_id

        fn_id = _resolve_sector_fn(ctx, sector_id, e.fnName)
        ctx.ident_to_symbol[id(e.fnName)] = fn_id

        for a in e.args:
            _resolve_expr(ctx, scope, a)
        return
    if isinstance(e, ast.CallSectorExpr):
        sector_id = _lookup_single(ctx, ctx.global_scope, "sectors", e.sector.name)
        if sector_id is None:
            raise ResolveError(f"Unknown sector: {e.sector.name}", e.sector.span)
        ctx.ident_to_symbol[id(e.sector)] = sector_id

        fn_id = _resolve_sector_fn(ctx, sector_id, e.fnName)
        ctx.ident_to_symbol[id(e.fnName)] = fn_id

        for a in e.args:
            _resolve_expr(ctx, scope, a)
        return
    if isinstance(e, ast.ProceedExpr):
        for a in e.args:
            _resolve_expr(ctx, scope, a)
        return

    if isinstance(e, ast.TrySuffixExpr):
        _resolve_expr(ctx, scope, e.inner)
        return

    raise ResolveError("Unsupported expression in Phase 2", e.span)


def _resolve_pattern(ctx: _Ctx, scope: Scope, p: ast.Pattern) -> None:
    if isinstance(p, ast.PWildcard):
        return
    if isinstance(p, ast.PBool):
        return
    if isinstance(p, ast.PVar):
        _define_in_scope(ctx, scope, p.name, SymbolKind.VAR, owner=None)
        return
    if isinstance(p, ast.PConstructor):
        name = _qname_str(p.name)

        # Expand pattern aliases: `pattern Foo = Some(_)` then match `Foo`.
        # Only expand when this constructor is nullary.
        if p.args is None and name in ctx.pattern_aliases:
            seen: set[str] = set()

            def expand(n: str, pat: ast.Pattern) -> ast.Pattern:
                if n in seen:
                    raise ResolveError(f"Cyclic pattern alias: {n}", p.span)
                seen.add(n)
                if isinstance(pat, ast.PConstructor):
                    nn = _qname_str(pat.name)
                    if pat.args is None and nn in ctx.pattern_aliases:
                        return expand(nn, ctx.pattern_aliases[nn])
                    if pat.args:
                        for a in pat.args:
                            _resolve_pattern(ctx, scope, a)
                    return pat
                if isinstance(pat, ast.PVar):
                    return pat
                if isinstance(pat, ast.PWildcard):
                    return pat
                return pat

            expanded = expand(name, ctx.pattern_aliases[name])
            _resolve_pattern(ctx, scope, expanded)
            return

        matches = ctx.global_scope.lookup("values", name)
        if not matches:
            raise ResolveError(f"Unknown constructor pattern: {name}", p.span)
        ctx.typename_to_symbol[id(p.name)] = matches[0]
        if p.args:
            for a in p.args:
                _resolve_pattern(ctx, scope, a)
        return


def _resolve_ident_value(ctx: _Ctx, scope: Scope, ident: ast.Ident) -> SymbolId:
    matches = scope.lookup("values", ident.name)
    if not matches:
        raise ResolveError(f"NameNotFound: {ident.name}", ident.span)
    if len(matches) > 1:
        # If one of the candidates originates from the same source file, prefer it.
        # This allows stdlib modules (flattened into global scope) to refer to their
        # own definitions without being shadowed by imported duplicates.
        same_file = [sid for sid in matches if ctx.symbols[sid - 1].span.file == ident.span.file]
        if len(same_file) == 1:
            sid = same_file[0]
        else:
            raise ResolveError(f"NameAmbiguity: {ident.name}", ident.span)
    else:
        sid = matches[0]
    ctx.ident_to_symbol[id(ident)] = sid
    return sid


def _resolve_sector_fn(ctx: _Ctx, sector_id: SymbolId, fn_name: ast.Ident) -> SymbolId:
    scope = ctx.sector_scopes.get(sector_id)
    matches: list[SymbolId] = []
    if scope is not None:
        matches.extend(scope.lookup("values", fn_name.name))

    for sym in ctx.symbols:
        if sym.kind == SymbolKind.FN and sym.name == fn_name.name:
            if (sym.data or {}).get("sector") == sector_id:
                matches.append(sym.id)

    matches = list(dict.fromkeys(matches))
    if not matches:
        raise ResolveError(f"NameNotFound: {fn_name.name}", fn_name.span)
    if len(matches) > 1:
        raise ResolveError(f"NameAmbiguity: {fn_name.name}", fn_name.span)
    return matches[0]


def _lookup_single(ctx: _Ctx, scope: Scope, ns: str, name: str) -> SymbolId | None:
    matches = scope.lookup(ns, name)
    if not matches:
        return None
    return matches[0]


def _lookup_unique_value(ctx: _Ctx, scope: Scope, name: str, *, span: Span) -> SymbolId:
    matches = scope.lookup("values", name)
    if not matches:
        raise ResolveError(f"NameNotFound: {name}", span)
    if len(matches) > 1:
        raise ResolveError(f"NameAmbiguity: {name}", span)
    return matches[0]
