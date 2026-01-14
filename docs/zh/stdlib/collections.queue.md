# `collections.queue`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use collections.queue
```

## 类型
```flavent
type Queue[T] = { front: List[T], back: List[T] }
type QueuePop[T] = { value: T, rest: Queue[T] }
```

## 函数
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

