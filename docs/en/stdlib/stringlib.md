# `stringlib`

## Overview
String helpers focused on deterministic, allocation-light operations.

Notes:
- `strFind` returns `-1` when no match is found.
- `strFindOpt` returns `Some(index)` / `None` and is preferred in new code.
- `startsWith`/`endsWith` and `strStartsWith`/`strEndsWith` are equivalent (alias pair for compatibility).
- `strLength`/`strCode`/`strSliceRange`/`strFromCodePoint` are low-level bridge wrappers for reuse by other stdlib modules.

## Import
```flavent
use stringlib
```

## Examples
```flavent
let i0 = strFind("abcabc", "bc", 0)      // 1
let i1 = strFindOpt("abc", "z", 0)       // None
let ok = strStartsWith("hello", "he")    // true
let out = trimSpaces("  hi  ")           // "hi"
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn strFind(h: Str, needle: Str, start: Int) -> Int = do:
fn strFindOpt(h: Str, needle: Str, start: Int) -> Option[Int] = do:
fn strContains(h: Str, needle: Str) -> Bool = strFind(h, needle, 0) >= 0
fn strLength(s: Str) -> Int = strLen(s)
fn strCode(s: Str, i: Int) -> Int = strCodeAt(s, i)
fn strSliceRange(s: Str, a: Int, b: Int) -> Str = strSlice(s, a, b)
fn strFromCodePoint(code: Int) -> Str = strFromCode(code)
fn startsWith(h: Str, prefix: Str) -> Bool = do:
fn endsWith(h: Str, suffix: Str) -> Bool = do:
fn strStartsWith(h: Str, prefix: Str) -> Bool = startsWith(h, prefix)
fn strEndsWith(h: Str, suffix: Str) -> Bool = endsWith(h, suffix)
fn trimLeftSpaces(s: Str) -> Str = do:
fn trimRightSpaces(s: Str) -> Str = do:
fn trimSpaces(s: Str) -> Str = trimRightSpaces(trimLeftSpaces(s))
fn split(s: Str, sep: Str) -> List[Str] = do:
fn join(xs: List[Str], sep: Str) -> Str = _joinAcc(xs, sep, "")
```
<!-- AUTO-GEN:END FUNCTIONS -->
