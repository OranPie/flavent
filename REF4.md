下面进入 **B：语义强化（偏语言设计）**。我给你一套“可写进规范”的**严格语义**，覆盖你点到的 4 块：**handler 的错误策略、sector 崩溃模型、need 一致性模型、Stream/背压形式语义**。尽量做到：实现者照着写 runtime 就不会歧义。

---

# B1) Handler 中 `?` /错误 的严格策略（ErrorEvent + Supervisor）

## 1. 事件处理的返回语义

* 所有 `on EventX -> body` 的 handler **静态返回 `Unit`**（即：handler 不是普通函数，不把值返回给调用者）。
* handler 内允许 `?`（对 `Result/Option`），但传播边界不是“return 某个值”，而是走**统一错误通道**。

## 2. 错误通道：标准事件 `Event.Error`

语言内建一类错误事件（可固定名字或标准库提供）：

```flavent
type Event.Error = {
  sector: Str,
  handler: Str,        // handler 标识（可用 source span hash）
  cause: Err,          // 结构化错误
  event: Json,         // 原始事件（序列化快照）
  time: Time
}
```

## 3. `?` 在 handler 中的行为（严格）

在 handler body 内出现 `expr?`：

* 若 `expr` 为成功值：继续执行
* 若失败（`Err(e)` 或 `None`）：

  1. 立即**中止当前 handler**（不再执行后续语句）
  2. 运行时生成并 `emit Event.Error{...}` 到**本 sector 的 supervisor**
  3. handler 视为 **Failed**

> 这条保证：handler 的失败不会悄悄吞掉，也不会把 sector 直接带崩（除非 supervisor 策略规定要崩）。

## 4. 显式错误处理：`try`/`catch`（可选扩展，但很实用）

为了不让所有错误都走 supervisor，你可以提供一个最小 `try` 表达式（不破坏扁平）：

```flavent
try:
  ... stmts ...
catch e: Err ->
  ... stmts ...
```

语义：捕获该块内由 `?` 引发的失败（以及显式 `throw`），转为本地处理，不生成 `Event.Error`（除非 catch 里再 `emit`）。

---

# B2) Sector 崩溃模型（Supervisor Tree + Restart 策略）

sector 是并发隔离单元，你要的是“像 Erlang/actor 一样可监管，但更可控”。

## 1. Sector 状态机

每个 sector 运行时有状态：

* `Starting`：初始化（加载 need、注册 handlers）
* `Running`：正常处理事件
* `Stopping`：停止中（清空/丢弃 mailbox 取决于策略）
* `Crashed`：未处理异常导致崩溃（或 supervisor 判定）
* `Restarting`：重启中

## 2. 崩溃定义（Crash）

满足任意条件即判定 sector crash：

* handler 中发生**未捕获异常**（非 `Result`/`Option` 的运行时异常）
* supervisor 策略要求：连续失败超过阈值 / 特定错误类型为 fatal
* 资源不可恢复（例如 mailbox 内部损坏，或必须的 runtime 组件失效）

> 注意：handler 的 `?` 失败默认不算 crash（只算 handler failed），除非 supervisor 指定“某些 Err 视为 fatal”。

## 3. Supervisor（监管器）

每个 sector 有一个 supervisor（可以是隐式内建或显式声明）：

```flavent
sector web supervisor:
  strategy: restart
  max_restarts: 3 in 10s
  on_error: log+metrics
  on_exhausted: escalate
```

### 推荐的默认策略（可写成语言默认）

* `strategy = restart`
* `max_restarts = 5 in 30s`
* `on_error = emit Event.Error + log`
* `on_exhausted = stop process` 或 `escalate to parent`

## 4. 重启语义（Restart semantics）

当 sector 重启：

* sector 内 `let` 状态 **重置为初始值**
* `need` 缓存**默认清空**（可配置保留，见 B3）
* handler 注册保持不变（因为是代码静态的）
* mailbox 处理策略必须明确（选一种）：

### Mailbox 策略（必须在规范里二选一）

1. **Drop**（推荐默认）：重启时丢弃所有未处理事件
2. **Replay**：重启后继续处理崩溃前未处理事件（要求事件可重放且幂等，复杂但强）

我建议默认 Drop，配合显式“可靠队列/持久化 stream”来做 Replay。

## 5. Supervisor Tree（可选但很强）

支持 sector 的父子层级（监督树）：

* 子 sector 崩溃，父 supervisor 决定重启子还是升级（escalate）
* 父崩溃可带着子一起重启（one-for-all / one-for-one）

最小实现可只做“每 sector 自带 supervisor”，树结构作为 v2 扩展。

---

# B3) `need` 一致性模型（并发、失败缓存、重启互动）

`need` 是你语言的“按需评估取值”，语义必须非常清晰，否则实现会乱。

## 1. 状态模型：NeedCell

每个 `need x = expr` 在运行时是一个 cell：

* `Unforced`
* `Forcing(owner=fiberId)`
* `Ready(value)`
* `Failed(error)`（是否缓存失败由策略决定）
* `Expired(deadline)`（若 TTL）

## 2. by-need（单飞）语义：同一时刻只计算一次

当某 fiber 在 sector S 中第一次读取 `x`：

* 若 `Unforced`：把 cell 置为 `Forcing(owner=thisFiber)`，开始计算 expr
* 若 `Forcing`：其他 fiber **挂起等待**（不是重复算）
* 若 `Ready`：立即返回缓存值
* 若 `Failed`：

  * 默认：直接返回失败（等价 `Err` 或 throw 取决于 need 类型）
  * 若声明 `need(cacheFail="no")`：重新计算（回到 `Forcing`）

## 3. need 的 effect 限制（非常关键）

为了不破坏 sector 隔离：

* `need` 的 expr 允许副作用，但必须**绑定到一个 sector**执行。
* 规则：第一次读取 `need` 的那个 sector，就是它的执行上下文；因此：

  * 若 need expr 推导 effect 为 `@fs`，那么它**只能在 fs sector 中首次触发**
  * 其他 sector 读取它要通过 `rpc fs.getNeedValue()` 或让 need 定义在 fs sector 内（推荐）

### 推荐规范写法（最严格、最好实现）

把 `need` 放到 sector 内部作为 sector state：

```flavent
sector fs:
  need config = fs.readText("app.toml") |> toml.parse
```

这样 config 的首次求值必然发生在 fs sector，不存在跨 sector 歧义。

## 4. TTL 与一致性

`need(cache="ttl:5m") x = expr`：

* `Ready(value, expiresAt)` 到期后变为 `Expired`
* 下一次读取触发重新计算（同样单飞）

## 5. 与 sector 重启的互动（必须定死）

当 sector 重启：

* 默认：该 sector 内所有 NeedCell 回到 `Unforced`
* 可选策略（通过 supervisor 配置）：

  * `need_cache: clear`（默认）
  * `need_cache: keep`（保留 Ready 值；Failed 仍建议清空）

---

# B4) Stream / Backpressure 的形式语义（事件驱动数据流）

你想要“事件驱动 + on-demand”，那 Stream 必须是**可背压的拉/推混合模型**，否则要么丢数据，要么内存炸。

## 1. 抽象：Stream 是带背压的生产者

定义：

* `Stream[T]` 不是 List，也不是无限 push；它是一个**异步序列**。
* 它与 consumer 之间通过一个 **Demand（需求量）协议**协调。

## 2. 核心协议（最小可实现）

把 stream runtime 定义成三个事件（内部或显式）：

* `Event.StreamPull{ id, n }`：consumer 请求 n 个元素
* `Event.StreamPush{ id, item }`：producer 交付一个元素
* `Event.StreamEnd{ id, reason }`：结束（正常/错误/取消）

语义规则：

* producer **只能在收到 Pull 后** push（否则违反背压）
* consumer 发 Pull 后，可以逐个收到 Push；消费速率决定 Pull 频率
* `buffer` 是显式算子，不隐式无限缓存

## 3. 常用算子的语义约束（严格）

以 `stream.map / filter / take / forEach` 为例：

* `map(f)`：对每个 item 应用纯函数 f（要求 f 是 `pure`，除非你提供 `mapEffect`）
* `filter(p)`：p 也默认 `pure`
* `take(k)`：消费 k 个后发送 cancel 并 end
* `forEach(g)`：g 允许 `@S`（因为 forEach 通常是副作用终端算子），但必须在某个 sector 内执行

> 这延续 effect 体系：中间算子默认纯，终端算子允许副作用。

## 4. Buffer 的明确定义（不要隐式）

提供一个显式算子：

```flavent
stream.buffer(cap=1024, overflow="block|drop|latest")
```

* `block`：producer 在 buffer 满时等待（严格背压）
* `drop`：丢弃新来的 item（需计数/可观察）
* `latest`：保留最新，覆盖旧值（适合 UI/传感器）

## 5. 错误与取消

* producer 出错 → `StreamEnd(reason=Err)`
* consumer 取消 → producer 必须停止产出并释放资源（socket/file 等）
* `forEach` 内发生 `?` 失败：

  * 默认：cancel stream + emit `Event.Error`（同 handler 语义）

---

# 一个把 B1-B4 串起来的“语义示例”（不求语法花哨）

```flavent
type Event.Error = { sector: Str, handler: Str, cause: Err, event: Json, time: Time }
type Err = { msg: Str }
type Result[T,E] = Ok(T) | Err(E)

sector ingest supervisor:
  strategy: restart
  max_restarts: 3 in 10s
  need_cache: clear
  mailbox: drop

sector ingest:
  need token = auth.fetchToken()          // 首次用到时才拉 token，失败走 ErrorEvent

  on Event.Start ->
    let s: Stream[Bytes] = net.listen(9000)     // @net，只能在 sector 内
    s
      |> stream.buffer(cap=1024, overflow="block")
      |> stream.map(b -> b.toStr())             // pure
      |> stream.forEach(line -> do:             // effectful terminal
           let t = token?                       // need + ?，失败 -> handler fail -> ErrorEvent
           log.info("line", tags={auth=t})
         )
```

---

如果你要把 B 继续“更严格/更形式化”，下一步通常是两件：

1. 给 **handler 调度公平性** 与 **事件优先级** 一个精确定义（避免 starvation）。
2. 给 **mixin around 的织入顺序** 与 **冲突解析** 一套完全确定的线性化规则（类似 C3 linearization）。

你只要回：`继续1` 或 `继续2` 我就接着把那部分也写成规范。
