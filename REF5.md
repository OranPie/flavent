下面把你要的 **(1) handler 调度公平性/优先级** 和 **(2) mixin around 织入顺序/冲突线性化** 写成**可进规范、无歧义**的严格定义（MVP 级别但可扩展）。

---

# C1) Handler 调度：公平性、优先级、去饥饿（starvation-free）

> 目标：sector 是单线程事件循环（或逻辑单线程），但要对事件队列、handler 执行、优先级与公平性做确定规定，避免“某类事件永远处理不到”。

## 1. Sector mailbox 与事件分类

每个 sector `S` 有一个 mailbox，运行时将事件分为三类队列（MVP 必须有这三类，便于解释优先级与背压）：

1. `sysQ`：系统事件（restart、StreamPull/Push、timers 内部事件等）
2. `rtQ`：运行时事件（`Event.Error`、supervisor 通知等）
3. `appQ`：应用事件（用户 `emit` 的事件）

优先级顺序固定为：`sysQ > rtQ > appQ`

> 解释：流背压、取消、timer 这些是保证系统正确性的“硬事件”，必须更高优先级。

## 2. 事件派发与 handler 选择（deterministic)

一个事件 `E` 到达后，选择 handler 的规则必须是确定的。

### 2.1 Handler 的匹配集合

对事件类型 `E`，找到所有满足的 handler：

* `on E -> ...`
* `on E as x when cond -> ...`，其中 `cond` 在绑定 `x` 后求值

匹配集合记为 `H = [h1, h2, ...]`。

### 2.2 排序规则（固定）

对集合 `H`，按以下 key 排序（从高到低）：

1. `when` 的**静态特异性分数**（SpecificityScore）
2. 源码出现顺序（FileOrder，稳定排序）
3. （可选）显式 `priority=N`（如果你未来加语法）

#### SpecificityScore（MVP 可实现定义）

* 若无 `when`：score = 0
* 有 `when`：

  * 仅由字面量比较、字段相等、`and/or/not` 组成：score = 2
  * 含函数调用或复杂表达式：score = 1
    （因为复杂表达式可能有副作用/不稳定；MVP 鼓励简单 when）

> 实现建议：编译期对 when AST 做模式识别，给出 score。识别不了就当 1。

### 2.3 执行规则

* 对排序后的 `H`，按顺序执行，直到遇到一个 handler **标记为“消费事件”** 或队列耗尽。

为保持 MVP 简单，定义默认行为：

* handler 默认 **consume**（即执行第一个匹配 handler 后停止）
* 若要广播语义，可提供可选关键字 `on ... -> ... (continue)` 或 `on*`（扩展）

**MVP 固定：只执行排序后第一个匹配 handler。**

> 这样语义最简单、最可控，也符合“扁平事件路由”。

## 3. 时间片与公平性（避免长 handler 占死循环）

### 3.1 原子性

一个 handler 的执行在逻辑上是“原子”的：它运行到结束或失败，不会被同 sector 的其他事件抢占。

### 3.2 Cooperative Yield（协作让出）

为了避免单个 handler 计算过久导致饥饿，规范要求提供一个内建点：

* `await`、`rpc`、`stream.forEach` 等**挂起点**会把控制权还给 event loop。
* 额外提供一个显式 `yield()`（标准库/内建）：

```flavent
yield()   // effect: event, only in sector
```

语义：把当前 fiber 挂起到“就绪队列”尾部，让 event loop 处理下一个事件，然后再恢复该 fiber。

### 3.3 强制公平策略（必须写死）

为了保证 starvation-free，规定调度器采用 **两级循环 + 配额**：

* 每轮主循环按队列优先级取事件，但对 `sysQ/rtQ` 也要防止它们无限占用
* 固定配额（可配置但要有默认）：

默认配额：

* 每处理 **最多 50 个 sysQ 事件** 必须尝试处理 1 个 rtQ/appQ（若存在）
* 每处理 **最多 50 个 rtQ 事件** 必须尝试处理 1 个 appQ（若存在）

伪规则（规范式）：

* 事件循环按优先级取，但当某队列连续取满 `quota` 次且低优先级队列非空时，必须切换到低优先级队列取 1 个事件。

> 这条是“系统正确性 vs 应用响应性”的折中：sysQ 仍优先，但不会把 appQ 永久饿死。

## 4. 事件投递顺序（happens-before）

同一 sector 内：

* `emit` 的事件进入目标 sector 的队列时，保持 **FIFO**（对同一发送者、同一目标 sector 的顺序必须保持）。
* 不同发送者之间顺序不保证（允许交错）。

如果你未来要更强一致性，可以加“per-sender sequence”。

---

# C2) mixin around 织入顺序：线性化、冲突与可审计

> 目标：多个 mixin 同时对同一 target（type 或 sector）做增强/around，必须有**唯一确定的执行顺序**，并能生成审计报告。

## 1. 名词与对象

* target：`T`（类型）或 `sector S`
* join point：某个函数 `f`（比如 `fn handle(...)`）
* mixin：`Mi`，带 `(name, version)` 唯一标识

mixin item 两类：

1. `add`: 新增函数/方法
2. `around`: 拦截已有函数（或新增函数也可被 around）

## 2. “可用 mixin 集合”的确定（启用集）

一个编译单元中，某 target 的 mixin 集合由以下来源组成：

* 显式 `use mixin X vN`
* 或编译器默认启用的标准 mixin（若存在）

记该 target 的启用集为 `M = {M1, M2, ...}`。

## 3. 冲突的严格定义

对 target 的同名函数 `f`：

### 3.1 Add-Add 冲突

若存在两个 mixin 都 `add fn f(...)`，且签名在擦除泛型后等价（或同名同参）：

* 必须通过 `resolve mixin-conflict` 指定优先级
* 否则编译错误

### 3.2 Base 与 Add

若 base（原定义）中已有 `f`，而 mixin `add f` 试图覆盖：

* 视为冲突（除非 mixin 声明 `replace fn` ——可选扩展）
* MVP：禁止覆盖，只能 `around`，不能 add 同名替换

### 3.3 Around-Around 冲突

多个 `around fn f` 不算冲突，它们需要线性化形成调用链（下面定义）。

---

## 4. 线性化规则（确定 around 链）

### 4.1 全局顺序：MixinOrder

对某 target 的启用 mixin 集合 `M`，定义一个全序 `MixinOrder(T)`：

排序 key（从高到低）：

1. 显式 `resolve` 给出的 `prefer A over B`
2. 若无 prefer 约束：按 `use mixin` 的出现顺序（文件顺序）
3. 若仍相同（跨文件合并）：按 `(MixinName lexical, version desc)` 保证稳定

这会得到一个列表：
`L = [M1, M2, ..., Mk]`（从“更优先”到“更不优先”）

### 4.2 C3 线性化（可选但更强）

如果你未来引入“mixin 依赖”或“mixin 组合”（mixin 内部 use 其他 mixin），就需要 C3。
**MVP 可先不用 C3**，但要把扩展点写清楚：

* MVP：`L` 直接用上面的排序
* v2：若 mixin 可声明 `requires`，则对依赖图做 C3 linearization 得到 `L`

我先给 MVP 的确定链。

### 4.3 Around 链的构造（最关键）

对 join point 函数 `f`：

* 设 base 实现为 `base_f`
* 找到所有提供 `around fn f` 的 mixin，按 `L` 的顺序过滤成 `A = [a1, a2, ..., am]`

**织入后的调用链**定义为：

* 最外层为 `a1`
* 最内层为 `am`
* 最终 `proceed()` 调用落到 `base_f`

形式化：

```
weaved_f = a1( proceed -> a2( proceed -> ... am( proceed -> base_f ) ... ) )
```

也就是说：**越“优先”的 mixin 越外层**，它最先执行、最后结束（典型 AOP 语义）。

### 4.4 proceed 的语义（严格）

在 `around fn f(...)` 的块中：

* `proceed(args...)` 只能调用 **一次**（MVP 强约束，避免不可控）
* `proceed` 的参数必须与 `f` 兼容（同类型或可隐式转换）
* 如果 around 没有调用 proceed：

  * 等价于短路（拦截并吞掉 base）
  * 但必须显式声明 `around fn ... (shortcircuit)`（建议强制）
  * MVP：若缺少 proceed 直接报错，防止意外吞执行

我建议 MVP 规则：**proceed 必须恰好调用一次**（最可审计）。

---

## 5. Add 方法解析顺序（避免“谁提供的方法”不确定）

当调用一个方法 `x.f(...)`：

查找顺序（从高到低）：

1. target 本身定义的 `fn f`
2. mixin `add fn f`，按 `L` 顺序取第一个匹配签名
3. 若多个匹配且无 resolve：编译错误（歧义）

> 因为 MVP 禁止 mixin 覆盖 base 同名，所以 1 永远优先 2。

---

## 6. 审计输出（规范要求）

编译器必须能输出一份 “Weave Report”（至少包含）：

* 对每个 target、每个函数 f：

  * around 链顺序：`a1 -> a2 -> ... -> base`
  * 使用的 mixin 列表 `L`
  * 冲突与 resolve 结果
  * source span（文件+行列）用于追踪

---

# 一个确定性示例（把顺序说死）

```flavent
sector web:
  fn handle(req: Event.HttpRequest) -> Unit =
    log.info("base")

use mixin M.Audit v2
use mixin M.Metrics v1

mixin M.Audit v2 into sector web:
  around fn handle(req: Event.HttpRequest) -> Unit:
    log.info("audit enter")
    proceed(req)
    log.info("audit exit")

mixin M.Metrics v1 into sector web:
  around fn handle(req: Event.HttpRequest) -> Unit:
    let t0 = time.now()
    proceed(req)
    metrics.hist("lat", time.now()-t0)
```

启用顺序 `use`：Audit 在前，Metrics 在后
=> `L = [Audit, Metrics]`
=> around 链：**Audit 外层，Metrics 内层，最后 base**

执行顺序严格为：

1. audit enter
2. metrics（计时开始）
3. base
4. metrics（记录）
5. audit exit

---

如果你想继续“更硬核形式化”，下一步通常是：

* 给出 **operational semantics（小步语义）**：用状态转移形式描述 event loop、rpc、await、stream pull/push；
* 或给出 **类型推导规则**：用推理规则（⊢）把 effect/type 推导写成论文式。

你更想要哪一个？（你回 “小步语义” 或 “推导规则” 就行）
