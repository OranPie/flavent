下面给你 **flavent 的 AST（方案 A）输出**：按“能直接写 parser/编译器”的方式定义 **节点类型、字段、约束**。我用一种中立的 **Typed AST schema**（接近 TypeScript/JSON Schema 风格），你可以很容易映射到 Rust/Go/Java。

---

# 0) 通用基础节点

```ts
type Span = { file: string; start: number; end: number; line: number; col: number }

type Ident = { kind: "Ident"; name: string; span: Span }

type QualifiedName = {
  kind: "QualifiedName"
  parts: Ident[]        // e.g. ["Event","HttpRequest"]
  span: Span
}

type Literal =
  | { kind: "LitInt"; value: string; span: Span }      // keep string for big-int
  | { kind: "LitFloat"; value: string; span: Span }
  | { kind: "LitStr"; value: string; span: Span }
  | { kind: "LitBytes"; value: string; span: Span }    // raw/escaped
  | { kind: "LitBool"; value: boolean; span: Span }
  | { kind: "LitNull"; span: Span }                    // optional (if you want)
```

---

# 1) Program / Top-level

```ts
type Program = {
  kind: "Program"
  items: TopItem[]
  run?: RunStmt
  span: Span
}

type RunStmt = { kind: "RunStmt"; span: Span }
```

```ts
type TopItem =
  | TypeDecl
  | ConstDecl
  | LetDecl
  | NeedDecl
  | FnDecl
  | MixinDecl
  | UseMixinStmt
  | ResolveMixinStmt
  | SectorDecl
  | OnHandler
```

---

# 2) Types AST

## 2.1 Type Declarations

```ts
type TypeDecl = {
  kind: "TypeDecl"
  name: QualifiedName
  rhs: TypeRhs
  span: Span
}

type TypeRhs =
  | { kind: "TypeAlias"; target: TypeRef; span: Span }
  | { kind: "RecordType"; fields: FieldDecl[]; span: Span }
  | { kind: "SumType"; variants: VariantDecl[]; span: Span }

type FieldDecl = {
  kind: "FieldDecl"
  name: Ident
  ty: TypeRef
  span: Span
}

type VariantDecl = {
  kind: "VariantDecl"
  name: Ident
  payload?: TypeRef[]      // Variant(T1, T2, ...)
  span: Span
}
```

## 2.2 Type References

```ts
type TypeRef =
  | { kind: "TypeName"; name: QualifiedName; args?: TypeRef[]; span: Span } // Result[T,E]
  | { kind: "TypeParen"; inner: TypeRef; span: Span }
```

> 约束：解析期只构造；语义期（typecheck）再解析内建类型（Result/Option/List/Map/Chan/Stream 等）。

---

# 3) Declarations AST（const/let/need）

```ts
type ConstDecl = {
  kind: "ConstDecl"
  name: Ident
  value: Expr
  span: Span
}

type LetDecl = {
  kind: "LetDecl"
  name: Ident
  value: Expr        // later checked to be PureExpr at top-level if top-level let
  span: Span
}

type NeedDecl = {
  kind: "NeedDecl"
  name: Ident
  attrs?: NeedAttr
  value: Expr
  span: Span
}

type NeedAttr = {
  kind: "NeedAttr"
  cache?: string      // e.g. "ttl:5m", "none"
  cacheFail?: "yes" | "no"
  span: Span
}
```

---

# 4) Functions AST

```ts
type FnDecl = {
  kind: "FnDecl"
  name: Ident
  sectorQual?: Ident          // fn@fs => "fs" ; absent => pure
  params: ParamDecl[]
  retType?: TypeRef
  body: FnBody
  span: Span
}

type ParamDecl = { kind: "ParamDecl"; name: Ident; ty: TypeRef; span: Span }

type FnBody =
  | { kind: "BodyExpr"; expr: Expr; span: Span }
  | { kind: "BodyDo"; block: Block; span: Span }
```

---

# 5) Sector AST

```ts
type SectorDecl = {
  kind: "SectorDecl"
  name: Ident
  supervisor?: SupervisorSpec      // optional (from semantics B2)
  items: SectorItem[]
  span: Span
}

type SectorItem = LetDecl | FnDecl | OnHandler
```

Supervisor（可选但你前面要了语义 B2）：

```ts
type SupervisorSpec = {
  kind: "SupervisorSpec"
  strategy?: "restart" | "stop" | "escalate"
  maxRestarts?: { count: number; windowMs: number }  // "3 in 10s" normalized
  mailbox?: "drop" | "replay"
  needCache?: "clear" | "keep"
  onError?: "log" | "log+metrics" | "emit"
  span: Span
}
```

---

# 6) Event Handlers AST

```ts
type OnHandler = {
  kind: "OnHandler"
  event: EventPattern
  binder?: Ident              // "as req"
  when?: Expr                 // optional guard
  body: HandlerBody
  span: Span
}

type EventPattern =
  | { kind: "EventType"; name: QualifiedName; span: Span }
  | { kind: "EventCall"; name: QualifiedName; args: Expr[]; span: Span } // Event.Timer(1s)

type HandlerBody =
  | { kind: "HandlerExpr"; expr: Expr; span: Span }
  | { kind: "HandlerDo"; block: Block; span: Span }
```

> MVP 约束（语义期）：handler 返回类型固定 `Unit`；`?` 失败走 `Event.Error`。

---

# 7) Mixin AST（add + around + resolve）

```ts
type MixinDecl = {
  kind: "MixinDecl"
  name: QualifiedName
  version: number                // vN
  target: MixinTarget
  items: MixinItem[]
  span: Span
}

type MixinTarget =
  | { kind: "TargetType"; name: QualifiedName; span: Span }
  | { kind: "TargetSector"; name: Ident; span: Span }

type MixinItem = MixinFnAdd | MixinAround

type MixinFnAdd = {
  kind: "MixinFnAdd"
  sig: FnSignature               // add fn f(...)
  body: FnBody
  span: Span
}

type MixinAround = {
  kind: "MixinAround"
  sig: FnSignature               // around fn f(...)
  block: Block                   // must contain exactly one Proceed(...) in MVP
  span: Span
}

type FnSignature = {
  kind: "FnSignature"
  name: Ident
  params: ParamDecl[]
  retType?: TypeRef
  span: Span
}

type UseMixinStmt = {
  kind: "UseMixinStmt"
  name: QualifiedName
  version: number
  span: Span
}

type ResolveMixinStmt = {
  kind: "ResolveMixinStmt"
  rules: PreferRule[]
  span: Span
}

type PreferRule = {
  kind: "PreferRule"
  prefer: { name: QualifiedName; version: number }
  over:   { name: QualifiedName; version: number }
  span: Span
}
```

---

# 8) Statements / Blocks AST（do/if/for/emit/return/assign）

```ts
type Block = { kind: "Block"; stmts: Stmt[]; span: Span }

type Stmt =
  | LetStmt
  | AssignStmt
  | EmitStmt
  | ReturnStmt
  | IfStmt
  | ForStmt
  | ExprStmt
  | StopStmt
  | YieldStmt      // from fairness spec C1 (optional but recommended)
```

```ts
type LetStmt = { kind: "LetStmt"; name: Ident; value: Expr; span: Span }

type AssignStmt = {
  kind: "AssignStmt"
  target: LValue
  op: "=" | "+=" | "-=" | "*=" | "/="
  value: Expr
  span: Span
}

type LValue =
  | { kind: "LVar"; name: Ident; span: Span }
  | { kind: "LMember"; object: Expr; field: Ident; span: Span }
  | { kind: "LIndex"; object: Expr; index: Expr; span: Span }

type EmitStmt = { kind: "EmitStmt"; expr: Expr; span: Span }
type ReturnStmt = { kind: "ReturnStmt"; expr: Expr; span: Span }
type ExprStmt = { kind: "ExprStmt"; expr: Expr; span: Span }
type StopStmt = { kind: "StopStmt"; span: Span }
type YieldStmt = { kind: "YieldStmt"; span: Span }
```

```ts
type IfStmt = {
  kind: "IfStmt"
  cond: Expr
  thenBlock: Block
  elseBlock?: Block
  span: Span
}

type ForStmt = {
  kind: "ForStmt"
  binder: Ident
  iterable: Expr
  body: Block
  span: Span
}
```

---

# 9) Expressions AST（含 `?`, `match`, `await`, `rpc/call`, `proceed`）

## 9.1 表达式总类型

```ts
type Expr =
  | LitExpr
  | VarExpr
  | RecordLitExpr
  | TupleLitExpr
  | CallExpr
  | MemberExpr
  | IndexExpr
  | UnaryExpr
  | BinaryExpr
  | PipeExpr
  | MatchExpr
  | DoExpr            // optional: if you want do as expression; MVP can keep only in FnBody/HandlerBody
  | AwaitExpr
  | RpcExpr
  | CallSectorExpr
  | ProceedExpr       // only valid inside MixinAround
  | TrySuffixExpr
```

### 9.2 基本表达式

```ts
type LitExpr = { kind: "LitExpr"; lit: Literal; span: Span }
type VarExpr = { kind: "VarExpr"; name: Ident; span: Span }

type RecordLitExpr = {
  kind: "RecordLitExpr"
  items: { key: Ident; value: Expr; span: Span }[]
  span: Span
}

type TupleLitExpr = { kind: "TupleLitExpr"; items: Expr[]; span: Span }

type CallExpr = { kind: "CallExpr"; callee: Expr; args: Expr[]; span: Span }
type MemberExpr = { kind: "MemberExpr"; object: Expr; field: Ident; span: Span }
type IndexExpr = { kind: "IndexExpr"; object: Expr; index: Expr; span: Span }
```

### 9.3 运算/管道/一元

```ts
type UnaryExpr = { kind: "UnaryExpr"; op: "-" | "not"; expr: Expr; span: Span }

type BinaryExpr = {
  kind: "BinaryExpr"
  op: "and" | "or" | "==" | "!=" | "<" | "<=" | ">" | ">=" | "+" | "-" | "*" | "/"
  left: Expr
  right: Expr
  span: Span
}

// a |> f |> g  可建成链或二叉；建议链方便后续 desugar
type PipeExpr = { kind: "PipeExpr"; head: Expr; stages: Expr[]; span: Span }
```

### 9.4 match

```ts
type MatchExpr = {
  kind: "MatchExpr"
  scrutinee: Expr
  arms: MatchArm[]
  span: Span
}

type MatchArm = { kind: "MatchArm"; pat: Pattern; body: Expr; span: Span }

type Pattern =
  | { kind: "PWildcard"; span: Span }
  | { kind: "PVar"; name: Ident; span: Span }
  | { kind: "PConstructor"; name: QualifiedName; args?: Pattern[]; span: Span }
```

### 9.5 await / rpc / call

```ts
type AwaitExpr = { kind: "AwaitExpr"; eventType: QualifiedName; span: Span }

// rpc db.readUser(id)
type RpcExpr = {
  kind: "RpcExpr"
  sector: Ident
  fnName: Ident
  args: Expr[]
  span: Span
}

// call db.readUser(id)  (if you want call as expr Unit) or keep as Stmt
type CallSectorExpr = {
  kind: "CallSectorExpr"
  sector: Ident
  fnName: Ident
  args: Expr[]
  span: Span
}
```

### 9.6 proceed（仅 mixin around 内合法）

```ts
type ProceedExpr = {
  kind: "ProceedExpr"
  args: Expr[]
  span: Span
}
```

### 9.7 `?` try-suffix

```ts
type TrySuffixExpr = { kind: "TrySuffixExpr"; inner: Expr; span: Span }
```

---

# 10) 语义期（type/effect）建议放哪：Typed AST / HIR

实现时通常分两层：

## 10.1 Parsed AST（上面给的）

* 只保证语法结构
* 不做类型/效果推导

## 10.2 Typed AST / HIR（语义后）

给每个表达式挂上：

```ts
type Effect = { kind: "pure" } | { kind: "sector"; name: string } | { kind: "event" }

type TypedExpr = Expr & {
  type: TypeRefResolved        // 解析到符号表的类型（或 TypeId）
  effect: Effect
}
```

并额外生成两类“已降糖”节点（推荐）：

* `PipeExpr` desugar 成一系列 `CallExpr`
* `TrySuffixExpr` desugar 成显式 early-exit（在函数里变 return Err / 在 handler 里变 emit Error + abort）

---

# 11) 关键约束（AST 层可做 quick checks）

* `ProceedExpr` 只能出现在 `MixinAround.block` 内
* `RunStmt` 全程序最多一个
* `Top-level LetDecl` RHS 必须 `pure`（语义期检查）
* `FnDecl` 未标注 sector 的必须推导 `pure`
* `OnHandler` 在顶层时属于默认 `sector main`（在 HIR 里可把它搬到一个合成 sector）

---

如果你要我再进一步，我可以直接给你：

1. **AST → HIR 的 desugar 清单**（每个语法糖如何展开）
2. **符号表/作用域模型**（type/sector/mixin 的 name resolution）
3. **mixin weaving 的 IR 结构**（把 around 链变成一个确定的 call graph）
