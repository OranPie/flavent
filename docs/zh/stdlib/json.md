# `json`

## 概述
JSON 编解码（纯 Flavent 解析/序列化）。

注意：
- `loads` 返回 `Option[Json]`：解析失败为 `None`。
- 数字当前只支持 **整数**（`JInt`）。
- 会跳过常见空白（空格/\t/\n/\r）。

## 导入
```flavent
use json
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type Json = JNull | JBool(Bool) | JInt(Int) | JStr(Str) | JArr(List[Json]) | JObj(Map[Str, Json])
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn jNull() -> Json = JNull
fn dumps(j: Json) -> Str = match j:
fn loads(s: Str) -> Option[Json] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->

