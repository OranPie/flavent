from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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
    IfStmt,
    IndexExpr,
    LetStmt,
    LitExpr,
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
)
from .resolve import Resolution
from .symbols import Symbol, SymbolId, SymbolKind


@dataclass(frozen=True, slots=True)
class BridgeUse:
    kind: str  # 'rpc' | 'call' | 'pure_call'
    symbol: str
    file: str
    line: int
    col: int


_DEPRECATED_PREFIXES = (
    "_pyBase64",
    "_pySha256",
)


def audit_bridge_usage(hir: Program, res: Resolution) -> dict[str, Any]:
    sym_by_id: dict[SymbolId, Symbol] = {s.id: s for s in res.symbols}

    bridge_file = str(Path(__file__).resolve().parent.parent / "stdlib" / "_bridge_python.flv")
    bridge_file_norm = bridge_file.replace("\\", "/")

    # Sector symbol id for `_bridge_python` if present.
    bridge_sector_id: SymbolId | None = None
    for s in res.symbols:
        if s.kind == SymbolKind.SECTOR and s.name == "_bridge_python":
            bridge_sector_id = s.id
            break

    uses: list[BridgeUse] = []

    def is_bridge_symbol(sym_id: SymbolId) -> bool:
        s = sym_by_id.get(sym_id)
        if s is None:
            return False
        return s.span.file.replace("\\", "/").endswith(bridge_file_norm.split("/")[-2] + "/" + bridge_file_norm.split("/")[-1]) or s.span.file.replace("\\", "/") == bridge_file_norm

    def sym_name(sym_id: SymbolId) -> str:
        s = sym_by_id.get(sym_id)
        return s.name if s is not None else f"<sym:{sym_id}>"

    def add_use(kind: str, sym_id: SymbolId, span) -> None:
        uses.append(
            BridgeUse(
                kind=kind,
                symbol=sym_name(sym_id),
                file=span.file,
                line=span.line,
                col=span.col,
            )
        )

    def visit_expr(e: Expr) -> None:
        if isinstance(e, LitExpr) or isinstance(e, UndefExpr):
            return
        if isinstance(e, VarExpr):
            return
        if isinstance(e, RecordLitExpr):
            for it in e.items:
                visit_expr(it.value)
            return
        if isinstance(e, TupleLitExpr):
            for x in e.items:
                visit_expr(x)
            return
        if isinstance(e, MemberExpr):
            visit_expr(e.object)
            return
        if isinstance(e, IndexExpr):
            visit_expr(e.object)
            visit_expr(e.index)
            return
        if isinstance(e, UnaryExpr):
            visit_expr(e.expr)
            return
        if isinstance(e, BinaryExpr):
            visit_expr(e.left)
            visit_expr(e.right)
            return
        if isinstance(e, CallExpr):
            # Track direct calls to top-level bridge functions.
            if isinstance(e.callee, VarExpr):
                if is_bridge_symbol(e.callee.sym):
                    add_use("pure_call", e.callee.sym, e.span)
            visit_expr(e.callee)
            for a in e.args:
                if isinstance(a, CallArgPos):
                    visit_expr(a.value)
                elif isinstance(a, CallArgStar):
                    visit_expr(a.value)
                elif isinstance(a, CallArgKw):
                    visit_expr(a.value)
                elif isinstance(a, CallArgStarStar):
                    visit_expr(a.value)
                else:
                    # Backward compat / unknown
                    if hasattr(a, "value"):
                        visit_expr(getattr(a, "value"))
            return
        if isinstance(e, MatchExpr):
            visit_expr(e.scrutinee)
            for arm in e.arms:
                if isinstance(arm, MatchArmExpr):
                    visit_expr(arm.body)
            return
        if isinstance(e, AwaitEventExpr):
            return
        if isinstance(e, RpcCallExpr):
            # rpc/call into `_bridge_python` sector
            if bridge_sector_id is not None and e.sector == bridge_sector_id:
                add_use("rpc" if e.awaitResult else "call", e.fn, e.span)
            for a in e.args:
                visit_expr(a)
            return

        # Fallback: attempt to traverse dataclass-ish nodes conservatively.
        if hasattr(e, "__dict__"):
            for v in e.__dict__.values():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, (LitExpr, VarExpr, CallExpr, RpcCallExpr, MatchExpr, RecordLitExpr, TupleLitExpr, MemberExpr, IndexExpr, UnaryExpr, BinaryExpr, AwaitEventExpr, UndefExpr)):
                            visit_expr(item)
                elif isinstance(v, (LitExpr, VarExpr, CallExpr, RpcCallExpr, MatchExpr, RecordLitExpr, TupleLitExpr, MemberExpr, IndexExpr, UnaryExpr, BinaryExpr, AwaitEventExpr, UndefExpr)):
                    visit_expr(v)
            return

    def visit_stmt(st) -> None:
        if isinstance(st, LetStmt):
            visit_expr(st.expr)
            return
        if isinstance(st, AssignStmt):
            visit_expr(st.expr)
            # target may contain expr
            if hasattr(st.target, "object"):
                visit_expr(getattr(st.target, "object"))
            if hasattr(st.target, "index"):
                visit_expr(getattr(st.target, "index"))
            return
        if isinstance(st, IfStmt):
            visit_expr(st.cond)
            visit_block(st.thenBlock)
            if st.elseBlock is not None:
                visit_block(st.elseBlock)
            return
        if isinstance(st, ForStmt):
            visit_expr(st.iterable)
            visit_block(st.body)
            return
        if isinstance(st, MatchStmt):
            visit_expr(st.scrutinee)
            for arm in st.arms:
                if isinstance(arm, MatchArmStmt):
                    visit_block(arm.body)
            return
        if isinstance(st, EmitStmt):
            visit_expr(st.expr)
            return
        if isinstance(st, ReturnStmt):
            visit_expr(st.expr)
            return
        if isinstance(st, AbortHandlerStmt):
            if st.cause is not None:
                visit_expr(st.cause)
            return
        if isinstance(st, ExprStmt):
            visit_expr(st.expr)
            return
        if isinstance(st, (StopStmt, YieldStmt)):
            return

    def visit_block(b: Block) -> None:
        for st in b.stmts:
            visit_stmt(st)

    # Traverse program.
    for fn in hir.fns:
        visit_block(fn.body)
    for sec in hir.sectors:
        for fn in sec.fns:
            visit_block(fn.body)
        for h in sec.handlers:
            visit_block(h.body)

    def is_deprecated(sym: str) -> bool:
        return any(sym.startswith(p) for p in _DEPRECATED_PREFIXES)

    counts: dict[str, int] = {}
    deprecated: dict[str, int] = {}
    for u in uses:
        key = f"{u.kind}:{u.symbol}"
        counts[key] = counts.get(key, 0) + 1
        if u.kind == "pure_call" and is_deprecated(u.symbol):
            deprecated[u.symbol] = deprecated.get(u.symbol, 0) + 1

    return {
        "bridge_file": bridge_file_norm,
        "bridge_sector_present": bridge_sector_id is not None,
        "uses": [asdict(u) for u in uses],
        "counts": counts,
        "deprecated": deprecated,
    }


def format_bridge_warnings(report: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for issue in bridge_warning_issues(report):
        code = issue["code"]
        message = issue["message"]
        out.append(f"BridgeWarning: [{code}] {message}")
    return out


def bridge_warning_issues(report: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    deprecated: dict[str, int] = report.get("deprecated", {})
    uses = report.get("uses", [])
    for name, n in sorted(deprecated.items()):
        loc = None
        for u in uses:
            if u.get("kind") == "pure_call" and u.get("symbol") == name:
                loc = {
                    "file": u.get("file", ""),
                    "line": int(u.get("line", 0) or 0),
                    "col": int(u.get("col", 0) or 0),
                }
                break
        out.append(
            {
                "severity": "warning",
                "code": "WBR001",
                "message": f"deprecated bridge shim used: {name} (count={n})",
                "stage": "bridge_audit",
                "location": loc,
                "hint": "Replace direct/deprecated bridge shim usage with stdlib wrappers.",
                "metadata": {"symbol": name, "count": n},
            }
        )
    return out
