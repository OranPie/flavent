下面继续补齐你要的两块：**(1) 缩进词法/INDENT-DEDENT 精确定义**，以及 **(2) effect/type 规则**（包含：sector 归属、`call/rpc`、`emit/await`、`?` 传播、以及标准库 effect 标注方式）。我会保持“严格、可实现”的口径。

---

# 1) 缩进语法的精确定义（INDENT/DEDENT）

flavent 采用“类似 Python”的缩进块，但要更严格：**只允许出现在明确引入块的地方**（如 `do:`、`sector:`、`match:`、`if:`、`for:`、`mixin:` 等）。解析器不需要“猜测块”，只要看到 `:` + 换行即可进入缩进模式。

## 1.1 行与换行（Logical Line）

* 源码由 **物理行** 组成（以 `\n` 结束；文件末尾可无 `\n`，视为隐式 `\n`）。
* 经过词法处理后产生 **逻辑行**（Logical Line）：

  * 在括号/中括号/大括号内：换行不产生 `NL`（即“隐式续行”）。
  * 否则：物理换行产生 `NL` token。

> 括号集合：`(` `)` `[` `]` `{` `}`
> 在这些括号未闭合时，忽略换行与缩进变化。

## 1.2 注释与空行

* `//` 单行注释在词法阶段移除（直到行末）。
* `/* ... */` 块注释移除；若实现支持嵌套，按栈匹配。
* **空行**（去掉空白与注释后为空）：

  * 不产生 `NL`
  * 不影响缩进栈

## 1.3 缩进单位与 Tab

为避免歧义，规则必须硬性：

* 缩进只允许空格（space）。**Tab 直接词法错误**。
* 缩进级别以“空格数”计。
* 可选：约束每级缩进必须是 2 或 4 的倍数（lint/编译选项，不属于语法必需）。

## 1.4 INDENT/DEDENT 产生算法（严格）

维护一个缩进栈 `S`，初始化为 `[0]`（表示顶层缩进 0）。

逐行处理每个**会产生 NL 的逻辑行**（即不在括号内、非空行）：

设该逻辑行行首空格数为 `k`。

1. 若上一逻辑行以 `:` 结尾（且该 `:` 不在括号内），则该行必须是块内容行：

   * 要求 `k > top(S)`，否则 **IndentationError: expected indent**
   * 产生 `INDENT`，并 `push k` 进栈

2. 若上一逻辑行不以 `:` 结尾：

   * 若 `k == top(S)`：不产生缩进 token
   * 若 `k > top(S)`：**IndentationError: unexpected indent**
     （因为只有 `:` 能引入块）
   * 若 `k < top(S)`：循环弹栈并产生 `DEDENT` 直到满足：

     * `k == top(S)`：结束
     * 若栈弹空或最终 `k` 不等于任何栈元素：**IndentationError: unaligned dedent**

3. 每个逻辑行末尾产生 `NL` token（用于分隔语句），但：

   * 若该行在括号内（隐式续行）则不产生
   * 空行不产生

4. 文件结束时：

   * 生成一个 `NL`（若最后一行不是空且未产生 NL）
   * 产生若干 `DEDENT`，直到栈回到 `[0]`

## 1.5 “块”的语法触发点（唯一触发）

下列语法结构必须以 `":" NL INDENT ... DEDENT` 形式出现（冒号+换行+缩进）：

* `sector X:`
* `do:`
* `match e:`
* `if cond:`
* `else:`
* `for x in it:`
* `mixin ... into ...:`
* `around fn ...:`
* `resolve mixin-conflict:`

> 这保证了：**不会出现“凭缩进判断块”的不确定性**，只认冒号。

## 1.6 可选替代：显式花括号块（等价模式）

如果你想让实现更简单、或更适合自动格式化，可定义一个“等价语法模式”：

* 允许 `X: { ... }` 替代 `X:\n  ...`
* 花括号块内 `;` 或 `NL` 均可分隔语句
* 这属于语法扩展，不影响核心定义

---

# 2) effect/type 规则（严格、可静态检查）

flavent 的核心是：**副作用只能发生在 sector**，并且跨 sector 必须显式 `call/rpc`。这需要一个“effect 系统”，最小实现只要做到：能标注/推导“纯/有副作用/属于哪个 sector”。

下面给出 MVP 的严格规则。

---

## 2.1 Effect 集合与函数签名扩展

定义 effect（效果）为枚举（最小集）：

* `pure`：无副作用、可在任意位置执行
* `@S`：属于某个 sector `S` 的 effect（表示可能读写该 sector 状态/调用该 sector 的 I/O 能力）
* `event`：与事件系统交互（`emit/await`），也必须在 sector 内

> 实现上可以把 `event` 看成 `@S` 的子集：所有事件操作都在某个 sector 的运行时里发生。

### 函数的 effect 注解形式

建议把 effect 放在函数名后或返回类型前，MVP 语法你可以选一种固定格式：

**方案 A（最简）**：沿用 `fn@sector` 语法

* `fn foo(...) -> T = ...` 默认 `pure`
* `fn@web foo(...) -> T = ...` effect 为 `@web`

**方案 B（更显式）**：增加 `!effect`（可选扩展）

* `fn foo(...) -> T !pure = ...`
* `fn foo(...) -> T !@web = ...`

下面以方案 A 作为“严格定义”。

---

## 2.2 表达式/语句的 effect 规则（推导）

### 2.2.1 基本规则

* 字面量、纯算术、结构构造、纯函数调用：`pure`
* `let x = expr` 的 effect 等于 `expr` 的 effect
* `if/for/match/do` 的 effect 是其所有分支/语句 effect 的 **join**（取“最强”）
* `emit/await/call/rpc` 都是 **非 pure**，必须在 sector 内

### 2.2.2 join（效果合并）规则

定义偏序：

* `pure` < `@S`（任意 sector）
* 不同 `@S1` 与 `@S2` 不可合并（除非你引入 `@any` 或 `@multi`，MVP 直接视为冲突）

**join(a,b)**：

* 若 a==b 返回 a
* 若一方为 pure，返回另一方
* 若 a=@S1 且 b=@S2 且 S1≠S2：**EffectError: mixed sectors in one expression**

> 这条非常关键：它强制你把跨 sector 的东西拆到 `rpc/call`，保证隔离。

---

## 2.3 哪些地方允许什么 effect

### 2.3.1 顶层（Top-level）

* 允许：`pure`
* 不允许：任何 `@S`、`event`
  也就是说顶层 `const/let` 要求 RHS 是 `pure`。

例外：

* `need` 可以允许 `@S` 或 I/O（因为它的执行发生在 runtime；但仍要受“首次使用发生在哪个 sector”的约束，见 2.5）。

### 2.3.2 sector 内

* 允许：`@thatSector`、`pure`、`event`
* 不允许：直接执行 `@otherSector` 的函数（必须 `rpc/call`）

### 2.3.3 `fn` 体内

* `fn`（未标注）必须是 `pure`，其函数体推导 effect 若非 `pure` → 编译错误
* `fn@S` 必须推导为 `@S` 或 `pure`（纯也可），若出现 `@T` 且 T≠S → 编译错误

---

## 2.4 跨 sector 调用：call / rpc 的静态类型

### 2.4.1 规则

* 设 `f` 是 `fn@db readUser(id:Uuid)->Result[User,Err]`
* 在 `sector web` 里：

  * 不能直接 `readUser(id)`（因为它属于 `@db`）
  * 必须 `rpc db.readUser(id)` 或 `call db.readUser(id)`

### 2.4.2 类型定义

* `rpc S.f(args...) : T`，其中 `f: (A...)->T`，`rpc` 表达式本身的 effect 是 `@currentSector`（因为等待发生在当前 sector 的事件循环里），但它会触发跨 sector 消息
* `call S.f(args...) : Unit`（fire-and-forget），effect 同上

> 你也可以让 `rpc` 返回 `Future[T]` 再 `await`，但 MVP 可以直接让 `rpc` 阻塞在事件循环意义上的“挂起等待”。

---

## 2.5 事件系统的严格类型：emit / await

### 2.5.1 事件类型约束

约定事件类型是某个 `type Event.X = ...`（命名空间约定，不是硬语法），事件模式必须是一个类型名。

* `emit e`：要求 `e` 的静态类型是某个事件类型 `E`
  `emit` 是语句（或表达式返回 `Unit`），effect 为 `event`（因此只能在 sector）

* `await E`：表达式，返回 `E` 类型的值
  只能在 sector（effect = `event`）

### 2.5.2 handler 约束

`on E as x -> body`

* `x` 的类型推导为 `E`
* `body` 的 effect 必须是当前 handler 所在 sector 的 `@S`（或 `pure`），并允许 `event`

---

## 2.6 `?`（TrySuffix）的严格传播语义（Result/Option）

`expr?` 只允许用于两类类型：

1. `Result[T,E]`
2. `Option[T]`

并且只允许出现在以下上下文：

* 函数体（`fn` 或 `fn@S`）内
* handler body 内
* do-block 内

### 2.6.1 对 Result 的规则

若 `expr : Result[T,E]`：

* `expr? : T`
* 若 `expr` 为 `Err(e)`，则立即从“当前可传播边界”返回 `Err(e)`

传播边界定义：

* 在 `fn ... -> Result[U,E]` 内，`?` 直接 `return Err(e)`
* 在 `fn ... -> U`（非 Result 返回）内使用 `?` → **TypeError: try on non-Result-returning function**
* 在 handler 中，等价于：触发一个 runtime error event 或中止该 handler（MVP 建议：handler 必须返回 `Unit`，`?` 遇错就 `stop current handler` 并把错误交给默认错误处理器）

### 2.6.2 对 Option 的规则

若 `expr : Option[T]`：

* `expr? : T`
* 若为 `None`，立即从传播边界返回 `None`（要求当前函数返回 `Option[...]`），否则类型错误。

---

## 2.7 标准库如何声明 effect（建议的“可检查接口”）

为了让编译器能静态检查，标准库函数需要带 effect 信息。MVP 可以用“模块即 sector”的约定：

* `fs.*` 默认是 `@fs`
* `net.*` 默认是 `@net`
* `io.*` 默认是 `@main`（或专门 `@io`）
* `time.*` 如果读时钟算副作用：归到 `@main` 或 `@time`
* `json.*`、`math.*`、`regex.*` 默认 `pure`

形式上可以在库的“签名文件”写成：

```
fn@fs fs.readText(path: Str) -> Str
fn@fs fs.exists(path: Str) -> Bool
fn@net http.get(url: Str) -> HttpResponse
fn     json.parse(s: Str) -> Result[Json, Err]
fn     min(a:Int,b:Int,c:Int) -> Int
```

---

# 3) 最终“严格版”补丁：EBNF 增补点

你上一版 EBNF 里提到 `INDENT/DEDENT` 但没定义产生规则，现在已经给了词法算法。若要写进语法文件，一般写成：

```
Block := ":" NL INDENT { Stmt } DEDENT ;
```

并在词法规范中引用 1.4 的算法。

同时建议把 `await` 加入 PrimaryExpr（如果你要 `await Event.X` 是表达式）：

```
PrimaryExpr := ... | AwaitExpr ;
AwaitExpr   := "await" TypeName ;
```

以及把 `call/rpc` 作为表达式/语句（取决于你想让它们返回值与否）：

* `rpc` 是表达式：放进 `PrimaryExpr`
* `call` 是语句：放进 `Stmt`

---

# 4) 一个“严格合法且触发所有规则”的最小例子

```flavent
type Event.Start = {}
type Err = { msg: Str }
type Result[T,E] = Ok(T) | Err(E)

fn parseInt(s: Str) -> Result[Int, Err] = do:
  if s.len() == 0: Err({msg="empty"})
  else: Ok(s.toInt())

sector fs:
  fn@fs readN() -> Result[Int, Err] = do:
    let t = fs.readText("n.txt")
    parseInt(t.trim())

sector main:
  on Event.Start ->
    let n = rpc fs.readN()?       // 只能 rpc，不能直接调用 @fs
    io.writeText(n.toStr() + "\n")
    stop()

run()
```

---

如果你下一步想继续“从严格定义走到可实现”，最自然的下一章就是：

* **把 `event` 也纳入 effect join**（比如允许 `@S + event` 的合并形式），以及
* **定义 handler 错误传播策略**（`?` 在 handler 中遇 Err 到底是 swallow、发 ErrorEvent、还是终止 sector）。

我也可以直接给你这两条的严格规范版本。
