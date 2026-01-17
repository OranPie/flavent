# `regex`

## 概述
最小正则实现（当前以功能为主，语法范围有限）。

要点：
- `compile` 当前不做校验（总是成功）。
- `compileChecked` 会做基本语法校验（括号/字符类/转义等）。
- `findFirstSpan/findAllSpans` 返回匹配片段的 `[start, end)`。
- `findFirst` 返回第一个匹配到的子串。
- 支持 `\\b` 单词边界与惰性量词（`*?`/`+?`/`??`）。
- `replace`/`replaceAll` 支持 `$0`（整体匹配）与 `$1..$n`。
- `findFirstCaptures` 返回第 0 组（整体匹配）以及 1..n 组。

## 导入
```flavent
use regex
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type Regex = { pat: Str }
type RxSpan = { start: Int, end: Int }
type RxCapture = { idx: Int, start: Int, end: Int }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn regex(pat: Str) -> Regex = { pat = pat }
fn compile(pat: Str) -> Regex = regex(pat)
fn compileChecked(pat: Str) -> Result[Regex, Str] = do:
fn isMatch(r: Regex, s: Str) -> Bool = do:
fn findFirstSpan(r: Regex, s: Str) -> Option[RxSpan] = do:
fn findAllSpans(r: Regex, s: Str) -> List[RxSpan] = do:
fn findFirst(r: Regex, s: Str) -> Option[Str] = do:
fn findFirstCaptures(r: Regex, s: Str) -> Option[List[Str]] = do:
fn replace(r: Regex, s: Str, repl: Str) -> Str = do:
fn replaceAll(r: Regex, s: Str, repl: Str) -> Str = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
