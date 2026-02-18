# `regex`

## Overview
Minimal regex implementation.

Key points:
- `compile` does not validate.
- `compileChecked` performs basic validation (groups/classes/escapes).
- `findFirstSpan` / `findAllSpans` return `[start, end)` spans.
- `findFirst` returns the first matching substring.
- Supports `\\b` word boundary and lazy quantifiers (`*?`, `+?`, `??`).
- `replace`/`replaceAll` support `$0` (whole match) and `$1`..`$n`.
- `findFirstCaptures` returns group 0 (full match) followed by groups 1..n.
- Zero-length matches in `replaceAll` always advance safely to avoid infinite loops.

## Import
```flavent
use regex
```

## Examples
```flavent
let r = compile("^ab$")
let ok = isMatch(r, "ab")                               // true
let caps = findFirstCaptures(compile("(ab)(cd)"), "zzabcdyy")
// Some(Cons("abcd", Cons("ab", Cons("cd", Nil))))
let out = replace(compile("(ab)(cd)"), "zzabcdyy", "<$0,$1,$2,$$>")
// "zz<abcd,ab,cd,$>yy"
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Regex = { pat: Str }
type RxSpan = { start: Int, end: Int }
type RxCapture = { idx: Int, start: Int, end: Int }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
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
