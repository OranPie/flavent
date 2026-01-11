# REF8: Python 依赖最小化与 stdlib 自举规范（A 档：最小 builtin）

本规范的目标是：**最大化 Flavent 自举能力**，把 Python 侧实现收缩到“没有它就无法运行/无法观测外界”的最小集合。

> 原则：除非功能“与外界交互”或“语言运行时必须原语”，否则一律放在 stdlib（Flavent 代码）实现。

---

## 1. 术语

- **builtin**：编译器/运行时硬编码提供的类型/原语（在 stdlib 缺失时也存在）。
- **stdlib**：用 Flavent 写的标准库模块，按 `use` 加载。
- **bridge**：`_bridge_python` 模块，提供不可自举的系统能力（时间/IO/系统调用等）。

---

## 2. 最小 builtin 集合（A 档）

### 2.1 必须 builtin 的类型

仅保留：

- `Unit`
- `Bool`
- `Int`
- `Float`
- `Str`
- `Bytes`

> 说明：
> - `Json/Uuid/Time/Duration/Chan/Stream/Set` **不作为 builtin**，应逐步以 stdlib 实现或由 bridge 提供最小支撑。
> - 允许在实现早期阶段暂时保留更多 builtin，但必须在文档中标记“临时”，并有迁移计划。

### 2.2 必须 builtin 的语法/运行时原语

- 缩进块语法（lexer 的 `INDENT/DEDENT`）
- `sector`/事件循环语义
- `emit` / `await`
- `rpc` / `call`
- effect 检查（`pure` vs `@Sector`）

---

## 3. stdlib 模块系统规范

### 3.1 模块加载路径

`use a.b.c` 的加载规则（按顺序尝试）：

1. `stdlib/a/b/c.flv`
2. `stdlib/a/b/c/__init__.flv`

要求：

- 模块加载必须支持循环检测与去重。
- stdlib 预加载入口为 `stdlib/prelude.flv`。

### 3.2 stdlib 中的命名策略

- `collections.*` 只定义数据结构与纯算法（不触发 bridge）。
- `time.*` 对外 API 尽量纯 Flavent；若需要系统时间，则通过 bridge。
- `math.*` 必须纯 Flavent。

---

## 4. `_bridge_python` 的严格边界

### 4.1 形式

- `_bridge_python` 是 stdlib 内部模块，通常以 `sector _bridge_python:` 暴露能力。
- 上层 stdlib 通过 `rpc/call` 调用。

### 4.2 允许 bridge 的能力（必需项）

仅允许“外界交互”类：

- **时间**：wall clock / monotonic clock、sleep
- **IO**：文件/网络/控制台
- **系统**：进程、环境变量、平台信息
- （可选）随机数：若暂不自举 PRNG

### 4.3 禁止 bridge 的能力

以下一律不得通过 Python 实现：

- 容器数据结构：`List/Map/Queue/Heap/Set`
- 通用算法：排序、搜索、哈希表实现
- 纯数据变换：解析/编码（若可自举）

---

## 5. stdlib 自举路线（建议优先级）

### P0（已完成/正在完成）

- `collections.list`：`List[T] = Nil | Cons(T, List[T])`
- `collections.queue`：`Queue[T]`（two-list queue）
- `collections.heap`：Int-only skew heap
- `collections.map`：关联表 Map（type alias over List[Entry]）

### P1（下一步）

- `math`：`min/max/abs/clamp` 等
- `time`：上层 API（格式化可后续），底层 now/sleep 走 bridge

### P2（后续）

- `collections.set`：可先用 `Map[T, Unit]` 或去重 List
- `uuid/json`：逐步实现或定义最小接口

---

## 6. 编译器支持要求（为自举服务）

为了让 stdlib 能自举，需要编译器提供以下能力：

- Sum type 构造器的通用类型推导（含泛型）
- 0-arity 构造器可作为值使用（在有 expected type 的位置）
- 泛型 record 的字段类型检查（record literal / member / constraints）
- 泛型 type alias 展开（例如 `type Map[K,V] = List[Entry[K,V]]`）

---

## 7. 非目标（Non-goals）

- 不要求 stdlib 在没有 `_bridge_python` 的情况下访问外界（时间/IO 仍需要 bridge）。
- 不要求立即实现高性能数据结构；先以可用性与语义正确为主。
