# `csv`

## 概述
纯 Flavent 实现的 CSV 解析与格式化工具。

特性：
- 支持自定义分隔符与引用符。
- 支持 RFC 风格引用转义（字段内 `""`）。
- 提供按行与多行文本的解析/输出接口。

## 导入
```flavent
use csv
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type CsvOptions = { delimiter: Str, quote: Str }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn csvDefaultOptions() -> CsvOptions = { delimiter = ",", quote = "\"" }
fn csvParseLineWith(line: Str, opts: CsvOptions) -> Result[List[Str], Str] = do:
fn csvParseLine(line: Str) -> Result[List[Str], Str] = csvParseLineWith(line, csvDefaultOptions())
fn csvParseWith(text: Str, opts: CsvOptions) -> Result[List[List[Str]], Str] = do:
fn csvParse(text: Str) -> Result[List[List[Str]], Str] = csvParseWith(text, csvDefaultOptions())
fn csvEncodeFieldWith(field: Str, opts: CsvOptions) -> Str = do:
fn csvEncodeField(field: Str) -> Str = csvEncodeFieldWith(field, csvDefaultOptions())
fn csvStringifyLineWith(fields: List[Str], opts: CsvOptions) -> Str = _csvJoinFieldsAcc(fields, opts, "")
fn csvStringifyLine(fields: List[Str]) -> Str = csvStringifyLineWith(fields, csvDefaultOptions())
fn csvStringifyWith(rows: List[List[Str]], opts: CsvOptions) -> Str = joinLines(_csvStringifyRowsAcc(rows, opts, Nil))
fn csvStringify(rows: List[List[Str]]) -> Str = csvStringifyWith(rows, csvDefaultOptions())
```
<!-- AUTO-GEN:END FUNCTIONS -->
