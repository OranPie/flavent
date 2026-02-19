# `collections.deque`

## Overview
Double-ended queue helpers with persistent list-backed structure.

Use this module when you need efficient front/back push and pop operations.

## Import
```flavent
use collections.deque
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Deque[T] = { front: List[T], back: List[T] }
type DequePop[T] = { value: T, rest: Deque[T] }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn dequeEmpty[T]() -> Deque[T] = { front = Nil, back = Nil }
fn dequeIsEmpty[T](d: Deque[T]) -> Bool = isEmpty(d.front) and isEmpty(d.back)
fn dequePushFront[T](d: Deque[T], x: T) -> Deque[T] = { front = Cons(x, d.front), back = d.back }
fn dequePushBack[T](d: Deque[T], x: T) -> Deque[T] = { front = d.front, back = Cons(x, d.back) }
fn dequePeekFront[T](d: Deque[T]) -> Option[T] = do:
fn dequePeekBack[T](d: Deque[T]) -> Option[T] = do:
fn dequePopFront[T](d: Deque[T]) -> Option[DequePop[T]] = do:
fn dequePopBack[T](d: Deque[T]) -> Option[DequePop[T]] = do:
fn dequePeekFrontOr[T](d: Deque[T], default: T) -> T = match dequePeekFront(d):
fn dequePeekBackOr[T](d: Deque[T], default: T) -> T = match dequePeekBack(d):
fn dequePopFrontOr[T](d: Deque[T], default: T) -> DequePop[T] = match dequePopFront(d):
fn dequePopBackOr[T](d: Deque[T], default: T) -> DequePop[T] = match dequePopBack(d):
fn dequeSize[T](d: Deque[T]) -> Int = length(d.front) + length(d.back)
fn dequeToList[T](d: Deque[T]) -> List[T] = append(d.front, reverse(d.back))
fn dequeFromList[T](xs: List[T]) -> Deque[T] = { front = xs, back = Nil }
fn dequePushAllBack[T](d: Deque[T], xs: List[T]) -> Deque[T] = match xs:
fn dequePushAllFront[T](d: Deque[T], xs: List[T]) -> Deque[T] = match xs:
fn dequeConcat[T](a: Deque[T], b: Deque[T]) -> Deque[T] = dequePushAllBack(a, dequeToList(b))
```
<!-- AUTO-GEN:END FUNCTIONS -->
