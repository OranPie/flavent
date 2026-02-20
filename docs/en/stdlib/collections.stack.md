# `collections.stack`

## Overview
Persistent LIFO stack helpers backed by `List[T]`.

Use this module for push/pop/peek operations where the top element is the list head.

## Import
```flavent
use collections.stack
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Stack[T] = List[T]
type StackPop[T] = { value: T, rest: Stack[T] }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn stackEmpty[T]() -> Stack[T] = Nil
fn stackIsEmpty[T](s: Stack[T]) -> Bool = isEmpty(s)
fn stackPush[T](s: Stack[T], x: T) -> Stack[T] = Cons(x, s)
fn stackPeek[T](s: Stack[T]) -> Option[T] = match s:
fn stackPop[T](s: Stack[T]) -> Option[StackPop[T]] = match s:
fn stackPeekOr[T](s: Stack[T], default: T) -> T = match stackPeek(s):
fn stackPopOr[T](s: Stack[T], default: T) -> StackPop[T] = match stackPop(s):
fn stackSize[T](s: Stack[T]) -> Int = length(s)
fn stackToList[T](s: Stack[T]) -> List[T] = s
fn stackFromList[T](xs: List[T]) -> Stack[T] = xs
fn stackPushAll[T](s: Stack[T], xs: List[T]) -> Stack[T] = match xs:
```
<!-- AUTO-GEN:END FUNCTIONS -->
