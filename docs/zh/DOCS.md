# Flavent 语言与标准库文档（中文）

说明：本文件是 `DOCS.md` 的中文翻译/摘录版本，重点覆盖工程使用与标准库调用习惯。

## 1. 缩进与代码块

Flavent 使用类似 Python 的缩进语法；出现 `:` 后必须换行并缩进。

## 2. 扇区（sector）与副作用（rpc/call）

- 通过 `sector` 定义隔离的状态与行为。
- 跨 sector 调用必须使用 `rpc`（有返回）或 `call`（无返回）。

## 3. 标准库调用规范（Library Call Standard）

- 模块名：小写、层级用点号（如 `collections.list`）
- 函数名：camelCase
- 类型名：PascalCase
- 可能失败的 I/O 操作统一返回 `Result[..., Str]`

## 4. 包管理（flm）与模块加载

- 工程使用 `flm.json`。
- resolver 会优先从项目 `src/` / `vendor/` 加载 `use` 模块，然后才回退 `stdlib/`。

## 5. Python adapter（v2）

- 不能直接 import Python。
- 通过 stdlib `py` 统一入口：
  - `rpc py.invoke(adapter, method, payload) -> Result[Bytes, Str]`
  - `rpc py.invokeText(adapter, method, payload) -> Result[Str, Str]`
  - `rpc py.invokeJson(adapter, method, payload) -> Result[JsonValue, Str]`
- `flavent pkg install` 会生成 `pyadapters` wrappers：
  - `vendor/pyadapters/<adapter>.flv`

示例：

```flavent
use pyadapters.demo
let r = rpc demo.echo(b"hi")
```

Wrapper 可配置（`flm.json` 的 `wrappers`）：
- `bytes`（默认）、`text`（ASCII）、`json`（参数打包为 JSON 数组）
