# `collections.queue`

## Overview
(Edit this page freely. The generator only updates the marked API blocks.)

## Import
```flavent
use collections.queue
```

## Types
<!-- AUTO-GEN:START TYPES -->
```flavent
type Queue[T] = { front: List[T], back: List[T] }
type QueuePop[T] = { value: T, rest: Queue[T] }
```
<!-- AUTO-GEN:END TYPES -->

## Functions
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn queueEmpty[T]() -> Queue[T] = { front = Nil, back = Nil }
fn queueIsEmpty[T](q: Queue[T]) -> Bool = isEmpty(q.front) and isEmpty(q.back)
fn queuePush[T](q: Queue[T], x: T) -> Queue[T] = _queueNormalize({ front = q.front, back = Cons(x, q.back) })
fn queuePeek[T](q: Queue[T]) -> Option[T] = do:
fn queuePop[T](q: Queue[T]) -> Option[QueuePop[T]] = do:
fn queuePeekOr[T](q: Queue[T], default: T) -> T = match queuePeek(q):
fn queuePopOr[T](q: Queue[T], default: T) -> QueuePop[T] = match queuePop(q):
fn queueSize[T](q: Queue[T]) -> Int = length(q.front) + length(q.back)
fn queueToList[T](q: Queue[T]) -> List[T] = append(q.front, reverse(q.back))
fn queueFromList[T](xs: List[T]) -> Queue[T] = { front = xs, back = Nil }
fn queuePushAll[T](q: Queue[T], xs: List[T]) -> Queue[T] = match xs:
fn queueConcat[T](a: Queue[T], b: Queue[T]) -> Queue[T] = queuePushAll(a, queueToList(b))
```
<!-- AUTO-GEN:END FUNCTIONS -->
