# `stringfmt`

## Overview
Basic placeholder formatting for strings.

Rules:
- `{}` uses the next positional argument.
- `{0}` uses an explicit positional index.
- `{{` and `}}` escape braces.
- Named placeholders (`{name}`) work with `formatWith`/`formatMap`.
- Format spec: `{key:fill?align?width?type}` where align is `<`/`>`/`^` and type is `s`/`d`/`f`/`b`.
Use `formatArgs`/`formatWithArgs` to pass typed values.

## Import
```flavent
use stringfmt
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type FmtArg = FmtStr(Str) | FmtInt(Int) | FmtFloat(Float) | FmtBool(Bool)
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn concat(a: Str, b: Str) -> Str = a + b
fn concat3(a: Str, b: Str, c: Str) -> Str = a + b + c
fn surround(s: Str, left: Str, right: Str) -> Str = left + s + right
fn formatArgs(tmpl: Str, args: List[FmtArg]) -> Str = do:
fn format(tmpl: Str, args: List[Str]) -> Str = formatArgs(tmpl, _sfArgsFromStr(args))
fn format1(tmpl: Str, a0: Str) -> Str = format(tmpl, Cons(a0, Nil))
fn format2(tmpl: Str, a0: Str, a1: Str) -> Str = format(tmpl, Cons(a0, Cons(a1, Nil)))
fn format3(tmpl: Str, a0: Str, a1: Str, a2: Str) -> Str = format(tmpl, Cons(a0, Cons(a1, Cons(a2, Nil))))
fn formatWithArgs(tmpl: Str, posArgs: List[FmtArg], namedArgs: Map[Str, FmtArg]) -> Str = do:
fn formatWith(tmpl: Str, posArgs: List[Str], namedArgs: Map[Str, Str]) -> Str =
fn formatMapArgs(tmpl: Str, args: Map[Str, FmtArg]) -> Str =
fn formatMap(tmpl: Str, args: Map[Str, Str]) -> Str = formatMapArgs(tmpl, _sfMapArgsFromStr(args))
fn formatKV(tmpl: Str, k0: Str, v0: Str) -> Str = formatMap(tmpl, mapPut(mapEmpty(), k0, v0))
```
<!-- AUTO-GEN:END FUNCTIONS -->
