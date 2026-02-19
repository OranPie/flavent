# `url`

## 概述
纯 Flavent 实现的 URL 与 query-string 工具模块。

适用场景：
- URL 组件的百分号编码/解码。
- query 字符串中 `+` 与空格的编码/解码。
- 查询参数键值对的解析与构建。

## 导入
```flavent
use url
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type UrlQueryParam = { key: Str, value: Str }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn encodeComponent(s: Str) -> Str = _encodeAcc(s, 0, strLen(s), false, "")
fn decodeComponent(s: Str) -> Result[Str, Str] = _decodeAcc(s, 0, strLen(s), false, "")
fn queryEncode(s: Str) -> Str = _encodeAcc(s, 0, strLen(s), true, "")
fn queryDecode(s: Str) -> Result[Str, Str] = _decodeAcc(s, 0, strLen(s), true, "")
fn queryParse(q: Str) -> Result[List[UrlQueryParam], Str] = do:
fn queryBuild(parts: List[UrlQueryParam]) -> Str = _buildMany(parts, "")
```
<!-- AUTO-GEN:END FUNCTIONS -->
