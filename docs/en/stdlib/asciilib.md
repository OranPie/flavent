# `asciilib`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

Small helpers for ASCII/bytes interop and common byte sequences.

## Import
```flavent
use asciilib
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn crlfBytes() -> Bytes = bytesFromList(Cons(13, Cons(10, Nil)))
fn asciiFromBytes(b: Bytes) -> Str = _asciiFromBytesAcc(b, 0, bytesLen(b), "")
fn asciiToBytes(s: Str) -> Bytes = bytesFromList(_asciiCodesAcc(s, 0, strLen(s), Nil))
```
<!-- AUTO-GEN:END FUNCTIONS -->
