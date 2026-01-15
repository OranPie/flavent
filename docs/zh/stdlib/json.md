# `json`

## 概述
JSON 编解码（纯 Flavent 解析/序列化）。

注意：
- `loads` 返回 `Result[JsonValue, Str]`。
- 数字支持整数（`JInt`）与浮点（`JFloat`，含科学计数法）。
- 字符串转义支持 `\\uXXXX`（基础 Unicode）。
- 会跳过常见空白（空格/\t/\n/\r）。

## 导入
```flavent
use json
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type JsonValue = JNull | JBool(Bool) | JInt(Int) | JFloat(Float) | JStr(Str) | JArr(List[JsonValue]) | JObj(Map[Str, JsonValue])
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn jNull() -> JsonValue = JNull
fn dumps(j: JsonValue) -> Str = match j:
fn loads(s: Str) -> Result[JsonValue, Str] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
