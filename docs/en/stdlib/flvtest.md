# `flvtest`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use flvtest
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn fail(msg: Str) -> Result[Unit, Str] = Err(msg)
fn assertTrue(cond: Bool) -> Result[Unit, Str] = match cond:
fn assertEq[T](a: T, b: T) -> Result[Unit, Str] = match a == b:
```
<!-- AUTO-GEN:END FUNCTIONS -->
