from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Optional

from .span import Span
from .symbols import SymbolId, TypeId


TypeRef = Any


@dataclass(frozen=True, slots=True)
class TypeVar:
    id: TypeId
    span: Span


@dataclass(frozen=True, slots=True)
class TypeApp:
    base: TypeId
    args: list[TypeRef]
    span: Span


@dataclass(frozen=True, slots=True)
class Program:
    types: list[TypeDecl]
    consts: list[ValueDecl]
    globals: list[ValueDecl]
    needs: list[ValueDecl]
    fns: list[FnDecl]
    sectors: list[SectorDecl]
    run: bool
    span: Span


@dataclass(frozen=True, slots=True)
class TypeDecl:
    sym: SymbolId
    rhs: TypeRhs
    span: Span


TypeRhs = Any


@dataclass(frozen=True, slots=True)
class TypeAlias:
    target: TypeRef
    span: Span


@dataclass(frozen=True, slots=True)
class RecordType:
    fields: list[FieldDecl]
    span: Span


@dataclass(frozen=True, slots=True)
class FieldDecl:
    name: str
    ty: TypeRef
    span: Span


@dataclass(frozen=True, slots=True)
class SumType:
    variants: list[VariantDecl]
    span: Span


@dataclass(frozen=True, slots=True)
class VariantDecl:
    ctor: SymbolId
    payload: Optional[list[TypeRef]]
    span: Span


@dataclass(frozen=True, slots=True)
class ValueDecl:
    sym: SymbolId
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class Param:
    sym: SymbolId
    ty: TypeRef
    kind: str  # 'normal' | 'varargs' | 'varkw'
    span: Span


@dataclass(frozen=True, slots=True)
class FnDecl:
    sym: SymbolId
    ownerSector: Optional[SymbolId]
    params: list[Param]
    retType: Optional[TypeRef]
    body: Block
    span: Span


@dataclass(frozen=True, slots=True)
class SectorDecl:
    sym: SymbolId
    fns: list[FnDecl]
    handlers: list[HandlerDecl]
    lets: list[ValueDecl]
    needs: list[ValueDecl]
    span: Span


@dataclass(frozen=True, slots=True)
class HandlerDecl:
    sym: SymbolId
    eventType: TypeId
    binder: Optional[SymbolId]
    when: Optional[Expr]
    body: Block
    span: Span


@dataclass(frozen=True, slots=True)
class Block:
    stmts: list[Stmt]
    span: Span


Stmt = Any
Expr = Any


@dataclass(frozen=True, slots=True)
class LetStmt:
    sym: SymbolId
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class AssignStmt:
    target: LValue
    op: str
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class IfStmt:
    cond: Expr
    thenBlock: Block
    elseBlock: Optional[Block]
    span: Span


@dataclass(frozen=True, slots=True)
class ForStmt:
    binder: SymbolId
    iterable: Expr
    body: Block
    span: Span


@dataclass(frozen=True, slots=True)
class EmitStmt:
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class ReturnStmt:
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class AbortHandlerStmt:
    cause: Optional[Expr]
    span: Span


@dataclass(frozen=True, slots=True)
class StopStmt:
    span: Span


@dataclass(frozen=True, slots=True)
class YieldStmt:
    span: Span


@dataclass(frozen=True, slots=True)
class ExprStmt:
    expr: Expr
    span: Span


LValue = Any


@dataclass(frozen=True, slots=True)
class LVar:
    sym: SymbolId
    span: Span


@dataclass(frozen=True, slots=True)
class LMember:
    object: Expr
    field: str
    span: Span


@dataclass(frozen=True, slots=True)
class LIndex:
    object: Expr
    index: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class Literal:
    kind: str
    value: Any
    span: Span


@dataclass(frozen=True, slots=True)
class LitExpr:
    lit: Literal
    span: Span


@dataclass(frozen=True, slots=True)
class VarExpr:
    sym: SymbolId
    span: Span


@dataclass(frozen=True, slots=True)
class UndefExpr:
    span: Span


@dataclass(frozen=True, slots=True)
class RecordItem:
    key: str
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class RecordLitExpr:
    items: list[RecordItem]
    span: Span


@dataclass(frozen=True, slots=True)
class TupleLitExpr:
    items: list[Expr]
    span: Span


CallArg = Any


@dataclass(frozen=True, slots=True)
class CallArgPos:
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class CallArgStar:
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class CallArgKw:
    name: str
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class CallArgStarStar:
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class CallExpr:
    callee: Expr
    args: list[CallArg]
    span: Span


@dataclass(frozen=True, slots=True)
class MemberExpr:
    object: Expr
    field: str
    span: Span


@dataclass(frozen=True, slots=True)
class IndexExpr:
    object: Expr
    index: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class UnaryExpr:
    op: str
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class BinaryExpr:
    op: str
    left: Expr
    right: Expr
    span: Span


Pattern = Any


@dataclass(frozen=True, slots=True)
class PWildcard:
    span: Span


@dataclass(frozen=True, slots=True)
class PVar:
    sym: SymbolId
    span: Span


@dataclass(frozen=True, slots=True)
class PBool:
    value: bool
    span: Span


@dataclass(frozen=True, slots=True)
class PCtor:
    ctor: SymbolId
    args: Optional[list[Pattern]]
    span: Span


@dataclass(frozen=True, slots=True)
class MatchArmExpr:
    pat: Pattern
    body: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class MatchExpr:
    scrutinee: Expr
    arms: list[MatchArmExpr]
    span: Span


@dataclass(frozen=True, slots=True)
class MatchArmStmt:
    pat: Pattern
    body: Block
    span: Span


@dataclass(frozen=True, slots=True)
class MatchStmt:
    scrutinee: Expr
    arms: list[MatchArmStmt]
    span: Span


@dataclass(frozen=True, slots=True)
class AwaitEventExpr:
    typeId: TypeId
    span: Span


@dataclass(frozen=True, slots=True)
class RpcCallExpr:
    sector: SymbolId
    fn: SymbolId
    args: list[Expr]
    awaitResult: bool
    span: Span


def node_to_dict(node: Any) -> Any:
    if is_dataclass(node):
        d = asdict(node)
        d["_type"] = node.__class__.__name__
        return d
    if isinstance(node, list):
        return [node_to_dict(x) for x in node]
    if isinstance(node, dict):
        return {k: node_to_dict(v) for k, v in node.items()}
    return node
