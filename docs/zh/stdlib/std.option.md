# `std.option`

## 概述
`Option[T]` 用于表达“可能不存在”的值。

导入：
```flavent
use std.option
```

## 类型
- `Option[T] = Some(T) | None`

## API
- `unwrapOr(o, default) -> T`
- `isSome(o) -> Bool`
- `isNone(o) -> Bool`
- `orElse(o, other) -> Option[T]`
- `okOr(o, err) -> Result[T, E]`
- `unwrapOrZeroInt(o: Option[Int]) -> Int`
- `unwrapOrEmptyStr(o: Option[Str]) -> Str`
- `toList(o) -> List[T]`
- `fromBool(cond, v) -> Option[T]`
