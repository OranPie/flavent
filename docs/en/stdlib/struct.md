# `struct`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use struct
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Endian = Little | Big
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn packB(v: Int) -> Bytes = bytesFromByte(u32And(v, 255))
fn packH(v: Int) -> Bytes = do:
fn packI(v: Int) -> Bytes = do:
fn unpackB(b: Bytes, offset: Int) -> Result[Int, Str] = do:
fn unpackH(b: Bytes, offset: Int) -> Result[Int, Str] = do:
fn unpackI(b: Bytes, offset: Int) -> Result[Int, Str] = do:
fn calcsize(fmt: Str) -> Result[Int, Str] = _stCalcAcc(fmt, 0, strLen(fmt), 0)
fn pack(fmt: Str, values: List[Int]) -> Result[Bytes, Str] = do:
fn unpackFrom(fmt: Str, b: Bytes, offset: Int) -> Result[List[Int], Str] = do:
fn unpack(fmt: Str, b: Bytes) -> Result[List[Int], Str] = unpackFrom(fmt, b, 0)
```
<!-- AUTO-GEN:END FUNCTIONS -->
