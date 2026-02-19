# `path`

## Overview
Pure-Flavent path helpers for normalization and segment operations.

Provided capabilities:
- Normalize separators and `.` / `..` segments.
- Join path parts.
- Extract basename/dirname/extension/stem.

## Import
```flavent
use path
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn pathIsAbs(p: Str) -> Bool = startsWith(_canonSep(p), "/")
fn pathNormalize(p: Str) -> Str = do:
fn pathJoin(a: Str, b: Str) -> Str = do:
fn pathJoinAll(parts: List[Str]) -> Str = _pathJoinAllAcc(parts, "")
fn pathBase(p: Str) -> Str = do:
fn pathDir(p: Str) -> Str = do:
fn pathExt(p: Str) -> Str = do:
fn pathStem(p: Str) -> Str = do:
```
<!-- AUTO-GEN:END FUNCTIONS -->
