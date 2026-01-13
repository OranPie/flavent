from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, Optional

from .diagnostics import EffectError
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
    StopStmt,
    TupleLitExpr,
    UnaryExpr,
    UndefExpr,
    VarExpr,
    YieldStmt,
    PCtor,
    PVar,
    PBool,
    PWildcard,
)
from .resolve import Resolution
from .symbols import Symbol, SymbolId, SymbolKind


class StopProgram(Exception):
    pass


@dataclass(frozen=True)
class AbortHandler(Exception):
    cause: Any


@dataclass
class Bridge:
    def call(self, name: str, args: list[Any]) -> Any:
        raise RuntimeError(f"bridge call not allowed in runtime tests: {name}({len(args)} args)")


def run_hir_program(
    hir: Program,
    res: Resolution,
    *,
    entry_event_type: str | None = None,
    bridge: Bridge | None = None,
) -> None:
    """Execute a minimal subset of Flavent by interpreting HIR.

    This is intentionally small (MVP) and is meant to support flvtest runtime tests.
    """

    if bridge is None:
        bridge = Bridge()

    sym_by_id: dict[SymbolId, Symbol] = {s.id: s for s in res.symbols}

    def is_pure_bridge_sym(sym: SymbolId) -> bool:
        s = sym_by_id.get(sym)
        if s is None:
            return False
        return s.span.file.replace("\\", "/").endswith("/stdlib/_bridge_python.flv")

    def eval_pure_bridge(name: str, args: list[Any]) -> Any:
        # String primitives
        if name == "strLen":
            return len(str(args[0]))
        if name == "strCodeAt":
            s = str(args[0])
            i = int(args[1])
            if i < 0 or i >= len(s):
                return 0
            return ord(s[i])
        if name == "strSlice":
            s = str(args[0])
            a = int(args[1])
            b = int(args[2])
            a = max(0, min(len(s), a))
            b = max(0, min(len(s), b))
            if b < a:
                b = a
            return s[a:b]
        if name == "strFromCode":
            code = int(args[0])
            try:
                return chr(code)
            except Exception:
                return ""

        # Bytes primitives (Bytes represented as python bytes)
        if name == "_pyBytesLen":
            return len(bytes(args[0]))
        if name == "_pyBytesGet":
            b = bytes(args[0])
            i = int(args[1])
            if i < 0 or i >= len(b):
                return 0
            return int(b[i])
        if name == "_pyBytesSlice":
            b = bytes(args[0])
            a = int(args[1])
            c = int(args[2])
            a = max(0, min(len(b), a))
            c = max(0, min(len(b), c))
            if c < a:
                c = a
            return b[a:c]
        if name == "_pyBytesConcat":
            return bytes(args[0]) + bytes(args[1])
        if name == "_pyBytesFromByte":
            x = int(args[0]) & 0xFF
            return bytes([x])

        # U32 primitives: wrap to 32-bit unsigned range
        mask = 0xFFFFFFFF
        if name == "_pyU32Wrap":
            return int(args[0]) & mask
        if name == "_pyU32And":
            return (int(args[0]) & int(args[1])) & mask
        if name == "_pyU32Or":
            return (int(args[0]) | int(args[1])) & mask
        if name == "_pyU32Xor":
            return (int(args[0]) ^ int(args[1])) & mask
        if name == "_pyU32Not":
            return (~int(args[0])) & mask
        if name == "_pyU32Shl":
            return (int(args[0]) << (int(args[1]) & 31)) & mask
        if name == "_pyU32Shr":
            return (int(args[0]) >> (int(args[1]) & 31)) & mask

        raise RuntimeError(f"unsupported pure bridge primitive: {name}")

    # Resolve `_bridge_python` sector symbol.
    bridge_sector_id: SymbolId | None = None
    for s in res.symbols:
        if s.kind == SymbolKind.SECTOR and s.name == "_bridge_python":
            bridge_sector_id = s.id
            break

    fn_by_sym: dict[SymbolId, Any] = {}
    for fn in hir.fns:
        fn_by_sym[fn.sym] = fn
    for sec in hir.sectors:
        for fn in sec.fns:
            fn_by_sym[fn.sym] = fn

    ctor_by_sym: dict[SymbolId, str] = {s.id: s.name for s in res.symbols if s.kind == SymbolKind.CTOR}

    type_by_id: dict[int, str] = {s.id: s.name for s in res.symbols if s.kind == SymbolKind.TYPE}

    def find_type_id(name: str) -> int | None:
        for tid, tname in type_by_id.items():
            if tname == name:
                return tid
        return None

    entry_tid: int | None = None
    if entry_event_type is not None:
        entry_tid = find_type_id(entry_event_type)
        if entry_tid is None:
            raise RuntimeError(f"entry event type not found: {entry_event_type}")

    # Init sector state (populated after eval_expr is defined below).
    sector_state: dict[SymbolId, dict[SymbolId, Any]] = {}

    # Event loop structures.
    # - events_by_type: queued events by TypeId.
    # - waiting: suspended tasks waiting for a TypeId.
    # - runnable: tasks ready to run.
    events_by_type: dict[int, list[Any]] = {}
    waiting: dict[int, list[_Task]] = {}
    runnable: list[_Task] = []

    def deep_eq(a: Any, b: Any) -> bool:
        if type(a) != type(b):
            return False
        if isinstance(a, (int, float, bool, str, bytes)) or a is None:
            return a == b
        if isinstance(a, dict):
            if a.keys() != b.keys():
                return False
            return all(deep_eq(a[k], b[k]) for k in a.keys())
        if isinstance(a, tuple) and len(a) == 2 and isinstance(a[0], str):
            # sum value: (CtorName, payload)
            return a[0] == b[0] and deep_eq(a[1], b[1])
        if isinstance(a, tuple):
            return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(a, b))
        return a == b

    def make_sum(name: str, payload: list[Any]) -> Any:
        return (name, payload)

    def list_from_py(xs: list[Any]) -> Any:
        # Represent List[T] as Cons(x, rest) / Nil sum values.
        out: Any = make_sum("Nil", [])
        for x in reversed(xs):
            out = make_sum("Cons", [x, out])
        return out

    def list_to_py(v: Any) -> list[Any]:
        out: list[Any] = []
        cur = v
        while True:
            if isinstance(cur, tuple) and cur[0] == "Nil":
                return out
            if isinstance(cur, tuple) and cur[0] == "Cons" and isinstance(cur[1], list) and len(cur[1]) == 2:
                out.append(cur[1][0])
                cur = cur[1][1]
                continue
            raise RuntimeError("not a List")

    @dataclass
    class _Task:
        gen: Generator[Any, Any, Any]
        sector: SymbolId | None
        env: dict[SymbolId, Any]
        env_event_types: dict[SymbolId, int]

    def eval_expr_gen(
        e: Expr,
        env: dict[SymbolId, Any],
        current_sector: SymbolId | None,
        env_event_types: dict[SymbolId, int],
    ) -> Generator[Any, Any, Any]:
        if isinstance(e, LitExpr):
            if e.lit.kind == "LitInt":
                # Parser stores INT token text (normalized decimal) as a string.
                return int(e.lit.value)
            if e.lit.kind == "LitFloat":
                return float(e.lit.value)
            if e.lit.kind == "LitBytes":
                # Lexer stores raw bytes literal contents as a string.
                return str(e.lit.value).encode("utf-8")
            return e.lit.value

        if isinstance(e, UndefExpr):
            return None

        if isinstance(e, VarExpr):
            if e.sym in env:
                return env[e.sym]
            if current_sector is not None and e.sym in sector_state.get(current_sector, {}):
                return sector_state[current_sector][e.sym]
            # Nullary constructors are referenced as variables in expressions.
            ctor_name = ctor_by_sym.get(e.sym)
            if ctor_name is not None:
                return make_sum(ctor_name, [])
            # Unbound globals default to None for MVP.
            return None

        if isinstance(e, RecordLitExpr):
            out: dict[str, Any] = {}
            for it in e.items:
                out[it.key] = (yield from eval_expr_gen(it.value, env, current_sector, env_event_types))
            return out

        if isinstance(e, TupleLitExpr):
            items: list[Any] = []
            for x in e.items:
                items.append((yield from eval_expr_gen(x, env, current_sector, env_event_types)))
            return tuple(items)

        if isinstance(e, MemberExpr):
            obj = (yield from eval_expr_gen(e.object, env, current_sector, env_event_types))
            if isinstance(obj, dict):
                return obj.get(e.field)
            raise RuntimeError("member access on non-record")

        if isinstance(e, IndexExpr):
            obj = (yield from eval_expr_gen(e.object, env, current_sector, env_event_types))
            idx = (yield from eval_expr_gen(e.index, env, current_sector, env_event_types))
            if isinstance(obj, (list, tuple)):
                return obj[int(idx)]
            raise RuntimeError("index on non-seq")

        if isinstance(e, UnaryExpr):
            v = (yield from eval_expr_gen(e.expr, env, current_sector, env_event_types))
            if e.op == "-":
                return -v
            if e.op == "not":
                return not v
            raise RuntimeError(f"unhandled unary op: {e.op}")

        if isinstance(e, BinaryExpr):
            a = (yield from eval_expr_gen(e.left, env, current_sector, env_event_types))
            b = (yield from eval_expr_gen(e.right, env, current_sector, env_event_types))
            op = e.op
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if op == "/":
                if isinstance(a, int) and isinstance(b, int):
                    return a // b
                return a / b
            if op == "==":
                return deep_eq(a, b)
            if op == "!=":
                return not deep_eq(a, b)
            if op == "<":
                return a < b
            if op == "<=":
                return a <= b
            if op == ">":
                return a > b
            if op == ">=":
                return a >= b
            if op == "and":
                return bool(a) and bool(b)
            if op == "or":
                return bool(a) or bool(b)
            raise RuntimeError(f"unhandled binary op: {op}")

        if isinstance(e, MatchExpr):
            scr = (yield from eval_expr_gen(e.scrutinee, env, current_sector, env_event_types))
            for arm in e.arms:
                assert isinstance(arm, MatchArmExpr)
                ok, binds = match_pattern(arm.pat, scr)
                if ok:
                    env2 = dict(env)
                    env2.update(binds)
                    return (yield from eval_expr_gen(arm.body, env2, current_sector, env_event_types))
            raise RuntimeError("non-exhaustive match")

        if isinstance(e, CallExpr):
            callee_v = e.callee
            # ctor call
            if isinstance(callee_v, VarExpr) and callee_v.sym in ctor_by_sym:
                name = ctor_by_sym[callee_v.sym]
                payload: list[Any] = []
                for a in e.args:
                    if isinstance(a, CallArgPos):
                        payload.append((yield from eval_expr_gen(a.value, env, current_sector, env_event_types)))
                    elif isinstance(a, CallArgStar):
                        payload.extend(list_to_py((yield from eval_expr_gen(a.value, env, current_sector, env_event_types))))
                    elif isinstance(a, CallArgKw):
                        payload.append((yield from eval_expr_gen(a.value, env, current_sector, env_event_types)))
                    elif isinstance(a, CallArgStarStar):
                        payload.append((yield from eval_expr_gen(a.value, env, current_sector, env_event_types)))
                    else:
                        # Backward compatibility: treat as positional arg.
                        payload.append((yield from eval_expr_gen(a, env, current_sector, env_event_types)))
                return make_sum(name, payload)

            # Pure bridge primitive call.
            if isinstance(callee_v, VarExpr) and is_pure_bridge_sym(callee_v.sym):
                sym = sym_by_id.get(callee_v.sym)
                fn_name = sym.name if sym is not None else str(callee_v.sym)
                args_pos2: list[Any] = []
                for a in e.args:
                    if isinstance(a, CallArgPos):
                        args_pos2.append((yield from eval_expr_gen(a.value, env, current_sector, env_event_types)))
                    elif isinstance(a, CallArgStar):
                        args_pos2.extend(list_to_py((yield from eval_expr_gen(a.value, env, current_sector, env_event_types))))
                    elif isinstance(a, CallArgKw):
                        # ignore keyword args in MVP runtime
                        args_pos2.append((yield from eval_expr_gen(a.value, env, current_sector, env_event_types)))
                    elif isinstance(a, CallArgStarStar):
                        # ignore in MVP runtime
                        pass
                    else:
                        args_pos2.append((yield from eval_expr_gen(a, env, current_sector, env_event_types)))
                return eval_pure_bridge(fn_name, args_pos2)

            # function call
            if isinstance(callee_v, VarExpr) and callee_v.sym in fn_by_sym:
                fn = fn_by_sym[callee_v.sym]
                args_pos: list[Any] = []
                kwargs: dict[str, Any] = {}
                for a in e.args:
                    if isinstance(a, CallArgPos):
                        args_pos.append((yield from eval_expr_gen(a.value, env, current_sector, env_event_types)))
                    elif isinstance(a, CallArgStar):
                        args_pos.extend(list_to_py((yield from eval_expr_gen(a.value, env, current_sector, env_event_types))))
                    elif isinstance(a, CallArgKw):
                        kwargs[a.name] = (yield from eval_expr_gen(a.value, env, current_sector, env_event_types))
                    elif isinstance(a, CallArgStarStar):
                        # ignore for MVP
                        pass
                    else:
                        # Backward compatibility: treat as positional arg.
                        args_pos.append((yield from eval_expr_gen(a, env, current_sector, env_event_types)))
                return (yield from call_fn_gen(fn, args_pos, kwargs, current_sector))

            raise RuntimeError("unsupported call")

        if isinstance(e, RpcCallExpr):
            args: list[Any] = []
            for a in e.args:
                args.append((yield from eval_expr_gen(a, env, current_sector, env_event_types)))
            if bridge_sector_id is not None and e.sector == bridge_sector_id:
                fn_name = sym_by_id.get(e.fn).name if sym_by_id.get(e.fn) else str(e.fn)
                return bridge.call(fn_name, args)

            # Cross-sector call into another sector: execute callee in that sector context.
            fn = fn_by_sym.get(e.fn)
            if fn is None:
                raise RuntimeError("unknown rpc target")
            out = (yield from call_fn_gen(fn, args, {}, e.sector))
            return out if e.awaitResult else None

        if isinstance(e, AwaitEventExpr):
            ev = yield ("await", e.typeId)
            return ev

        raise RuntimeError(f"unhandled expr: {type(e).__name__}")

    def eval_expr(e: Expr, env: dict[SymbolId, Any], current_sector: SymbolId | None) -> Any:
        gen = eval_expr_gen(e, env, current_sector, {})
        try:
            x = next(gen)
        except StopIteration as si:
            return si.value
        raise RuntimeError(f"unexpected runtime yield in pure expression: {x!r}")

    # Populate sector_state (pure initializers only).
    for sec in hir.sectors:
        env: dict[SymbolId, Any] = {}
        for d in sec.lets:
            # Evaluate sequentially; allow referencing previous lets via `env`.
            env[d.sym] = eval_expr(d.expr, env, None)
        sector_state[sec.sym] = env

    def match_pattern(pat, v: Any) -> tuple[bool, dict[SymbolId, Any]]:
        if isinstance(pat, PWildcard):
            return True, {}
        if isinstance(pat, PBool):
            return bool(v) == pat.value, {}
        if isinstance(pat, PVar):
            return True, {pat.sym: v}
        if isinstance(pat, PCtor):
            if not (isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], list)):
                return False, {}
            name, payload = v
            ctor_name = ctor_by_sym.get(pat.ctor)
            if ctor_name != name:
                return False, {}
            if pat.args is None:
                return True, {}
            if len(pat.args) != len(payload):
                return False, {}
            binds: dict[SymbolId, Any] = {}
            for sp, sv in zip(pat.args, payload, strict=True):
                ok, b2 = match_pattern(sp, sv)
                if not ok:
                    return False, {}
                binds.update(b2)
            return True, binds
        return False, {}

    def exec_block_gen(
        b: Block,
        env: dict[SymbolId, Any],
        current_sector: SymbolId | None,
        env_event_types: dict[SymbolId, int],
    ) -> Generator[Any, Any, Any]:
        for st in b.stmts:
            yield from exec_stmt_gen(st, env, current_sector, env_event_types)
        return None

    def exec_stmt_gen(
        st,
        env: dict[SymbolId, Any],
        current_sector: SymbolId | None,
        env_event_types: dict[SymbolId, int],
    ) -> Generator[Any, Any, None]:
        if isinstance(st, LetStmt):
            v = (yield from eval_expr_gen(st.expr, env, current_sector, env_event_types))
            env[st.sym] = v
            if isinstance(st.expr, AwaitEventExpr):
                env_event_types[st.sym] = st.expr.typeId
            return
        if isinstance(st, AssignStmt):
            v = (yield from eval_expr_gen(st.expr, env, current_sector, env_event_types))
            if isinstance(st.target, LVar):
                if st.target.sym in env:
                    env[st.target.sym] = v
                elif current_sector is not None and st.target.sym in sector_state.get(current_sector, {}):
                    sector_state[current_sector][st.target.sym] = v
                else:
                    env[st.target.sym] = v
                return
            if isinstance(st.target, LMember):
                obj = (yield from eval_expr_gen(st.target.object, env, current_sector, env_event_types))
                if not isinstance(obj, dict):
                    raise RuntimeError("assign member on non-record")
                obj[st.target.field] = v
                return
            if isinstance(st.target, LIndex):
                obj = (yield from eval_expr_gen(st.target.object, env, current_sector, env_event_types))
                idx = (yield from eval_expr_gen(st.target.index, env, current_sector, env_event_types))
                obj[int(idx)] = v
                return
            raise RuntimeError("unsupported assign target")
        if isinstance(st, IfStmt):
            cond = (yield from eval_expr_gen(st.cond, env, current_sector, env_event_types))
            if cond:
                yield from exec_block_gen(st.thenBlock, env, current_sector, env_event_types)
            elif st.elseBlock is not None:
                yield from exec_block_gen(st.elseBlock, env, current_sector, env_event_types)
            return
        if isinstance(st, ForStmt):
            it = (yield from eval_expr_gen(st.iterable, env, current_sector, env_event_types))
            for x in list_to_py(it):
                env[st.binder] = x
                yield from exec_block_gen(st.body, env, current_sector, env_event_types)
            return
        if isinstance(st, MatchStmt):
            scr = (yield from eval_expr_gen(st.scrutinee, env, current_sector, env_event_types))
            for arm in st.arms:
                assert isinstance(arm, MatchArmStmt)
                ok, binds = match_pattern(arm.pat, scr)
                if ok:
                    # Execute in the same env so assignments to existing variables
                    # (e.g. lowering-produced `res_sym`) are preserved, but treat
                    # pattern bindings as scoped locals.
                    saved = dict(env)
                    env.update(binds)
                    try:
                        yield from exec_block_gen(arm.body, env, current_sector, env_event_types)
                    finally:
                        for k in binds.keys():
                            if k in saved:
                                env[k] = saved[k]
                            else:
                                env.pop(k, None)
                    return
            raise RuntimeError("non-exhaustive match stmt")
        if isinstance(st, EmitStmt):
            # Minimal event loop: require emitting an event-typed variable.
            if isinstance(st.expr, VarExpr) and st.expr.sym in env_event_types:
                tid = env_event_types[st.expr.sym]
                val = (yield from eval_expr_gen(st.expr, env, current_sector, env_event_types))
                yield ("emit", tid, val)
                return
            raise RuntimeError("emit currently only supports event-typed vars (binder or await result)")
            return
        if isinstance(st, ReturnStmt):
            raise _Return((yield from eval_expr_gen(st.expr, env, current_sector, env_event_types)))
        if isinstance(st, AbortHandlerStmt):
            cause = (yield from eval_expr_gen(st.cause, env, current_sector, env_event_types)) if st.cause is not None else None
            raise AbortHandler(cause=cause)
        if isinstance(st, StopStmt):
            raise StopProgram()
        if isinstance(st, YieldStmt):
            return
        if isinstance(st, ExprStmt):
            _ = (yield from eval_expr_gen(st.expr, env, current_sector, env_event_types))
            return
        raise RuntimeError(f"unhandled stmt: {type(st).__name__}")

    class _Return(Exception):
        def __init__(self, value: Any):
            self.value = value

    def call_fn_gen(
        fn,
        args_pos: list[Any],
        kwargs: dict[str, Any],
        current_sector: SymbolId | None,
    ) -> Generator[Any, Any, Any]:
        env: dict[SymbolId, Any] = {}
        env_event_types: dict[SymbolId, int] = {}
        ai = 0
        for p in fn.params:
            if p.kind == "normal":
                if ai < len(args_pos):
                    env[p.sym] = args_pos[ai]
                    ai += 1
                elif p.sym in kwargs:
                    env[p.sym] = kwargs[p.sym]
                else:
                    env[p.sym] = None
            elif p.kind == "varargs":
                env[p.sym] = list_from_py(args_pos[ai:])
                ai = len(args_pos)
            elif p.kind == "varkw":
                env[p.sym] = {}

        try:
            yield from exec_block_gen(fn.body, env, current_sector, env_event_types)
        except _Return as r:
            return r.value
        return None

    def enqueue_event(tid: int, value: Any) -> None:
        events_by_type.setdefault(tid, []).append(value)
        # Wake one waiter if present.
        ws = waiting.get(tid)
        if ws:
            t = ws.pop(0)
            runnable.append(t)

    def make_handler_task(h: HandlerDecl, sec_sym: SymbolId, ev_value: Any) -> _Task:
        env: dict[SymbolId, Any] = {}
        env_event_types: dict[SymbolId, int] = {}
        if h.binder is not None:
            env[h.binder] = ev_value
            env_event_types[h.binder] = h.eventType

        def _gen() -> Generator[Any, Any, Any]:
            yield from exec_block_gen(h.body, env, sec_sym, env_event_types)
            return None

        return _Task(gen=_gen(), sector=sec_sym, env=env, env_event_types=env_event_types)

    def dispatch_one_event() -> bool:
        # Deterministic: smallest type id first.
        for tid in sorted(events_by_type.keys()):
            q = events_by_type.get(tid)
            if not q:
                continue
            ev = q.pop(0)
            # Schedule handlers in program order.
            for sec in hir.sectors:
                for h in sec.handlers:
                    if h.eventType == tid:
                        runnable.append(make_handler_task(h, sec.sym, ev))
            return True
        return False

    try:
        # Seed initial event.
        if entry_tid is not None:
            enqueue_event(entry_tid, {})
        else:
            # If no entry event specified, just run nothing.
            return

        steps = 0
        while True:
            # If nothing runnable, try to dispatch a queued event.
            if not runnable:
                if not dispatch_one_event():
                    return

            task = runnable.pop(0)

            try:
                req = next(task.gen)
            except StopProgram:
                return
            except AbortHandler as ah:
                raise RuntimeError(f"handler aborted: {ah.cause!r}")
            except StopIteration:
                continue

            if isinstance(req, tuple) and req and req[0] == "emit":
                _, tid, val = req
                enqueue_event(int(tid), val)
                runnable.append(task)
                continue

            if isinstance(req, tuple) and req and req[0] == "await":
                _, tid = req
                tid = int(tid)
                # If an event is already queued, consume immediately.
                q = events_by_type.get(tid)
                if q:
                    ev = q.pop(0)
                    try:
                        req2 = task.gen.send(ev)
                    except StopProgram:
                        return
                    except AbortHandler as ah:
                        raise RuntimeError(f"handler aborted: {ah.cause!r}")
                    except StopIteration:
                        continue
                    # The resumed step may have yielded again; push back and handle next loop.
                    runnable.append(_Task(gen=_prepend(req2, task.gen), sector=task.sector, env=task.env, env_event_types=task.env_event_types))
                else:
                    waiting.setdefault(tid, []).append(task)
                continue

            # Unknown yield: just keep running.
            runnable.append(task)

            steps += 1
            if steps > 100000:
                raise RuntimeError("runtime exceeded step limit")
    except StopProgram:
        return


def _prepend(first, gen):
    # Helper to re-yield a value already produced by send().
    v = first
    while True:
        if v is not None:
            sent = yield v
        else:
            sent = yield
        v = gen.send(sent)


__all__ = ["Bridge", "run_hir_program"]
