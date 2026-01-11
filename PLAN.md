# flavent 编译器设计计划（Python 实现）

本计划以 `REF1.md` ~ `REF7.md` 为权威规格来源。

目标：用 Python 分阶段实现一个可运行的 `flavent` 编译器/解释器流水线：

- `source (.flv)`
- `Lexer (INDENT/DEDENT)`
- `Parser -> AST`（对齐 `REF6`）
- `Resolve (符号表/作用域)`（对齐 `REF7#2`）
- `Desugar AST -> HIR`（对齐 `REF7#1`）
- `Type+Effect check`（对齐 `REF2#2`）
- `Mixin weave`（对齐 `REF7#3` + `REF5#C2`）
- `Runtime (sectors/event loop)`（对齐 `REF4/REF5`）

---

## Phase 1：词法 + 语法 + AST（MVP 可解析闭环）

### 目标
构建一个最小闭环：

- 能对 `.flv` 源码做词法分析（含 `INDENT/DEDENT`）
- 能按 `REF1` 的 EBNF 解析出 AST（结构对齐 `REF6`）
- 能通过 CLI 运行：`python -m flavent parse file.flv`，输出 AST（JSON/pretty）
- 提供一组最小测试用例，覆盖关键语法节点

### 交付物（Deliverables）
- **项目结构（Python package）**
  - `flavent/__init__.py`
  - `flavent/cli.py`：命令行入口（parse/lex）
  - `flavent/diagnostics.py`：错误/Span/源码定位格式化
  - `flavent/span.py`：`Span` 定义与构造
  - `flavent/token.py`：Token/TokenKind
  - `flavent/lexer.py`：Lexer（含缩进算法、注释、括号内忽略 NL）
  - `flavent/ast.py`：AST 数据结构（dataclasses），字段与 `REF6` 对齐
  - `flavent/parser.py`：递归下降（或 Pratt）解析器
  - `tests/`：pytest

- **词法（对齐 REF1#2 + REF2#1）**
  - 空白/注释：支持 `//` 单行、`/* */` 块（先不做嵌套也可，但需要明确 TODO）
  - 关键字：按 `REF1#2.4`
  - 字面量：Int/Float/Str/Bytes/Bool
  - 括号内换行：不产生 `NL`，不触发缩进栈变化（`REF2#1.1`）
  - 缩进：只允许空格；Tab 直接错误（`REF2#1.3`）
  - `INDENT/DEDENT` 算法：严格按 `REF2#1.4`

- **语法（对齐 REF1#3）**
  - Top-level items：type/const/let/need/fn/mixin/use/resolve/sector/on/run
  - Blocks：`X: NL INDENT ... DEDENT`（do/sector/match/if/else/for/mixin/around/resolve）
  - 表达式优先级：按 `REF1#3.10`
  - `await`/`rpc`/`call`：解析为 AST 节点（对齐 `REF6#9.5`）
  - `proceed(...)`：仅在 mixin around block 内语法允许（语义限制 Phase 2+ 做）

- **AST（对齐 REF6）**
  - 以 dataclasses 实现 `Program/TopItem/.../Expr/Stmt` 等节点
  - 每个节点包含 `span`（文件、行列、offset），便于错误报告

- **诊断与错误体验**
  - 统一错误类型：LexError/ParseError（含 span + message）
  - CLI 输出：错误时打印 file:line:col + 摘要 + 源码行 + caret

### 验收标准（Acceptance Criteria）
- `python -m flavent lex examples/minimal.flv`
  - 输出 token 序列，能看到 `INDENT/DEDENT/NL` 在正确位置
- `python -m flavent parse examples/minimal.flv`
  - 输出 AST（JSON）
  - `run()` 可缺省（AST 中 `run` 为 None），不在 Phase 1 处理默认注入
- pytest 通过，至少包含：
  - 缩进错误：`expected indent` / `unexpected indent` / `unaligned dedent`
  - 表达式优先级：`a |> f |> g(x)` 解析结构正确（仍保留 PipeExpr，Phase 3 才 desugar）
  - `sector` 内 items、`mixin around` block、`resolve mixin-conflict` block

### Phase 1 的边界（明确不做什么）
- 不做 name resolution（SymbolId）
- 不做类型/effect 检查
- 不做 AST->HIR desugar
- 不做 mixin weaving
- 不做 runtime

---

## Phase 2：符号表与作用域解析（Name Resolution）

对齐 `REF7#2`：

- Pass1：收集声明（global/sector scopes）
- Pass2：解析引用（TypeRef -> TypeId；VarExpr -> SymbolId）
- 产物：Resolved AST（或 Typed AST 的前置形态），并为后续 HIR/类型检查准备

验收：能在示例中正确解析：

- 内层遮蔽（shadowing）规则
- sector-qualified 调用里的 sector 与 fn 解析
- 产生明确错误：NameNotFound / NameAmbiguity

---

## Phase 3：AST → HIR 降糖（Desugar & Normalize）

对齐 `REF7#1`：

- 默认 sector 注入（顶层 on handler 归入 main）
- `PipeExpr` 降糖为普通调用链
- `TrySuffixExpr (?)` 降糖为显式 early-exit（基于边界：fn Result/Option 或 handler abort+ErrorEvent）
- `await EventType` 降糖为 HIR 原语 `AwaitEvent`
- `rpc/call` 降糖为 HIR `RpcCall`

验收：HIR 不包含 PipeExpr/TrySuffixExpr/ProceedExpr。

---

## Phase 4：类型系统 + effect 系统（Type & Effect Checking）

对齐 `REF2#2`：

- `pure` vs `@S` 的 effect 推导与 join
- 顶层 const/let 必须 pure
- `fn` 未标注必须 pure；`fn@S` 不能混入其他 `@T`
- `emit/await/rpc/call` 只能在 sector 内
- `?` 仅允许 Result/Option 且受返回类型/handler 规则约束

验收：提供一组正/反例用例，错误信息可定位。

---

## Phase 5：Mixin weaving（around 链 + add 冲突）

对齐 `REF5#C2` + `REF7#3`：

- 启用集：use mixin
- resolve prefer 形成偏序并拓扑排序（检测环）
- around 链 outer->inner 线性化
- proceed 替换为 next impl 调用（weaved 后无 proceed）
- 生成 Weave Report（审计输出）

验收：示例中顺序严格符合 `use` + `prefer` 规则。

---

## Phase 6：运行时（sectors / event loop / handler 调度）

对齐 `REF4` + `REF5#C1`：

- sector mailbox：sysQ/rtQ/appQ
- handler 选择与确定性（when specificity + file order）
- 公平性配额 + `yield()`
- handler 中 `?` 的错误通道：emit `Event.Error` + abort handler
- need cell 单飞 + TTL + restart 交互

验收：用 Python 解释执行 HIR：能跑最小示例（Event.Start -> IO -> stop）。
