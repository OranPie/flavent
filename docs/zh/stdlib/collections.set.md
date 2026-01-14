# `collections.set`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use collections.set
```

## 类型
```flavent
type Set[T] = Map[T, Unit]
```

## 函数
```flavent
fn setEmpty[T]() -> Set[T] = mapEmpty()
fn setHas[T](s: Set[T], x: T) -> Bool = match mapGet(s, x):
fn setAdd[T](s: Set[T], x: T) -> Set[T] = mapPut(s, x, ())
fn setRemove[T](s: Set[T], x: T) -> Set[T] = mapRemove(s, x)
fn setSize[T](s: Set[T]) -> Int = length(s)
fn setToList[T](s: Set[T]) -> List[T] = mapKeys(s)
fn setAddAll[T](s: Set[T], xs: List[T]) -> Set[T] = _setAddAll(s, xs)
fn setFromList[T](xs: List[T]) -> Set[T] = setAddAll(setEmpty(), xs)
fn setUnion[T](a: Set[T], b: Set[T]) -> Set[T] = _setAddAll(a, setToList(b))
fn setIntersect[T](a: Set[T], b: Set[T]) -> Set[T] = _setKeepIfIn(a, b, setToList(a))
fn setDiff[T](a: Set[T], b: Set[T]) -> Set[T] = _setKeepIfNotIn(a, b, setToList(a))
fn setIsSubset[T](a: Set[T], b: Set[T]) -> Bool = _setAllIn(setToList(a), b)
fn setEquals[T](a: Set[T], b: Set[T]) -> Bool = setIsSubset(a, b) and setIsSubset(b, a)
```

