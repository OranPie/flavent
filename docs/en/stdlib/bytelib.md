# `bytelib`

## Overview
Byte helpers for `Bytes` manipulation and conversion to/from `List[Int]`.

Notes:
- `bytesFind` uses `-1` for not found.
- `bytesFindOpt` is the Option-based variant for new code.
- `bytesStartsWith` / `bytesEndsWith` are pure comparisons (no mutation).

## Import
```flavent
use bytelib
```

## Examples
```flavent
let h = bytesFromList(Cons(1, Cons(2, Cons(3, Nil))))
let i = bytesFindOpt(h, bytesFromList(Cons(2, Nil)), 0) // Some(1)
let p = bytesStartsWith(h, bytesFromList(Cons(1, Nil))) // true
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type ByteArray = List[Int]
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn bytesLen(b: Bytes) -> Int = _pyBytesLen(b)
fn bytesGet(b: Bytes, i: Int) -> Int = _pyBytesGet(b, i)
fn bytesSlice(b: Bytes, start: Int, end: Int) -> Bytes = _pyBytesSlice(b, start, end)
fn bytesConcat(a: Bytes, b: Bytes) -> Bytes = _pyBytesConcat(a, b)
fn bytesFromByte(x: Int) -> Bytes = _pyBytesFromByte(x)
fn bytesFind(h: Bytes, needle: Bytes, start: Int) -> Int = do:
fn bytesFindOpt(h: Bytes, needle: Bytes, start: Int) -> Option[Int] = do:
fn bytesStartsWith(h: Bytes, prefix: Bytes) -> Bool = do:
fn bytesEndsWith(h: Bytes, suffix: Bytes) -> Bool = do:
fn bytesToList(b: Bytes) -> List[Int] = _btToListAcc(b, 0, bytesLen(b))
fn bytesFromList(xs: List[Int]) -> Bytes = _btFromList(xs)
fn bytesConcatAll(xs: List[Bytes]) -> Bytes = match xs:
fn byteArrayEmpty() -> ByteArray = Nil
fn byteArrayPush(a: ByteArray, x: Int) -> ByteArray = append(a, Cons(x, Nil))
fn byteArrayToBytes(a: ByteArray) -> Bytes = bytesFromList(a)
fn bytesToByteArray(b: Bytes) -> ByteArray = bytesToList(b)
```
<!-- AUTO-GEN:END FUNCTIONS -->
