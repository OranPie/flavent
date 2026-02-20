# `collections.priority_queue`

## 概述
基于有序列表实现的持久化优先队列工具。

优先级数值越小，越先被弹出。

## 导入
```flavent
use collections.priority_queue
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type PriorityItem[T] = { priority: Int, value: T }
type PriorityQueue[T] = List[PriorityItem[T]]
type PriorityPop[T] = { value: T, priority: Int, rest: PriorityQueue[T] }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
<!-- AUTO-GEN:START FUNCTIONS -->
```flavent
fn priorityQueueEmpty[T]() -> PriorityQueue[T] = Nil
fn priorityQueueIsEmpty[T](q: PriorityQueue[T]) -> Bool = isEmpty(q)
fn priorityQueuePush[T](q: PriorityQueue[T], priority: Int, value: T) -> PriorityQueue[T] =
fn priorityQueuePushItem[T](q: PriorityQueue[T], item: PriorityItem[T]) -> PriorityQueue[T] =
fn priorityQueuePeek[T](q: PriorityQueue[T]) -> Option[T] = match q:
fn priorityQueuePeekPriority[T](q: PriorityQueue[T]) -> Option[Int] = match q:
fn priorityQueuePop[T](q: PriorityQueue[T]) -> Option[PriorityPop[T]] = match q:
fn priorityQueuePeekOr[T](q: PriorityQueue[T], default: T) -> T = match priorityQueuePeek(q):
fn priorityQueuePopOr[T](q: PriorityQueue[T], defaultPriority: Int, defaultValue: T) -> PriorityPop[T] =
fn priorityQueueSize[T](q: PriorityQueue[T]) -> Int = length(q)
fn priorityQueueToList[T](q: PriorityQueue[T]) -> List[PriorityItem[T]] = q
fn priorityQueuePushAll[T](q: PriorityQueue[T], xs: List[PriorityItem[T]]) -> PriorityQueue[T] = match xs:
fn priorityQueueFromList[T](xs: List[PriorityItem[T]]) -> PriorityQueue[T] =
```
<!-- AUTO-GEN:END FUNCTIONS -->
