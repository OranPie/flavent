# `file.lines`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use file.lines
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn splitLines(s: Str) -> List[Str] = _linesSplitAcc(s, 0, 0, Nil)
fn joinLines(xs: List[Str]) -> Str = _joinLines(xs)
```
<!-- AUTO-GEN:END FUNCTIONS -->
