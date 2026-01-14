# `regex`

## 概述
最小正则实现（当前以功能为主，语法范围有限）。

要点：
- `compile` 当前不做校验（总是成功）。
- `compileChecked` 会做基本语法校验（括号/字符类/转义等）。
- `findFirstSpan/findAllSpans` 返回匹配片段的 `[start, end)`。

## 导入
```flavent
use regex
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type Regex = { pat: Str }
type RxSpan = { start: Int, end: Int }
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
fn findFirst(r: Regex, s: Str) -> Option[Int] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->

