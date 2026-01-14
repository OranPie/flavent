# `std.option`

## 概述
（自动生成的 API 参考页。可在此基础上补充示例与行为/边界说明。）

## 导入
```flavent
use std.option
```

## 类型
```flavent
type Option[T] = Some(T) | None
```

## 函数
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

