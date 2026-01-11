下面给出 **flavent** 的最终总结：**严格语法定义（EBNF 风格）+ 程序结构规范 + 核心语义约束**。我把它写成“可做 parser/编译器的最小完整版本”（MVP），并明确哪些是关键字、哪些是表达式、哪些是顶层条目。

---

# 1) 程序结构总览

一个 `.flv` 文件由**一串顶层条目**组成（扁平化），顶层条目之间可任意顺序（建议：type → mixin → const/need → fn → sector → on → run）。

**顶层条目种类**：

* `type` 类型定义
* `const` 常量
* `let` 顶层不可变绑定（仅允许纯表达式；若要副作用需放 sector）
* `need` 按需绑定（允许副作用，但首次使用时发生；建议只做加载/解析）
* `fn` 函数定义（可标注 `@sector`）
* `mixin` 混入定义
* `use mixin` 启用混入（可选）
* `resolve mixin-conflict` 冲突解决（可选）
* `sector` 分区定义（内部可有 `let` 状态、`fn`、`on`）
* 顶层 `on` 事件处理器（隐式属于默认 sector：`main`）
* `run()` 程序启动语句（可出现 0 或 1 次；无则默认生成）

---

# 2) 词法（Lexical）

### 2.1 空白与注释

* 空白：空格、制表、换行均可分隔 token
* 单行注释：`// ...` 到行末
* 块注释：`/* ... */` 可嵌套（推荐实现支持嵌套）

### 2.2 标识符

* `Identifier := (Letter | "_") { Letter | Digit | "_" }`
* 关键字不可用作 Identifier（见 2.4）

### 2.3 字面量

* `IntLiteral := Digit {Digit}`
* `FloatLiteral := Digit {Digit} "." Digit {Digit}`
* `StrLiteral := '"' { (any char except " or \n) | Escape } '"'`
* `BytesLiteral := 'b"' ... '"'`（语义：UTF-8 字节序列或转义）
* `BoolLiteral := "true" | "false"`

### 2.4 关键字（Reserved Words）

```
type const let need fn mixin use resolve prefer over into sector on when
do match if else for in return
emit await call rpc proceed
Ok Err Some None
run stop
```

---

# 3) 严格语法定义（EBNF）

> 约定：
>
> * `? ... ?` 表示注释说明
> * `{ X }` 0 次或多次
> * `[ X ]` 0 次或 1 次
> * `|` 选择
> * `NL` 表示换行（用于区分缩进块）；实现可采用“显式 `{}`”替代缩进块，但此处用缩进块定义

---

## 3.1 Compilation Unit

```
Program         := { TopItem } [ RunStmt ] ;

RunStmt         := "run" "(" ")" ;
```

---

## 3.2 Top-level Items

```
TopItem         := TypeDecl
                 | ConstDecl
                 | LetDecl
                 | NeedDecl
                 | FnDecl
                 | MixinDecl
                 | UseMixinStmt
                 | ResolveMixinStmt
                 | SectorDecl
                 | OnHandler ;
```

---

## 3.3 Type System

### 3.3.1 Type Declaration (ADT / Record / Alias)

```
TypeDecl        := "type" TypeName "=" TypeRhs ;

TypeName        := Identifier { "." Identifier } ;         ? 支持命名空间，如 Event.HttpRequest ?
TypeParamList   := "[" Type { "," Type } "]" ;

TypeRhs         := RecordType
                 | SumType
                 | Type ;                                  ? 作为 alias ?

RecordType      := "{" [ Field { "," Field } ] "}" ;
Field           := Identifier ":" Type ;

SumType         := Variant { "|" Variant } ;
Variant         := Identifier [ "(" [ Type { "," Type } ] ")" ] ;
```

### 3.3.2 Types

```
Type            := PrimaryType [ TypeParamList ] ;

PrimaryType     := TypeName
                 | "(" Type ")" ;
```

> 内建泛型类型示例：`Result[T,E]`, `Option[T]`, `List[T]`, `Map[K,V]`, `Chan[T]`, `Stream[T]`

---

## 3.4 Declarations

### 3.4.1 const / let / need

```
ConstDecl       := "const" Identifier "=" Expr ;
LetDecl         := "let"   Identifier "=" PureExpr ;
NeedDecl        := "need"  [ NeedAttr ] Identifier "=" Expr ;

NeedAttr        := "(" "cache" "=" StrLiteral ")" ;         ? e.g. need(cache="ttl:5m") token = ... ?

PureExpr        := Expr ;                                   ? 语义上要求无副作用，由编译器检查 ?
```

---

## 3.5 Functions

### 3.5.1 Function Declaration

```
FnDecl          := "fn" [ SectorQual ] Identifier "(" [ ParamList ] ")" [ "->" Type ] "=" FnBody ;

SectorQual      := "@" Identifier ;                         ? fn@fs readText(...) 绑定 sector ?

ParamList       := Param { "," Param } ;
Param           := Identifier ":" Type ;

FnBody          := Expr
                 | DoBlock ;
```

### 3.5.2 do-block (扁平块)

```
DoBlock         := "do" ":" NL INDENT { Stmt } DEDENT ;
```

---

## 3.6 Sectors

```
SectorDecl      := "sector" Identifier ":" NL INDENT { SectorItem } DEDENT ;

SectorItem      := LetDecl
                 | FnDecl
                 | OnHandler ;
```

> sector 内的 `let` 允许可变（配合赋值语句），但仅在本 sector 内可见/可变。

---

## 3.7 Event Handlers

```
OnHandler       := "on" EventPattern [ "as" Identifier ] [ WhenClause ] "->" HandlerBody ;

EventPattern    := TypeName
                 | TypeName "(" [ ArgList ] ")" ;           ? 如 Event.Timer(1s) ?

WhenClause      := "when" Expr ;

HandlerBody     := Expr
                 | DoBlock ;
```

---

## 3.8 Mixins

### 3.8.1 mixin declaration

```
MixinDecl       := "mixin" MixinName MixinVersion "into" MixinTarget ":" NL INDENT { MixinItem } DEDENT ;

MixinName       := Identifier { "." Identifier } ;
MixinVersion    := "v" IntLiteral ;

MixinTarget     := TypeName
                 | "sector" Identifier ;

MixinItem       := MixinFnAdd
                 | MixinAround ;

MixinFnAdd      := "fn" Identifier "(" [ ParamList ] ")" [ "->" Type ] "=" FnBody ;

MixinAround     := "around" "fn" Identifier "(" [ ParamList ] ")" [ "->" Type ] ":" NL INDENT { Stmt } DEDENT ;
```

### 3.8.2 enable / conflict resolution

```
UseMixinStmt    := "use" "mixin" MixinName "v" IntLiteral ;

ResolveMixinStmt:= "resolve" "mixin-conflict" ":" NL INDENT { PreferRule } DEDENT ;
PreferRule      := "prefer" MixinName "v" IntLiteral "over" MixinName "v" IntLiteral ;
```

---

## 3.9 Statements (用于 do-block / around-block)

```
Stmt            := LetStmt
                 | AssignStmt
                 | EmitStmt
                 | ReturnStmt
                 | IfStmt
                 | ForStmt
                 | ExprStmt ;

LetStmt         := "let" Identifier "=" Expr ;
AssignStmt      := LValue AssignOp Expr ;
AssignOp        := "=" | "+=" | "-=" | "*=" | "/=" ;

LValue          := Identifier | MemberAccess | IndexAccess ;

EmitStmt        := "emit" Expr ;
ReturnStmt      := "return" Expr ;

IfStmt          := "if" Expr ":" NL INDENT { Stmt } DEDENT
                   [ "else" ":" NL INDENT { Stmt } DEDENT ] ;

ForStmt         := "for" Identifier "in" Expr ":" NL INDENT { Stmt } DEDENT ;

ExprStmt        := Expr ;
```

---

## 3.10 Expressions

### 3.10.1 优先级（从低到高）

1. `|>` 管道
2. 逻辑：`or` `and`
3. 比较：`== != < <= > >=`
4. 加减：`+ -`
5. 乘除：`* /`
6. 一元：`- not`
7. 调用/成员/索引/后缀：`f(x) x.y x[i] x?`

### 3.10.2 EBNF

```
Expr            := PipeExpr ;

PipeExpr        := LogicExpr { "|>" LogicExpr } ;

LogicExpr       := CmpExpr { ("and" | "or") CmpExpr } ;
CmpExpr         := AddExpr { ( "==" | "!=" | "<" | "<=" | ">" | ">=" ) AddExpr } ;
AddExpr         := MulExpr { ( "+" | "-" ) MulExpr } ;
MulExpr         := UnaryExpr { ( "*" | "/" ) UnaryExpr } ;

UnaryExpr       := [ "-" | "not" ] PostfixExpr ;

PostfixExpr     := PrimaryExpr { PostfixOp } ;
PostfixOp       := Call
                 | Member
                 | Index
                 | TrySuffix ;

Call            := "(" [ ArgList ] ")" ;
ArgList         := Expr { "," Expr } ;

Member          := "." Identifier ;
Index           := "[" Expr "]" ;

TrySuffix       := "?" ;                                    ? Result/Option 的语法糖：失败则返回/传播 ?

PrimaryExpr     := Literal
                 | Identifier
                 | RecordLit
                 | TupleLit
                 | MatchExpr
                 | "(" Expr ")" ;

RecordLit       := "{" [ RecordItem { "," RecordItem } ] "}" ;
RecordItem      := Identifier "=" Expr ;

TupleLit        := "(" Expr "," Expr { "," Expr } ")" ;
```

### 3.10.3 match 表达式

```
MatchExpr       := "match" Expr ":" NL INDENT { MatchArm } DEDENT ;
MatchArm        := Pattern "->" Expr NL ;

Pattern         := Identifier
                 | Identifier "(" [ Pattern { "," Pattern } ] ")"
                 | "_" ;
```

---

# 4) 结构与语义约束（“严格结构”）

## 4.1 扁平化约束（Flatness)

* 顶层不允许出现任意块语句，只有 TopItem。
* 可嵌套块仅允许：

  * `do:`（函数体）
  * handler 的 `do:`
  * `if/for` 的块
  * mixin `around` 的块
* 推荐实现 **lint**：最大缩进深度默认 1（可配置），超过则警告/报错。

## 4.2 sector 规则（隔离与副作用）

* **副作用 API**（fs/net/ui/time/sleep 等）必须在某个 `sector` 内调用；纯函数区不允许直接调用（编译器检查 effect）。
* 标注 `fn@X` 的函数只能在 sector `X` 内直接调用；跨 sector 必须使用：

  * `call X.fn(args...)`：异步 fire-and-forget
  * `rpc X.fn(args...)`：请求-响应，返回值可用 `?`

## 4.3 need 规则（按需 + 缓存）

* `need x = expr` 在第一次读取 `x` 时求值并缓存（并发读取保证只算一次）。
* `need(cache="ttl:...")` 支持 TTL；过期后下次读取重新计算。
* `force x`（可选语法扩展）强制触发求值。

## 4.4 mixin 规则（可追踪与冲突）

* mixin 必须携带版本：`mixin Name vN ...`
* 同一 target 上同名函数的增强若冲突，必须：

  * 显式 `resolve mixin-conflict` 指定 `prefer ... over ...`
  * 或编译器报错拒绝构建

## 4.5 事件处理规则

* `on EventType ... -> ...` 声明 handler；多个 handler 匹配同事件时：

  * `when` 更具体优先（实现可用静态排序或运行时判定）
  * 同级按声明顺序

---

# 5) 最小“合法程序”的严格结构示例

```flavent
type Event.Start = {}

fn solve(input: Str) -> Str = input

sector main:
  on Event.Start ->
    let input = io.readAllText()
    io.writeText(solve(input) + "\n")
    stop()

run()
```

---

如果你下一步想把这份“严格定义”再推进到 **更接近可编译实现**，我可以直接补齐两块最重要的缺口（仍保持严格）：

1. **缩进语法的精确定义**（INDENT/DEDENT 产生规则），或改成显式 `{}` 的 EBNF。
2. **effect/type 规则**：哪些库函数属于哪个 sector、`?` 的精确传播语义（Result/Option）、以及 `emit/await` 的类型约束。
