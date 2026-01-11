from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Optional

from .span import Span


@dataclass(frozen=True, slots=True)
class Ident:
    name: str
    span: Span


@dataclass(frozen=True, slots=True)
class QualifiedName:
    parts: list[Ident]
    span: Span


@dataclass(frozen=True, slots=True)
class Program:
    items: list[TopItem]
    run: Optional[RunStmt]
    span: Span


@dataclass(frozen=True, slots=True)
class RunStmt:
    span: Span


TopItem = Any


@dataclass(frozen=True, slots=True)
class TypeDecl:
    name: QualifiedName
    params: Optional[list[Ident]]
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
    name: Ident
    ty: TypeRef
    span: Span


@dataclass(frozen=True, slots=True)
class SumType:
    variants: list[VariantDecl]
    span: Span


@dataclass(frozen=True, slots=True)
class VariantDecl:
    name: Ident
    payload: Optional[list[TypeRef]]
    span: Span


TypeRef = Any


@dataclass(frozen=True, slots=True)
class TypeName:
    name: QualifiedName
    args: Optional[list[TypeRef]]
    span: Span


@dataclass(frozen=True, slots=True)
class TypeParen:
    inner: TypeRef
    span: Span


@dataclass(frozen=True, slots=True)
class ConstDecl:
    name: Ident
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class LetDecl:
    name: Ident
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class NeedAttr:
    cache: Optional[str]
    cacheFail: Optional[str]
    span: Span


@dataclass(frozen=True, slots=True)
class NeedDecl:
    name: Ident
    attrs: Optional[NeedAttr]
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class ParamDecl:
    name: Ident
    ty: TypeRef
    kind: str  # 'normal' | 'varargs' | 'varkw'
    span: Span


FnBody = Any


@dataclass(frozen=True, slots=True)
class BodyExpr:
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class BodyDo:
    block: Block
    span: Span


@dataclass(frozen=True, slots=True)
class FnDecl:
    name: Ident
    sectorQual: Optional[Ident]
    typeParams: Optional[list[Ident]]
    params: list[ParamDecl]
    retType: Optional[TypeRef]
    body: FnBody
    span: Span


@dataclass(frozen=True, slots=True)
class SupervisorSpec:
    strategy: Optional[str]
    maxRestarts: Optional[dict[str, int]]
    mailbox: Optional[str]
    needCache: Optional[str]
    onError: Optional[str]
    span: Span


@dataclass(frozen=True, slots=True)
class SectorDecl:
    name: Ident
    supervisor: Optional[SupervisorSpec]
    items: list[Any]
    span: Span


@dataclass(frozen=True, slots=True)
class EventType:
    name: QualifiedName
    span: Span


@dataclass(frozen=True, slots=True)
class EventCall:
    name: QualifiedName
    args: list[Expr]
    span: Span


EventPattern = Any


HandlerBody = Any


@dataclass(frozen=True, slots=True)
class HandlerExpr:
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class HandlerDo:
    block: Block
    span: Span


@dataclass(frozen=True, slots=True)
class OnHandler:
    event: EventPattern
    binder: Optional[Ident]
    when: Optional[Expr]
    body: HandlerBody
    span: Span


@dataclass(frozen=True, slots=True)
class MixinTargetType:
    name: QualifiedName
    span: Span


@dataclass(frozen=True, slots=True)
class MixinTargetSector:
    name: Ident
    span: Span


MixinTarget = Any


@dataclass(frozen=True, slots=True)
class FnSignature:
    name: Ident
    params: list[ParamDecl]
    retType: Optional[TypeRef]
    span: Span


@dataclass(frozen=True, slots=True)
class MixinFnAdd:
    sig: FnSignature
    body: FnBody
    span: Span


@dataclass(frozen=True, slots=True)
class MixinFieldAdd:
    name: Ident
    ty: TypeRef
    span: Span


@dataclass(frozen=True, slots=True)
class MixinAround:
    sig: FnSignature
    block: Block
    span: Span


MixinItem = Any


@dataclass(frozen=True, slots=True)
class MixinDecl:
    name: QualifiedName
    version: int
    target: MixinTarget
    items: list[MixinItem]
    span: Span


@dataclass(frozen=True, slots=True)
class UseStmt:
    name: QualifiedName
    span: Span


@dataclass(frozen=True, slots=True)
class UseMixinStmt:
    name: QualifiedName
    version: int
    span: Span


@dataclass(frozen=True, slots=True)
class PreferRef:
    name: QualifiedName
    version: int


@dataclass(frozen=True, slots=True)
class PreferRule:
    prefer: PreferRef
    over: PreferRef
    span: Span


@dataclass(frozen=True, slots=True)
class ResolveMixinStmt:
    rules: list[PreferRule]
    span: Span


@dataclass(frozen=True, slots=True)
class PatternDecl:
    name: QualifiedName
    pat: Pattern
    span: Span


@dataclass(frozen=True, slots=True)
class Block:
    stmts: list[Stmt]
    span: Span


Stmt = Any
Expr = Any


@dataclass(frozen=True, slots=True)
class LetStmt:
    name: Ident
    value: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class LVar:
    name: Ident
    span: Span


@dataclass(frozen=True, slots=True)
class LMember:
    object: Expr
    field: Ident
    span: Span


@dataclass(frozen=True, slots=True)
class LIndex:
    object: Expr
    index: Expr
    span: Span


LValue = Any


@dataclass(frozen=True, slots=True)
class AssignStmt:
    target: LValue
    op: str
    value: Expr
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
class ExprStmt:
    expr: Expr
    span: Span


@dataclass(frozen=True, slots=True)
class StopStmt:
    span: Span


@dataclass(frozen=True, slots=True)
class YieldStmt:
    span: Span


@dataclass(frozen=True, slots=True)
class IfStmt:
    cond: Expr
    thenBlock: Block
    elseBlock: Optional[Block]
    span: Span


@dataclass(frozen=True, slots=True)
class ForStmt:
    binder: Ident
    iterable: Expr
    body: Block
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
    name: Ident
    span: Span


@dataclass(frozen=True, slots=True)
class RecordItem:
    key: Ident
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
    name: Ident
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
    field: Ident
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


@dataclass(frozen=True, slots=True)
class PipeExpr:
    head: Expr
    stages: list[Expr]
    span: Span


@dataclass(frozen=True, slots=True)
class MatchArm:
    pat: Pattern
    body: Expr
    span: Span


Pattern = Any


@dataclass(frozen=True, slots=True)
class PWildcard:
    span: Span


@dataclass(frozen=True, slots=True)
class PVar:
    name: Ident
    span: Span


@dataclass(frozen=True, slots=True)
class PConstructor:
    name: QualifiedName
    args: Optional[list[Pattern]]
    span: Span


@dataclass(frozen=True, slots=True)
class PBool:
    value: bool
    span: Span


@dataclass(frozen=True, slots=True)
class MatchExpr:
    scrutinee: Expr
    arms: list[MatchArm]
    span: Span


@dataclass(frozen=True, slots=True)
class AwaitExpr:
    eventType: QualifiedName
    span: Span


@dataclass(frozen=True, slots=True)
class RpcExpr:
    sector: Ident
    fnName: Ident
    args: list[Expr]
    span: Span


@dataclass(frozen=True, slots=True)
class CallSectorExpr:
    sector: Ident
    fnName: Ident
    args: list[Expr]
    span: Span


@dataclass(frozen=True, slots=True)
class ProceedExpr:
    args: list[Expr]
    span: Span


@dataclass(frozen=True, slots=True)
class TrySuffixExpr:
    inner: Expr
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
