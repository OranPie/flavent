# `regex`

## Overview
Minimal regex implementation.

Key points:
- `compile` does not validate.
- `compileChecked` performs basic validation (groups/classes/escapes).
- `findFirstSpan` / `findAllSpans` return `[start, end)` spans.

## Import
```flavent
use regex
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Regex = { pat: Str }
type RxSpan = { start: Int, end: Int }
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
fn findFirst(r: Regex, s: Str) -> Option[Int] = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
