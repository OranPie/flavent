# `collections.list`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use collections.list
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type List[T] = Nil | Cons(T, List[T])
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn nil[T]() -> List[T] = Nil
fn cons[T](x: T, xs: List[T]) -> List[T] = Cons(x, xs)
fn isEmpty[T](xs: List[T]) -> Bool = match xs:
fn head[T](xs: List[T]) -> Option[T] = match xs:
fn tail[T](xs: List[T]) -> Option[List[T]] = match xs:
fn length[T](xs: List[T]) -> Int = match xs:
fn reverse[T](xs: List[T]) -> List[T] = _revAcc(xs, Nil)
fn append[T](xs: List[T], ys: List[T]) -> List[T] = match xs:
fn get[T](xs: List[T], i: Int) -> Option[T] = match xs:
fn last[T](xs: List[T]) -> Option[T] = match xs:
fn take[T](xs: List[T], n: Int) -> List[T] = match n <= 0:
fn drop[T](xs: List[T], n: Int) -> List[T] = match n <= 0:
fn contains[T](xs: List[T], x: T) -> Bool = match xs:
fn concat[T](xss: List[List[T]]) -> List[T] = match xss:
fn repeat[T](x: T, n: Int) -> List[T] = match n <= 0:
fn rangeInt(start: Int, end: Int) -> List[Int] = match start >= end:
fn sumInt(xs: List[Int]) -> Int = match xs:
fn sumFloat(xs: List[Float]) -> Float = match xs:
```
<!-- AUTO-GEN:END FUNCTIONS -->
