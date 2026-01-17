# `py`

## 概述
Python 适配器统一入口（v2：子进程隔离）。

规则：
- Flavent 代码不能直接 import Python。
- 只能通过 `py.invoke(adapter, method, payload)` 走受控桥接。
- 建议配合 `flm.json` 的 `pythonAdapters` + `flavent pkg install` 自动生成的 `pyadapters` wrappers 使用。
 - `invokeText` 使用 ASCII 编码；`invokeJson` 使用 JSON 文本。

## 导入
```flavent
use py
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn invoke(adapter: Str, method: Str, payload: Bytes) -> Result[Bytes, Str] = rpc _bridge_python.pyAdapterCall(adapter, method, payload)
fn invokeText(adapter: Str, method: Str, payload: Str) -> Result[Str, Str] = do:
fn invokeJson(adapter: Str, method: Str, payload: JsonValue) -> Result[JsonValue, Str] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->

## 示例

```flavent
use pyadapters.demo
let r = rpc demo.echo(b"hi")
```
