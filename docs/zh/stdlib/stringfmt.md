# `stringfmt`

## 概述
基础字符串占位格式化。

规则：
- `{}` 使用下一个位置参数。
- `{0}` 使用显式的位置索引。
- `{{` 与 `}}` 表示转义大括号。
- 命名占位符（`{name}`）可用 `formatWith` / `formatMap`。
- 格式规格：`{key:填充?对齐?宽度?类型}`，对齐为 `<`/`>`/`^`，类型为 `s`/`d`/`f`/`b`。
要传入类型化参数请使用 `formatArgs`/`formatWithArgs`。

## 导入
```flavent
use stringfmt
```

## 类型
```flavent
type FmtArg = FmtStr(Str) | FmtInt(Int) | FmtFloat(Float) | FmtBool(Bool)
```

## 函数
```flavent
fn concat(a: Str, b: Str) -> Str = a + b
fn concat3(a: Str, b: Str, c: Str) -> Str = a + b + c
fn surround(s: Str, left: Str, right: Str) -> Str = left + s + right
fn formatArgs(tmpl: Str, args: List[FmtArg]) -> Str = do:
fn format(tmpl: Str, args: List[Str]) -> Str = do:
fn format1(tmpl: Str, a0: Str) -> Str = format(tmpl, Cons(a0, Nil))
fn format2(tmpl: Str, a0: Str, a1: Str) -> Str = format(tmpl, Cons(a0, Cons(a1, Nil)))
fn format3(tmpl: Str, a0: Str, a1: Str, a2: Str) -> Str = format(tmpl, Cons(a0, Cons(a1, Cons(a2, Nil))))
fn formatWithArgs(tmpl: Str, posArgs: List[FmtArg], namedArgs: Map[Str, FmtArg]) -> Str = do:
fn formatWith(tmpl: Str, posArgs: List[Str], namedArgs: Map[Str, Str]) -> Str = do:
fn formatMapArgs(tmpl: Str, args: Map[Str, FmtArg]) -> Str = ...
fn formatMap(tmpl: Str, args: Map[Str, Str]) -> Str = ...
fn formatKV(tmpl: Str, k0: Str, v0: Str) -> Str = formatMap(tmpl, mapPut(mapEmpty(), k0, v0))
```
