# `std.result`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use std.result
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn unwrapOrEmptyStr[E](r: Result[Str, E]) -> Str = unwrapOr(r, "")
fn isOkAndBool[E](r: Result[Bool, E]) -> Bool = match r:
```
<!-- AUTO-GEN:END FUNCTIONS -->
