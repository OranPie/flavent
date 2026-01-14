# `std.option`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use std.option
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Option[T] = Some(T) | None
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn unwrapOr[T](o: Option[T], default: T) -> T = match o:
fn isSome[T](o: Option[T]) -> Bool = match o:
fn isNone[T](o: Option[T]) -> Bool = match o:
fn orElse[T](o: Option[T], other: Option[T]) -> Option[T] = match o:
fn unwrapOrZeroInt(o: Option[Int]) -> Int = unwrapOr(o, 0)
fn unwrapOrEmptyStr(o: Option[Str]) -> Str = unwrapOr(o, "")
fn toList[T](o: Option[T]) -> List[T] = match o:
fn fromBool[T](cond: Bool, v: T) -> Option[T] = match cond:
```
<!-- AUTO-GEN:END FUNCTIONS -->
