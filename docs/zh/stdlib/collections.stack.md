# `collections.stack`

## 概述
基于 `List[T]` 的持久化 LIFO 栈工具。

适用于 push/pop/peek 等“栈顶在表头”的操作模型。

## 导入
```flavent
use collections.stack
```

## 类型
<!-- AUTO-GEN:START TYPES -->
```flavent
type Stack[T] = List[T]
type StackPop[T] = { value: T, rest: Stack[T] }
```
<!-- AUTO-GEN:END TYPES -->

## 函数
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
