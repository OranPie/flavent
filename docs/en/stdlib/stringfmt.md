# `stringfmt`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use stringfmt
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn concat(a: Str, b: Str) -> Str = a + b
fn concat3(a: Str, b: Str, c: Str) -> Str = a + b + c
fn surround(s: Str, left: Str, right: Str) -> Str = left + s + right
fn format(tmpl: Str, args: List[Str]) -> Str = do:
fn format1(tmpl: Str, a0: Str) -> Str = format(tmpl, Cons(a0, Nil))
fn format2(tmpl: Str, a0: Str, a1: Str) -> Str = format(tmpl, Cons(a0, Cons(a1, Nil)))
fn format3(tmpl: Str, a0: Str, a1: Str, a2: Str) -> Str = format(tmpl, Cons(a0, Cons(a1, Cons(a2, Nil))))
fn formatWith(tmpl: Str, posArgs: List[Str], namedArgs: Map[Str, Str]) -> Str = do:
fn formatMap(tmpl: Str, args: Map[Str, Str]) -> Str = _sfConcatPieces(reverse(_sfScanMap(tmpl, 0, args, Nil)))
fn formatKV(tmpl: Str, k0: Str, v0: Str) -> Str = formatMap(tmpl, mapPut(mapEmpty(), k0, v0))
```
<!-- AUTO-GEN:END FUNCTIONS -->
