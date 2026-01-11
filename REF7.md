下面给你 **1) AST→HIR 降糖清单**、**2) 符号表/作用域模型**、**3) mixin weaving 的 IR 结构与生成步骤**（都按“可以直接实现”的规格写，尽量少废话但覆盖关键边界）。

---

# 1) AST → HIR：降糖与规范化（Desugar Checklist）

## 1.1 HIR 总体目标

HIR（High-level IR）应满足：

* **没有缩进块语法差异**：全部变成显式 `Block { stmts }`
* **没有 `PipeExpr`**：全部变成普通调用链
* **没有 `TrySuffixExpr (?)`**：全部变成显式 early-exit 控制流
* **sector/handler 的隐式归属显式化**
* 所有符号引用都变成 `SymbolId` / `TypeId`（已解析）

---

## 1.2 Program 级别规范化

### (A) 默认 sector 注入

若顶层存在 `OnHandler`，在 HIR 里把它们移动进一个合成/默认 sector：

* 若用户声明了 `sector main:`：顶层 handler 归入该 sector
* 否则 HIR 自动生成：

  * `sector main:` 并把顶层 handlers 放进去

### (B) 隐式 run 注入（可选）

若 AST 没有 `run()`，HIR 可插入默认 `run()`（或交由运行时入口处理）。建议：**HIR 保留显式 RunStmt**，没有就由后端补。

---

## 1.3 表达式降糖

### (1) `PipeExpr` 降糖

AST：`a |> f |> g(x) |> h`
HIR：左结合调用：

* `t1 = f(a)`
* `t2 = g(t1, x)`（规则：stage 若是 `CallExpr(callee=g, args=[x...])` 则把 `t1` 插到 args[0]）
* `t3 = h(t2)`

严格规则（避免歧义）：

* 若 stage 是 `VarExpr` 或 `MemberExpr`：视为一元函数 `stage(t)`
* 若 stage 是 `CallExpr(stageCallee, args...)`：变 `CallExpr(stageCallee, [t] + args)`
* 其他 stage（如二元运算表达式）非法：`PipeStageError`

**HIR 表示**：直接用 `CallExpr` 链，不保留 pipe 节点。

---

### (2) `TrySuffixExpr` (`expr?`) 降糖

`?` 的降糖取决于“传播边界”：

#### 2.3.1 在 `fn ... -> Result[U,E]`

AST：`let x = foo()?`
HIR：

```pseudo
tmp = foo()
match tmp:
  Ok(v)  -> x = v
  Err(e) -> return Err(e)
```

#### 2.3.2 在 `fn ... -> Option[U]`

类似：

```pseudo
tmp = foo()
match tmp:
  Some(v) -> x = v
  None    -> return None
```

#### 2.3.3 在 `handler`（`on ... -> ...`）

根据你之前的 B1 规范：失败生成 `Event.Error` 并中止 handler。

HIR：

```pseudo
tmp = foo()
match tmp:
  Ok(v)  -> x = v
  Err(e) -> {
     emit Event.Error{ sector=S, handler=H, cause=e, event=E_snapshot, time=now() }
     abort_handler
  }
```

> 说明：`abort_handler` 是 HIR 的控制流指令（类似 `return` 但只结束 handler fiber，不结束进程/sector）。

#### 2.3.4 在 `mixin around` 块内

`?` 同 handler 还是同 fn？建议与“被拦截函数”的边界一致：

* 如果 around 拦截的是 `fn -> Result`，就按 Result 传播
* 如果拦截的是 handler-like `Unit`（sector 内普通函数也可能是 Unit），那么你必须规定：

  * 要么禁止在 `Unit` 里用 `?`
  * 要么把失败转为 `Event.Error + early-exit`（推荐一致：**按所在函数签名推导**）

---

### (3) `await EventType` 降糖

AST：`await Event.X`
HIR：变成运行时原语：

* `AwaitEvent(typeId=Event.X)`，返回该事件的值（类型确定）

---

### (4) `rpc S.f(args...)` 降糖

HIR：两种实现路线，选一种写死：

**路线 A（直接挂起等待）**：

* `RpcCall(sector=S, fnSym=f, args=..., await=true)` 返回 `T`

**路线 B（Future + await）**（更通用）：

* `tmp = RpcCall(..., await=false)` 返回 `Future[T]`
* `AwaitFuture(tmp)`

MVP 推荐 A，简单。

---

### (5) `call S.f(...)` 降糖

HIR：`RpcCall(..., await=false)` 且结果类型 `Unit`。

---

## 1.4 语句降糖/规范化

### (A) `for binder in iterable: block`

若 iterable 是可迭代对象：
HIR 可保留 `ForStmt`（由后端展开），或 desugar 成显式 iterator：

```pseudo
it = iterable.iter()
while it.hasNext():
  binder = it.next()
  block
```

MVP：保留 `ForStmt`，后端/解释器实现迭代协议。

### (B) `stop() / yield()`

* `stop()` -> `StopProcess` 或 `StopSector`（你需要明确 stop 作用域；建议：在 handler/sector 中为 `StopSector`，在 main 为 `StopProcess`，或提供两者）
* `yield()` -> `YieldFiber`（把当前 fiber 放回就绪队列尾部）

---

## 1.5 HIR 推荐节点集合（比 AST 少）

**HIRExpr**：`Lit / Var(SymbolId) / Call / Member / Index / Match / AwaitEvent / RpcCall / RecordLit / TupleLit / Unary / Binary`
**HIRStmt**：`Let / Assign / If / For / Emit / Return / AbortHandler / Stop / Yield / ExprStmt`

---

# 2) 符号表与作用域模型（Name Resolution）

## 2.1 符号种类（Symbol Kinds）

建议用一个统一 `SymbolId`，附 `kind`：

* `SymType`：类型名（含泛型参数信息）
* `SymFn`：函数
* `SymSector`：sector
* `SymVar`：变量（let/const/param）
* `SymNeed`：need cell（可视为 var，但带 lazy 属性）
* `SymMixin`：mixin 名称 + version
* `SymHandler`：handler（编译器生成的符号，便于日志/审计）

## 2.2 作用域层级（Scope Stack）

从外到内：

1. **GlobalScope**

   * type / sector / mixin / top-level fn / top-level const/let/need
2. **SectorScope(S)**

   * sector 内的 let/need/fn/handlers
   * 注意：sector 内的 `fn` 与全局 `fn` 不同命名空间还是同？
     建议：同一个函数命名空间（统一查找），但带 `ownerSector` 元数据。
3. **FnScope / HandlerScope**

   * params、局部 let
4. **BlockScope**

   * do/if/for 的局部绑定（可选：MVP 也可以让 let 只在最近 block 生效）

## 2.3 名称解析规则（严格查找顺序）

### 2.3.1 变量/值标识符解析（Expr 中 Ident）

从内到外：

1. 当前 block locals
2. 当前 fn/handler locals + params
3. 所属 sector 的 let/need
4. 全局 const/let/need
5. （可选）预置名（比如 `Ok/Err/Some/None` 构造器）

若命中多个：报 `NameAmbiguityError`（除非同名允许 shadowing；建议允许内层遮蔽外层，但要 lint）。

### 2.3.2 类型名解析（TypeRef 中 QualifiedName）

从 GlobalScope 的 type namespace 查找：

* 允许 `QualifiedName` 作为命名空间（例如 `Event.HttpRequest`）
* 若你实现模块系统，再加 ModuleScope；MVP 可先把 `.` 当作纯名字层级。

### 2.3.3 sector 与 sector-qualified

* `fn@fs`：解析 `fs` 必须存在 `SymSector`，否则错误
* `rpc fs.readX`：解析 `fs` 为 sector，解析 `readX` 为该 sector 的函数（或全局函数但 ownerSector=fs）

## 2.4 两阶段构建（推荐）

**Pass 1：声明收集（Collect Decls）**

* 收集所有顶层 `type/sector/fn/mixin` 的名字 → 建 global symbol table
* 为每个 sector 建立 SectorScope（先收集 sector 内声明的 fn/let/need/handlers 的名字）

**Pass 2：引用解析（Resolve Uses）**

* 解析所有 TypeRef → TypeId
* 解析所有 Expr ident → SymbolId
* 同时建立 HandlerId、FnId 的 owner 关系

这样能处理前向引用（type/fn 在后面也能被用）。

---

# 3) Mixin Weaving：IR 结构与生成步骤（确定调用链）

你要的是：编译后函数体已经被织入（around 链确定），并且能输出审计报告。

## 3.1 Weave 输入

* Base IR：所有 `FnDecl`（包括 sector 内 fn）与其 HIR body
* Mixin 集：`MixinDecl` + `UseMixinStmt` + `ResolveMixinStmt`
* Target：Type 或 Sector

## 3.2 Weave 产物（推荐 IR）

### 3.2.1 CallGraph 层（最关键）

为每个被织入的函数 `f`，生成一个 **WeavedFunction** 记录：

```ts
type WeavedFunction = {
  fnId: FnId
  target: { kind: "Type"|"Sector"; name: string }
  baseImpl: ImplId                 // base body
  aroundChain: AroundImplId[]      // ordered outer->inner
  finalEntry: ImplId               // 织入后入口（可等于 outermost wrapper）
}
```

其中：

* `ImplId` 指向一个可执行实现（base 或 wrapper）
* `AroundImplId` 指向 mixin around 的 wrapper 实现

### 3.2.2 Wrapper 形式（把 around 变成显式函数）

每个 around 生成一个 wrapper 函数 `wrap_Mi_f`：

```ts
type WrapperImpl = {
  implId: ImplId
  origin: { mixin: MixinId; itemSpan: Span }
  wrapsFn: FnId
  params: ParamTypes
  retType: TypeId
  body: HIRBlock
  // body 中的 ProceedExpr 已经被替换成对 nextImpl 的调用
  next: ImplId
}
```

### 3.2.3 Proceed 替换规则

在 mixin around 的 HIR block 里：

* 找到唯一 `ProceedExpr(args...)`
* 替换为 `CallNextImpl(nextImpl, args...)`

> 这样 weaving 后就没有 Proceed 原语了，只有普通调用。

---

## 3.3 Mixin 顺序线性化（你之前的 C2）

给每个 target 构造 `MixinOrder L=[M1..Mk]`：

1. 应用 `resolve prefer A over B` 约束（构建有向图）
2. 图必须无环；否则 `MixinOrderCycleError`
3. 对图做拓扑排序
4. 同优先级 tie-break：

   * 按 `use mixin` 出现顺序
   * 再按 `(name lexical, version desc)` 保证稳定

得到 `L` 后：

* aroundChain = 在 `L` 顺序中筛选出提供 `around f` 的 mixin
* add 解析也用 `L`：取第一个匹配签名者（否则冲突）

---

## 3.4 Weaving 具体步骤（实现流程）

对每个 target（每个 type、每个 sector）分别做：

### Step 0：收集可用 mixin

* 根据 `use mixin` 得到启用集合 `M`
* 若 mixin target 不匹配该 target，忽略

### Step 1：构造线性顺序 `L`

* 用 3.3 得到 `L`

### Step 2：方法/函数表扩展（add）

* 对 target 的方法表（若 type）或函数表（若 sector）：

  * 插入 mixin add 的符号（作为候选实现）
  * 冲突（add-add 同签名）若无 resolve → error
  * base 已有同名同签名：MVP 禁止覆盖 → error（或要求 replace 扩展语法）

> 产物：`MethodSet/FunctionSet`，每个函数拥有“base 实现 + 可选多个 wrappers”。

### Step 3：around wrapper 生成

对每个 join point 函数 `f`：

* A = 按 `L` 顺序筛选 around 实现（outer->inner）
* 令 `next = baseImpl`
* 从内到外生成 wrappers（推荐逆序构建）：

  * for i from m..1:

    * newWrapper = lowerAroundToWrapper(A[i], next)
    * next = newWrapper
* 最终 `finalEntry = next`

把 `WeavedFunction(fnId=f, aroundChain=A, baseImpl, finalEntry)` 记录下来。

### Step 4：替换调用点（可选）

两种策略：

* **间接调用策略**：所有调用 `f` 都指向 `finalEntry`（通过符号表映射）
* **显式重写策略**：遍历 HIR，把对 `f` 的调用改为对 `finalEntry` 的调用

MVP 推荐：符号表层有 `FnId -> ImplId(finalEntry)` 映射，后端统一用 finalEntry。

---

## 3.5 Weave Report（审计输出）

对每个 target、每个 fn：

* `fn name`
* `base: file:line`
* `around: [ (mixinName v, file:line), ... ] outer->inner`
* `finalEntry implId`
* 冲突与 resolve 的结果（prefer 链）

---

## 3.6 与 effect/sector 的交互（必须定）

* around wrapper 的 effect 必须 **不弱于** 被拦截函数的 effect（不能把 `@fs` 拦截后变 `pure`）
* mixin into sector web 的 around 在语义上属于 `@web`
* wrapper 中若调用 `rpc` 等跨 sector 操作，必须符合 effect join（否则编译错误）

---

## 一个“从 AST→HIR→Weave”最小闭环示例（文字版）

* AST 有 `sector web fn handle`
* AST 有 `mixin M.Audit around handle`
* HIR 把 around block 里的 `proceed(req)` 变成 `CallNextImpl(next, req)`
* Weave 生成 `wrap_Audit_handle(next=base_handle)`
* finalEntry 指向 `wrap_Audit_handle`
* 后端调用 handle 实际执行 wrapper→base

---

如果你希望我再往前一步，我可以把这三块补成**可复制粘贴的实现伪代码**：

* `desugar_try_suffix(expr, boundary)`
* `resolve_symbols(program)` 两阶段
* `weave_mixins(target)`（含 topo sort + wrapper lowering）
